use crate::error::DbError;
use crate::models::NotebookRow;

/// Parameters for updating a notebook. All fields are optional; `None`
/// means "keep the current value".
#[derive(Debug, Clone, Default)]
pub struct UpdateNotebookParams {
    pub name: Option<String>,
    pub description: Option<Option<String>>,
}

/// Data access abstraction for the `notebooks` table.
#[async_trait::async_trait]
pub trait INotebookRepository: Send + Sync {
    /// Inserts a new notebook row.
    async fn insert(&self, row: &NotebookRow) -> Result<(), DbError>;

    /// Updates a notebook by ID with the provided fields.
    /// Returns `DbError::NotFound` if absent.
    async fn update(&self, id: &str, params: &UpdateNotebookParams) -> Result<(), DbError>;

    /// Deletes a notebook by ID. Returns `DbError::NotFound` if absent.
    async fn delete(&self, id: &str) -> Result<(), DbError>;

    /// Returns a single notebook by ID, or `None` if not found.
    async fn get_by_id(&self, id: &str) -> Result<Option<NotebookRow>, DbError>;

    /// Returns a single notebook by `name`, or `None` if not found.
    /// `name` is UNIQUE.
    async fn find_by_name(&self, name: &str) -> Result<Option<NotebookRow>, DbError>;

    /// Returns all notebooks ordered by creation time ascending (oldest first).
    async fn list_all(&self) -> Result<Vec<NotebookRow>, DbError>;
}
