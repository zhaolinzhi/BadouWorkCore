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
///
/// Every method that touches an existing row is scoped by the owning
/// `user_id`: a row belonging to another account is invisible, and
/// `update`/`delete` report `DbError::NotFound` for it.
#[async_trait::async_trait]
pub trait INotebookRepository: Send + Sync {
    /// Inserts a new notebook row.
    async fn insert(&self, row: &NotebookRow) -> Result<(), DbError>;

    /// Updates a notebook by ID with the provided fields.
    /// Returns `DbError::NotFound` if absent or owned by another user.
    async fn update(&self, id: &str, user_id: &str, params: &UpdateNotebookParams) -> Result<(), DbError>;

    /// Deletes a notebook by ID. Returns `DbError::NotFound` if absent
    /// or owned by another user.
    async fn delete(&self, id: &str, user_id: &str) -> Result<(), DbError>;

    /// Returns a single notebook by ID, or `None` if not found or owned
    /// by another user.
    async fn get_by_id(&self, id: &str, user_id: &str) -> Result<Option<NotebookRow>, DbError>;

    /// Returns a single notebook by `name`, or `None` if not found.
    /// `(user_id, name)` is UNIQUE.
    async fn find_by_name(&self, name: &str, user_id: &str) -> Result<Option<NotebookRow>, DbError>;

    /// Returns all notebooks of one account, ordered by creation time
    /// ascending (oldest first).
    async fn list_all(&self, user_id: &str) -> Result<Vec<NotebookRow>, DbError>;
}
