use std::sync::Arc;

use aionui_api_types::{
    CreateNoteRequest, CreateNotebookRequest, ListNotesQuery, NoteResponse, NotebookResponse, RawNoteResponse,
    StarToggleResponse, TagResponse, TagsListResponse, UpdateNoteRequest, UpdateNotebookRequest,
};
use aionui_common::TimestampMs;
use aionui_db::{
    INoteRepository, INotebookRepository, ITagRepository, ListNotesFilter, NoteRow, NotebookRow,
    SqliteNotebookRepository, SqlitePool, UpdateNoteParams, UpdateNotebookParams,
};

use crate::error::NotebookError;
use crate::file_store::MdFileStore;
use crate::workspace::{WorkspaceConfig, generate_md_filename};

#[derive(Clone)]
pub struct NotebookService {
    notebook_repo: Arc<dyn INotebookRepository>,
    note_repo: Arc<dyn INoteRepository>,
    tag_repo: Arc<dyn ITagRepository>,
    file_store: MdFileStore,
    /// 保留当前 notebook 模块绑定的工作区配置，便于在 service 层做路径/作用域决策。
    /// 实际写入路径目前由 `file_store` 解析，因此该字段暂未被直接读取。
    #[allow(dead_code)]
    workspace: WorkspaceConfig,
    pool: SqlitePool,
}

impl NotebookService {
    /// 构造 `NotebookService`。依赖通过 trait 注入，便于测试替换。
    pub fn new(
        notebook_repo: Arc<dyn INotebookRepository>,
        note_repo: Arc<dyn INoteRepository>,
        tag_repo: Arc<dyn ITagRepository>,
        file_store: MdFileStore,
        workspace: WorkspaceConfig,
        pool: SqlitePool,
    ) -> Self {
        Self {
            notebook_repo,
            note_repo,
            tag_repo,
            file_store,
            workspace,
            pool,
        }
    }

    // ── Notebooks ────────────────────────────────────────────────

    /// 创建一个新笔记本。
    ///
    /// - `name` 不能为空（trim 后判定）。
    /// - `name` 不能与已有笔记本重名，否则返回 `DuplicateName`。
    pub async fn create_notebook(&self, req: CreateNotebookRequest) -> Result<NotebookResponse, NotebookError> {
        let name = req.name.trim().to_owned();
        if name.is_empty() {
            return Err(NotebookError::InvalidRequest("name must not be empty".into()));
        }
        if self.notebook_repo.find_by_name(&name).await?.is_some() {
            return Err(NotebookError::DuplicateName(name));
        }
        let now = now_ms();
        let row = NotebookRow {
            id: generate_prefixed_id("nb"),
            name,
            description: req.description,
            created_at: now,
            updated_at: now,
        };
        SqliteNotebookRepository::new(self.pool.clone()).insert(&row).await?;
        Ok(to_notebook_response(&row))
    }

    /// 列出所有笔记本（不分页，按仓库默认排序）。
    pub async fn list_notebooks(&self) -> Result<Vec<NotebookResponse>, NotebookError> {
        let rows = self.notebook_repo.list_all().await?;
        Ok(rows.iter().map(to_notebook_response).collect())
    }

    /// 获取某个笔记本及其下全部笔记。
    ///
    /// 若 `id` 不存在，返回 `NotebookNotFound`。
    pub async fn get_notebook_with_notes(
        &self,
        id: &str,
    ) -> Result<(NotebookResponse, Vec<NoteResponse>), NotebookError> {
        let notebook = self
            .notebook_repo
            .get_by_id(id)
            .await?
            .ok_or_else(|| NotebookError::NotebookNotFound(id.to_owned()))?;
        let notes = self.note_repo.list_by_notebook(&notebook.id).await?;
        let note_responses = self.rows_to_responses(notes).await?;
        Ok((to_notebook_response(&notebook), note_responses))
    }

    /// 更新笔记本元数据（名称或描述）。`req` 字段为 tri-state：
    /// - `None` 不修改；
    /// - `Some(value)` 则设置为 `value`。
    ///
    /// 若新名称与已有笔记本重名（且不是自身）则返回 `DuplicateName`。
    pub async fn update_notebook(
        &self,
        id: &str,
        req: UpdateNotebookRequest,
    ) -> Result<NotebookResponse, NotebookError> {
        if let Some(ref name) = req.name
            && name.trim().is_empty()
        {
            return Err(NotebookError::InvalidRequest("name must not be empty".into()));
        }
        if let Some(ref new_name) = req.name
            && let Some(existing) = self.notebook_repo.find_by_name(new_name).await?
            && existing.id != id
        {
            return Err(NotebookError::DuplicateName(new_name.clone()));
        }
        let params = UpdateNotebookParams {
            name: req.name,
            description: req.description,
        };
        self.notebook_repo.update(id, &params).await?;
        let row = self
            .notebook_repo
            .get_by_id(id)
            .await?
            .ok_or_else(|| NotebookError::NotebookNotFound(id.to_owned()))?;
        Ok(to_notebook_response(&row))
    }

    /// 删除笔记本。当前实现不级联删除该笔记本下的笔记。
    pub async fn delete_notebook(&self, id: &str) -> Result<(), NotebookError> {
        self.notebook_repo.delete(id).await?;
        Ok(())
    }

    // ── Notes ────────────────────────────────────────────────────

    /// 创建一个新笔记。
    ///
    /// - `title` 不能为空。
    /// - 路径参数 `path_notebook_id` 优先；若为空则回落到 `req.notebook_id`（见规范 §5）。
    /// - 先写 Markdown 文件，再写 SQLite 元数据；若 SQLite 插入失败会自动清理已写入的文件。
    /// - 标签会先做 `insert_ignore_all` 后再 `set_note_tags` 建立关联。
    pub async fn create_note(
        &self,
        path_notebook_id: &str,
        req: CreateNoteRequest,
    ) -> Result<NoteResponse, NotebookError> {
        let title = req.title.trim().to_owned();
        if title.is_empty() {
            return Err(NotebookError::InvalidRequest("title must not be empty".into()));
        }
        // Path id takes precedence over req.notebook_id (per spec §5).
        let effective_notebook_id: Option<String> = if !path_notebook_id.is_empty() {
            Some(path_notebook_id.to_owned())
        } else {
            req.notebook_id.clone()
        };
        if let Some(ref nb_id) = effective_notebook_id
            && self.notebook_repo.get_by_id(nb_id).await?.is_none()
        {
            return Err(NotebookError::NotebookNotFound(nb_id.clone()));
        }

        let id = generate_prefixed_id("nt");
        let file_name = generate_md_filename();
        let file_path = format!("notes/{file_name}");

        let now = now_ms();

        // Write the raw Markdown body — no metadata block.
        self.file_store.write(&file_path, &req.content).await?;

        let row = NoteRow {
            id: id.clone(),
            file_path: file_path.clone(),
            title,
            notebook_id: effective_notebook_id,
            summary: req.summary.clone(),
            star: 0,
            created_at: now,
            updated_at: now,
        };
        if let Err(e) = self.note_repo.insert(&row).await {
            let _ = self.file_store.delete(&file_path).await;
            return Err(e.into());
        }

        if !req.tags.is_empty() {
            self.tag_repo.insert_ignore_all(&req.tags).await?;
            self.tag_repo.set_note_tags(&id, &req.tags).await?;
        }

        Ok(to_note_response(&row, req.tags))
    }

    /// 列出指定笔记本下的全部笔记。若笔记本不存在返回 `NotebookNotFound`。
    pub async fn list_notes_by_notebook(&self, notebook_id: &str) -> Result<Vec<NoteResponse>, NotebookError> {
        if self.notebook_repo.get_by_id(notebook_id).await?.is_none() {
            return Err(NotebookError::NotebookNotFound(notebook_id.to_owned()));
        }
        let rows = self.note_repo.list_by_notebook(notebook_id).await?;
        self.rows_to_responses(rows).await
    }

    /// 按查询条件（`notebook_id`、`tag`、`starred`、`limit`、`offset`）列出笔记。
    pub async fn list_notes_filtered(&self, query: &ListNotesQuery) -> Result<Vec<NoteResponse>, NotebookError> {
        let filter = ListNotesFilter {
            notebook_id: query.notebook_id.clone(),
            tag: query.tag.clone(),
            starred: query.starred,
            limit: query.limit.map(|n| n as i64),
            offset: query.offset.map(|n| n as i64),
        };
        let rows = self.note_repo.list_filtered(&filter).await?;
        self.rows_to_responses(rows).await
    }

    /// 按 id 获取笔记元数据（含标签），不读文件正文。
    pub async fn get_note(&self, id: &str) -> Result<NoteResponse, NotebookError> {
        let row = self
            .note_repo
            .get_by_id(id)
            .await?
            .ok_or_else(|| NotebookError::NoteNotFound(id.to_owned()))?;
        let tags = self.tag_repo.tags_for_note(&row.id).await?;
        Ok(to_note_response(&row, tags.into_iter().map(|t| t.name).collect()))
    }

    /// 获取笔记的原始 Markdown 正文。
    ///
    /// 若 SQLite 中存在记录但磁盘文件缺失，会自动删除孤儿行（自愈）并返回空内容。
    pub async fn get_note_raw(&self, id: &str) -> Result<RawNoteResponse, NotebookError> {
        let row = self
            .note_repo
            .get_by_id(id)
            .await?
            .ok_or_else(|| NotebookError::NoteNotFound(id.to_owned()))?;
        match self.file_store.read(&row.file_path).await {
            Ok(content) => Ok(RawNoteResponse { id: row.id, content }),
            Err(NotebookError::FileNotFound(p)) => {
                tracing::warn!(note_id = %row.id, file = %p, "raw fetch auto-repair: deleting orphan row");
                let _ = self.note_repo.delete(&row.id).await;
                Ok(RawNoteResponse {
                    id: row.id,
                    content: String::new(),
                })
            }
            Err(e) => Err(e),
        }
    }

    /// 更新笔记。`req` 字段均为 tri-state：
    ///
    /// - `tags`: `None` 保持原标签，`Some(vec)` 整体替换为该标签集合。
    /// - `notebook_id`: `None` 保持；`Some(None)` 清除；`Some(Some(id))` 设置（需校验存在）。
    /// - `summary`: 同上。
    /// - `content`: 只有提供时才会重写磁盘文件；纯元数据更新不动文件正文。
    /// - `star`: 提供则覆盖，不提供则保持。
    pub async fn update_note(&self, id: &str, req: UpdateNoteRequest) -> Result<NoteResponse, NotebookError> {
        if let Some(ref title) = req.title
            && title.trim().is_empty()
        {
            return Err(NotebookError::InvalidRequest("title must not be empty".into()));
        }

        let existing = self
            .note_repo
            .get_by_id(id)
            .await?
            .ok_or_else(|| NotebookError::NoteNotFound(id.to_owned()))?;

        let resolved_tags: Vec<String> = match &req.tags {
            Some(vec) => vec.clone(),
            None => self
                .tag_repo
                .tags_for_note(id)
                .await?
                .into_iter()
                .map(|t| t.name)
                .collect(),
        };

        // Tri-state notebook_id:
        //   None                       -> keep existing
        //   Some(None)                 -> clear
        //   Some(Some(id))             -> set (validate exists)
        let resolved_notebook_id: Option<String> = match &req.notebook_id {
            Some(opt) => {
                if let Some(new_id) = opt
                    && self.notebook_repo.get_by_id(new_id).await?.is_none()
                {
                    return Err(NotebookError::NotebookNotFound(new_id.clone()));
                }
                opt.clone()
            }
            None => existing.notebook_id.clone(),
        };

        let resolved_summary: Option<String> = match &req.summary {
            Some(opt) => opt.clone(),
            None => existing.summary.clone(),
        };

        // Only rewrite the file when content is provided. Metadata-only
        // updates touch SQLite only — the file body is opaque.
        if let Some(new_content) = &req.content {
            self.file_store.write(&existing.file_path, new_content).await?;
        }

        let star_i64 = req.star.map(|b| if b { 1 } else { 0 });
        let params = UpdateNoteParams {
            title: req.title.clone(),
            file_path: None,
            notebook_id: Some(resolved_notebook_id),
            summary: Some(resolved_summary),
            star: star_i64,
        };
        self.note_repo.update(id, &params).await?;

        if req.tags.is_some() {
            self.tag_repo.insert_ignore_all(&resolved_tags).await?;
            self.tag_repo.set_note_tags(id, &resolved_tags).await?;
        }

        let updated = self
            .note_repo
            .get_by_id(id)
            .await?
            .ok_or_else(|| NotebookError::NoteNotFound(id.to_owned()))?;
        let final_tags = self.tag_repo.tags_for_note(&updated.id).await?;
        Ok(to_note_response(
            &updated,
            final_tags.into_iter().map(|t| t.name).collect(),
        ))
    }

    /// 删除笔记：先删 SQLite 行，再尝试删除磁盘文件（失败不返回错误）。
    pub async fn delete_note(&self, id: &str) -> Result<(), NotebookError> {
        let row = self
            .note_repo
            .get_by_id(id)
            .await?
            .ok_or_else(|| NotebookError::NoteNotFound(id.to_owned()))?;
        self.note_repo.delete(id).await?;
        let _ = self.file_store.delete(&row.file_path).await;
        Ok(())
    }

    /// 切换笔记星标状态（0 ↔ 1），返回最新状态。
    pub async fn toggle_star(&self, id: &str) -> Result<StarToggleResponse, NotebookError> {
        let row = self
            .note_repo
            .get_by_id(id)
            .await?
            .ok_or_else(|| NotebookError::NoteNotFound(id.to_owned()))?;
        let new_star = if row.star == 0 { 1 } else { 0 };
        let params = UpdateNoteParams {
            star: Some(new_star),
            ..Default::default()
        };
        self.note_repo.update(id, &params).await?;
        Ok(StarToggleResponse {
            id: id.to_string(),
            star: new_star == 1,
        })
    }

    /// 列出所有标签及其被引用次数（按 `tag_repo.list_with_counts` 结果）。
    pub async fn list_tags(&self) -> Result<TagsListResponse, NotebookError> {
        let rows = self.tag_repo.list_with_counts().await?;
        let tags = rows
            .into_iter()
            .map(|r| TagResponse {
                name: r.name,
                count: r.count,
            })
            .collect();
        Ok(TagsListResponse { tags })
    }

    // ── Helpers ──────────────────────────────────────────────────

    /// 将一批 `NoteRow` 转成 `NoteResponse`，批量预取标签避免 N+1。
    async fn rows_to_responses(&self, rows: Vec<NoteRow>) -> Result<Vec<NoteResponse>, NotebookError> {
        let ids: Vec<String> = rows.iter().map(|r| r.id.clone()).collect();
        let grouped = self.tag_repo.tags_for_notes(&ids).await?;
        let map: std::collections::HashMap<String, Vec<String>> = grouped.into_iter().collect();
        Ok(rows
            .into_iter()
            .map(|row| {
                let tags = map.get(&row.id).cloned().unwrap_or_default();
                to_note_response(&row, tags)
            })
            .collect())
    }
}

// ── Row → response 转换辅助函数 ──────────────────────────────────

/// 将 `NotebookRow` 转换为对外的 `NotebookResponse`。
fn to_notebook_response(row: &NotebookRow) -> NotebookResponse {
    NotebookResponse {
        id: row.id.clone(),
        name: row.name.clone(),
        description: row.description.clone(),
        created_at: row.created_at,
        updated_at: row.updated_at,
    }
}

/// 将 `NoteRow` 与一组标签名转换为对外的 `NoteResponse`。
fn to_note_response(row: &NoteRow, tags: Vec<String>) -> NoteResponse {
    NoteResponse {
        id: row.id.clone(),
        title: row.title.clone(),
        notebook_id: row.notebook_id.clone(),
        file_path: row.file_path.clone(),
        summary: row.summary.clone(),
        tags,
        star: row.star == 1,
        created_at: row.created_at,
        updated_at: row.updated_at,
    }
}

// ── 通用辅助函数 ──────────────────────────────────────────────

/// 当前时间戳（毫秒）。
fn now_ms() -> TimestampMs {
    aionui_common::now_ms()
}

/// 生成带前缀的 id（如 `"nb-xxx"`、`"nt-xxx"`）。
fn generate_prefixed_id(prefix: &str) -> String {
    aionui_common::generate_prefixed_id(prefix)
}
