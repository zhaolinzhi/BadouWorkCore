use std::collections::HashSet;
use std::path::{Path, PathBuf};

use aionui_db::{INoteRepository, INotebookRepository, ITagRepository};
use tracing::{info, warn};

use crate::error::NotebookError;
use crate::file_store::MdFileStore;
use crate::workspace::{LEGACY_DEFAULT_USER_ID, WorkspaceConfig};

/// 旧版共享笔记目录的一次性迁移标记（位于工作区根目录下）。
///
/// 多账号改造之前，所有账号的正文都写在同一个共享的 `notes/` 目录里；改造之后
/// 正文按账号落在 `users/<user_dir>/notes/` 下，旧目录里的文件对所有账号都不再可达。
/// 迁移成功后写入该标记文件，保证这次搬家只做一次。
const LEGACY_MIGRATION_MARKER: &str = ".notes-legacy-migrated";

/// `WorkspaceSync::reconcile_for()` 一次执行的结果汇总。
#[derive(Debug, Default, Clone)]
pub struct WorkspaceSyncReport {
    pub inserted: usize,
    pub updated: usize,
    pub removed: usize,
    pub parse_failures: Vec<String>,
    pub orphans_cleaned: usize,
}

/// 将 SQLite 索引与磁盘上的 Markdown 文件树对齐。
///
/// 对齐是**按账号**进行的：`reconcile_for(user_id)` 只看该账号自己的正文目录，
/// 也只删该账号自己的行。多账号改造之前所有账号共用一个 `notes/` 目录，
/// 那时的 reconcile 会把别的账号的行当成孤儿删掉——按账号对齐之后不存在这个问题。
#[derive(Clone)]
pub struct WorkspaceSync {
    /// 用于记录当前 reconcile 归属于哪个工作区，并对未来"按工作区上报"保留扩展空间。
    /// `MdFileStore` 已经持有解析后的路径，因此该字段目前未被读取。
    #[allow(dead_code)]
    workspace: WorkspaceConfig,
    file_store: MdFileStore,
    note_repo: std::sync::Arc<dyn INoteRepository>,
    #[allow(dead_code)]
    notebook_repo: std::sync::Arc<dyn INotebookRepository>,
    tag_repo: std::sync::Arc<dyn ITagRepository>,
}

impl WorkspaceSync {
    /// 构造 `WorkspaceSync`，注入所需的 repo 与文件存储。
    pub fn new(
        workspace: WorkspaceConfig,
        file_store: MdFileStore,
        note_repo: std::sync::Arc<dyn INoteRepository>,
        notebook_repo: std::sync::Arc<dyn INotebookRepository>,
        tag_repo: std::sync::Arc<dyn ITagRepository>,
    ) -> Self {
        Self {
            workspace,
            file_store,
            note_repo,
            notebook_repo,
            tag_repo,
        }
    }

    /// 执行一次**按账号**的 reconcile 同步：
    ///
    /// 1. 把还留在旧位置（旧版共享目录、默认账号目录）的正文搬到该账号自己的目录。
    /// 2. 枚举该账号目录下的 `.md` 文件。
    /// 3. 枚举该账号在 SQLite 中的 `note` 行。
    /// 4. 对该账号中"DB 有行但磁盘缺文件"的孤儿行执行删除。
    /// 5. 对磁盘有但 DB 没有的孤儿文件仅记录警告、不自动摄取（因为无法从裸文件名推断元数据）。
    /// 6. 清理孤儿标签。
    pub async fn reconcile_for(&self, user_id: &str) -> Result<WorkspaceSyncReport, NotebookError> {
        let mut report = WorkspaceSyncReport::default();

        // 0. 先把旧位置里的正文搬到该账号自己的目录。搬家失败只记录日志，
        //    不能让整个笔记功能挂掉。
        if let Err(e) = self.migrate_legacy_notes(user_id).await {
            warn!(user_id = %user_id, error = %e, "sync: 旧版正文迁移失败，继续本次对齐");
        }

        // 1. Enumerate the files of THIS account only.
        let on_disk = self.file_store.list_md_files(user_id).await?;
        let disk_paths: HashSet<String> = on_disk.iter().map(|(rel, _, _)| format!("notes/{rel}")).collect();

        // 2. Enumerate the DB rows of THIS account only.
        let db_rows = self.note_repo.list_all_paths(user_id).await?;
        let db_paths: HashSet<String> = db_rows.iter().map(|(_, p, _)| p.clone()).collect();

        // 3. DB rows whose files are missing → delete row (scoped to this account).
        for (id, file_path, _) in &db_rows {
            if !disk_paths.contains(file_path) {
                match self.note_repo.delete(id, user_id).await {
                    Ok(_) => report.removed += 1,
                    Err(e) => warn!(note_id = %id, error = %e, "sync: failed to delete orphan row"),
                }
            }
        }

        // 4. Files on disk that have no DB row → log warning, do NOT ingest.
        // The service is the only writer; stray files are anomalies (e.g. user
        // manually dropped a file). We log and skip — a real ingest would
        // require human-provided metadata (title / tags / notebook), which we
        // can't infer from the bare filename.
        for rel in disk_paths.difference(&db_paths).cloned().collect::<Vec<_>>() {
            warn!(
                file = %rel,
                "sync: orphan file on disk not in DB index; ignoring (no auto-ingest)"
            );
            report.parse_failures.push(rel);
        }

        // 5. Cleanup orphan tags.
        match self.tag_repo.cleanup_orphans().await {
            Ok(removed) => report.orphans_cleaned = removed.len(),
            Err(e) => warn!(error = %e, "sync: orphan tag cleanup failed"),
        }

        info!(
            user_id = %user_id,
            removed = report.removed,
            skipped_files = report.parse_failures.len(),
            orphans_cleaned = report.orphans_cleaned,
            "notebook workspace reconcile complete"
        );

        Ok(report)
    }

    /// 把还留在旧位置的正文搬到 `user_id` 自己的目录。
    ///
    /// 正文可能残留在两个"旧位置"：
    ///
    /// 1. 旧版共享目录 `<root>/notes/`——多账号改造之前所有账号的正文都写在这里，
    ///    改造之后对所有账号都不再可达。这是一次性的搬家，用工作区根目录下的
    ///    标记文件（`.notes-legacy-migrated`）保证只做一次。
    /// 2. 默认账号目录 `<root>/users/system_default_user/notes/`——行级 adopt
    ///    （`adopt_system_default_data`）把旧账号的行改属第一个外部账号之后，
    ///    正文还留在原处，需要交给新主人。
    ///
    /// 归属以数据库行为准：只有当 `user_id` 自己的行引用了某个旧位置里的正文时，
    /// 才把它搬进该账号自己的目录。行属于谁，正文才属于谁——这样任何一个账号的
    /// reconcile 都不可能把别人的正文抢走。
    async fn migrate_legacy_notes(&self, user_id: &str) -> Result<(), NotebookError> {
        let rows = self.note_repo.list_all_paths(user_id).await?;
        let owned_paths: HashSet<String> = rows.iter().map(|(_, p, _)| p.clone()).collect();
        let target_dir = self.file_store.notes_dir_for(user_id);

        // 1. 旧版共享目录 → 该账号目录（一次性）。
        self.migrate_shared_notes_dir(user_id, &owned_paths, &target_dir)
            .await?;

        // 2. 默认账号目录 → 该账号目录（行级 adopt 之后的交接，可重复执行）。
        self.migrate_default_user_notes(user_id, &owned_paths, &target_dir)
            .await?;

        Ok(())
    }

    /// 旧版共享目录 `<root>/notes/` 的正文搬家（一次性）。
    async fn migrate_shared_notes_dir(
        &self,
        user_id: &str,
        owned_paths: &HashSet<String>,
        target_dir: &Path,
    ) -> Result<(), NotebookError> {
        // 一次性标记已经写过：不再重复搬家。
        if self.legacy_migration_marker_path().exists() {
            return Ok(());
        }
        let legacy_dir = self.workspace.notes_dir.clone();
        // 全新安装没有旧目录（或旧目录已被清空）——直接返回。
        if !legacy_dir.is_dir() {
            return Ok(());
        }
        let legacy_files = self.file_store.list_md_files_in_dir(&legacy_dir).await?;
        if legacy_files.is_empty() {
            return Ok(());
        }
        // 该账号的行没有引用旧目录里的任何正文 → 旧目录不属于它，不能搬。
        if !legacy_files
            .iter()
            .any(|(rel, _, _)| owned_paths.contains(&format!("notes/{rel}")))
        {
            return Ok(());
        }

        let moved = self.move_files(&legacy_files, target_dir).await?;
        if moved < legacy_files.len() {
            // 有文件没能搬走：先不写标记，下一个账号的 reconcile 还能再试一次。
            warn!(
                moved = moved,
                total = legacy_files.len(),
                "sync: 旧版共享正文迁移未完成，稍后重试"
            );
            return Ok(());
        }

        // 旧目录已经空了，顺手删掉。
        let _ = std::fs::remove_dir_all(&legacy_dir);
        self.write_legacy_migration_marker()?;
        info!(user_id = %user_id, moved = moved, "sync: 旧版共享 notes 目录已迁移到账号目录");
        Ok(())
    }

    /// 默认账号目录里的正文交接给新主人（行级 adopt 之后）。
    ///
    /// `adopt_system_default_data` 只改数据库里的归属，正文还在默认账号目录下；
    /// 新主人第一次读笔记时把正文搬到自己目录里，reconcile 才不会把它当成孤儿删掉。
    async fn migrate_default_user_notes(
        &self,
        user_id: &str,
        owned_paths: &HashSet<String>,
        target_dir: &Path,
    ) -> Result<(), NotebookError> {
        let default_dir = crate::workspace::user_notes_dir(&self.workspace.root, LEGACY_DEFAULT_USER_ID);
        if default_dir == target_dir {
            // 就是默认账号自己，正文已经在正确的位置。
            return Ok(());
        }
        if !default_dir.is_dir() {
            return Ok(());
        }
        let default_files = self.file_store.list_md_files_in_dir(&default_dir).await?;
        let movable: Vec<_> = default_files
            .iter()
            .filter(|(rel, _, _)| owned_paths.contains(&format!("notes/{rel}")))
            .cloned()
            .collect();
        if movable.is_empty() {
            return Ok(());
        }
        let moved = self.move_files(&movable, target_dir).await?;
        if moved > 0 {
            info!(user_id = %user_id, moved = moved, "sync: 默认账号目录的正文已交接给新主人");
        }
        Ok(())
    }

    /// 把 `files` 里的正文搬进 `dst_dir`，返回成功搬走的数量。
    ///
    /// 同名文件已经存在于目标目录时不覆盖：目标里的那份才是当前生效的正文。
    async fn move_files(&self, files: &[(String, PathBuf, i64)], dst_dir: &Path) -> Result<usize, NotebookError> {
        std::fs::create_dir_all(dst_dir).map_err(|e| NotebookError::FileIo {
            path: dst_dir.display().to_string(),
            source: e,
        })?;
        let mut moved = 0usize;
        for (rel, abs, _) in files {
            let dst = dst_dir.join(rel);
            if dst.exists() {
                warn!(from = %abs.display(), to = %dst.display(), "sync: 旧位置正文目标已存在，跳过迁移");
                continue;
            }
            if let Some(parent) = dst.parent() {
                std::fs::create_dir_all(parent).map_err(|e| NotebookError::FileIo {
                    path: parent.display().to_string(),
                    source: e,
                })?;
            }
            move_file(abs, &dst)?;
            moved += 1;
        }
        Ok(moved)
    }

    /// 一次性迁移标记文件的位置。
    fn legacy_migration_marker_path(&self) -> PathBuf {
        self.workspace.root.join(LEGACY_MIGRATION_MARKER)
    }

    /// 写入一次性迁移标记。
    fn write_legacy_migration_marker(&self) -> Result<(), NotebookError> {
        let path = self.legacy_migration_marker_path();
        std::fs::write(&path, b"migrated\n").map_err(|e| NotebookError::FileIo {
            path: path.display().to_string(),
            source: e,
        })
    }
}

/// 移动一个文件；跨设备时退化为"复制后删除"。
fn move_file(from: &Path, to: &Path) -> Result<(), NotebookError> {
    match std::fs::rename(from, to) {
        Ok(()) => Ok(()),
        Err(e) if e.raw_os_error() == Some(18) => {
            // EXDEV：跨卷移动，先复制再删除。
            std::fs::copy(from, to).map_err(|e| NotebookError::FileIo {
                path: to.display().to_string(),
                source: e,
            })?;
            std::fs::remove_file(from).map_err(|e| NotebookError::FileIo {
                path: from.display().to_string(),
                source: e,
            })
        }
        Err(e) => Err(NotebookError::FileIo {
            path: from.display().to_string(),
            source: e,
        }),
    }
}
