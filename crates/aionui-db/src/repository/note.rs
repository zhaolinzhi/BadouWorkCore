use crate::error::DbError;
use crate::models::NoteRow;

/// Parameters for updating a note. All fields are optional; `None`
/// means "keep the current value".
///
/// `notebook_id` is tri-state: `None` preserves the existing value;
/// `Some(None)` clears the notebook reference; `Some(Some(id))` sets
/// it (the service layer validates that the id exists).
#[derive(Debug, Clone, Default)]
pub struct UpdateNoteParams {
    pub title: Option<String>,
    pub file_path: Option<String>,
    pub notebook_id: Option<Option<String>>,
    pub summary: Option<Option<String>>,
    pub star: Option<i64>,
}

/// Filter for `list_filtered`. Every field is optional; absent means
/// "no filter on this column". `tag` requires a join against `note_tags`.
#[derive(Debug, Clone, Default)]
pub struct ListNotesFilter {
    pub notebook_id: Option<String>,
    pub tag: Option<String>,
    pub starred: Option<bool>,
    pub limit: Option<i64>,
    pub offset: Option<i64>,
}

/// Data access abstraction for the `notes` table.
#[async_trait::async_trait]
pub trait INoteRepository: Send + Sync {
    async fn insert(&self, row: &NoteRow) -> Result<(), DbError>;

    /// Update a note by ID. Touches `updated_at` automatically.
    /// Returns `DbError::NotFound` if absent.
    async fn update(&self, id: &str, params: &UpdateNoteParams) -> Result<(), DbError>;

    /// Delete a note by ID. Returns `DbError::NotFound` if absent.
    async fn delete(&self, id: &str) -> Result<(), DbError>;

    async fn get_by_id(&self, id: &str) -> Result<Option<NoteRow>, DbError>;

    /// Filtered list ordered by `updated_at` DESC.
    /// When `tag` is set, results are additionally restricted to notes
    /// that have that tag attached.
    async fn list_filtered(&self, filter: &ListNotesFilter) -> Result<Vec<NoteRow>, DbError>;

    /// List notes whose `file_path` matches exactly. Used by sync.
    async fn get_by_file_path(&self, file_path: &str) -> Result<Option<NoteRow>, DbError>;

    /// All notes for a given notebook id, ordered by `updated_at` DESC.
    /// Used by the `GET /api/notebooks/{id}/notes` endpoint.
    async fn list_by_notebook(&self, notebook_id: &str) -> Result<Vec<NoteRow>, DbError>;

    /// All notes with their file paths, used by sync to build the
    /// `notes_on_disk` set.
    async fn list_all_paths(&self) -> Result<Vec<(String, String, i64)>, DbError>;
    // (id, file_path, updated_at)

    /// Upsert by `file_path`. Used by sync when ingesting a new file.
    /// Returns the resulting `NoteRow` after insert.
    async fn upsert_by_file_path(&self, row: &NoteRow) -> Result<NoteRow, DbError>;
}
