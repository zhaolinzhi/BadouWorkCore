use std::collections::HashSet;

use aionui_db::{INoteRepository, INotebookRepository, ITagRepository};
use tracing::{info, warn};

use crate::error::NotebookError;
use crate::file_store::MdFileStore;
use crate::workspace::WorkspaceConfig;

/// `WorkspaceSync::reconcile()` 一次执行的结果汇总。
#[derive(Debug, Default, Clone)]
pub struct WorkspaceSyncReport {
    pub inserted: usize,
    pub updated: usize,
    pub removed: usize,
    pub parse_failures: Vec<String>,
    pub orphans_cleaned: usize,
}

/// 将 SQLite 索引与 `workspace.notes_dir` 下的磁盘文件树对齐。
///
/// 在 `NotebookService` 构造完成后调用一次 `reconcile()`。
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

    /// 执行一次 reconcile 同步：
    ///
    /// 1. 枚举磁盘上的 `.md` 文件。
    /// 2. 枚举 SQLite 中的 `note` 行。
    /// 3. 对 DB 中存在但磁盘缺失的孤儿行执行删除。
    /// 4. 对磁盘有但 DB 没有的孤儿文件仅记录警告、不自动摄取（因为无法从裸文件名推断元数据）。
    /// 5. 清理孤儿标签。
    pub async fn reconcile(&self) -> Result<WorkspaceSyncReport, NotebookError> {
        let mut report = WorkspaceSyncReport::default();

        // 1. Enumerate files on disk.
        let on_disk = self.file_store.list_md_files().await?;
        let disk_paths: HashSet<String> = on_disk.iter().map(|(name, _, _)| format!("notes/{name}")).collect();

        // 2. Enumerate DB rows.
        let db_rows = self.note_repo.list_all_paths().await?;
        let db_paths: HashSet<String> = db_rows.iter().map(|(_, p, _)| p.clone()).collect();

        // 3. DB rows whose files are missing → delete row.
        for (id, file_path, _) in &db_rows {
            if !disk_paths.contains(file_path) {
                match self.note_repo.delete(id).await {
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
            removed = report.removed,
            skipped_files = report.parse_failures.len(),
            orphans_cleaned = report.orphans_cleaned,
            "notebook workspace reconcile complete"
        );

        Ok(report)
    }
}
