use aionui_db::DbError;

/// 笔记本模块统一错误类型。service 层使用它抛出错误，
/// 在 `routes.rs` 通过 `From<NotebookError> for ApiError` 映射为 HTTP 层错误。
#[derive(Debug, thiserror::Error)]
pub enum NotebookError {
    #[error("Notebook not found: {0}")]
    NotebookNotFound(String),

    #[error("Note not found: {0}")]
    NoteNotFound(String),

    #[error("Duplicate name: {0}")]
    DuplicateName(String),

    #[error("Invalid request: {0}")]
    InvalidRequest(String),

    #[error("Invalid metadata: {0}")]
    InvalidMetadata(String),

    #[error("Workspace init failed: {0}")]
    WorkspaceInit(String),

    #[error("{0}")]
    Database(#[from] DbError),

    #[error("JSON error: {0}")]
    Json(#[from] serde_json::Error),

    #[error("File IO error at '{path}': {source}")]
    FileIo {
        path: String,
        #[source]
        source: std::io::Error,
    },

    #[error("File not found: {0}")]
    FileNotFound(String),
}
