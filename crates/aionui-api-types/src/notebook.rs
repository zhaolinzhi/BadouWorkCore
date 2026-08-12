use aionui_common::TimestampMs;
use serde::{Deserialize, Serialize};

// ---------------------------------------------------------------------------
// Notebook — request / response DTOs
// ---------------------------------------------------------------------------

#[derive(Debug, Deserialize)]
pub struct CreateNotebookRequest {
    pub name: String,
    #[serde(default)]
    pub description: Option<String>,
}

#[derive(Debug, Default, Deserialize)]
pub struct UpdateNotebookRequest {
    #[serde(default)]
    pub name: Option<String>,
    #[serde(default, deserialize_with = "double_option")]
    pub description: Option<Option<String>>,
}

fn double_option<'de, T, D>(deserializer: D) -> Result<Option<Option<T>>, D::Error>
where
    T: Deserialize<'de>,
    D: serde::Deserializer<'de>,
{
    Deserialize::deserialize(deserializer).map(Some)
}

#[derive(Debug, Clone, Serialize)]
pub struct NotebookResponse {
    pub id: String,
    pub name: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub description: Option<String>,
    pub created_at: TimestampMs,
    pub updated_at: TimestampMs,
}

// ---------------------------------------------------------------------------
// Note — request / response DTOs
// ---------------------------------------------------------------------------

#[derive(Debug, Deserialize)]
pub struct CreateNoteRequest {
    pub title: String,
    /// Full markdown body (without the metadata block — the server
    /// constructs the block from the other fields on save).
    pub content: String,
    /// Optional id of the parent notebook (e.g. `nb_xxx`).
    #[serde(default)]
    pub notebook_id: Option<String>,
    #[serde(default)]
    pub tags: Vec<String>,
    #[serde(default)]
    pub summary: Option<String>,
}

/// All fields optional. `None` means "keep current value". For
/// `notebook_id`/`summary`, `Some(None)` clears; `None` keeps.
#[derive(Debug, Default, Deserialize)]
pub struct UpdateNoteRequest {
    #[serde(default)]
    pub title: Option<String>,
    #[serde(default)]
    pub content: Option<String>,
    /// Tri-state: `None` keeps, `Some(None)` clears, `Some(Some(id))` sets.
    #[serde(default, deserialize_with = "double_option")]
    pub notebook_id: Option<Option<String>>,
    /// `None` keeps tags, `Some(vec)` replaces the entire set.
    #[serde(default)]
    pub tags: Option<Vec<String>>,
    #[serde(default, deserialize_with = "double_option")]
    pub summary: Option<Option<String>>,
    #[serde(default)]
    pub star: Option<bool>,
}

#[derive(Debug, Clone, Serialize)]
pub struct NoteResponse {
    pub id: String,
    pub title: String,
    pub notebook_id: Option<String>,
    pub file_path: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub summary: Option<String>,
    pub tags: Vec<String>,
    pub star: bool,
    pub created_at: TimestampMs,
    pub updated_at: TimestampMs,
}

/// Query params for `GET /api/notes`.
#[derive(Debug, Default, Deserialize)]
pub struct ListNotesQuery {
    #[serde(default)]
    pub notebook_id: Option<String>,
    #[serde(default)]
    pub tag: Option<String>,
    #[serde(default)]
    pub starred: Option<bool>,
    #[serde(default)]
    pub limit: Option<u32>,
    #[serde(default)]
    pub offset: Option<u32>,
}

/// Body returned by `GET /api/notes/{id}/raw`.
#[derive(Debug, Clone, Serialize)]
pub struct RawNoteResponse {
    pub id: String,
    pub content: String,
}

/// Body returned by `POST /api/notes/{id}/star`.
#[derive(Debug, Clone, Serialize)]
pub struct StarToggleResponse {
    pub id: String,
    pub star: bool,
}

/// Body returned by `GET /api/tags`.
#[derive(Debug, Clone, Serialize)]
pub struct TagsListResponse {
    pub tags: Vec<TagResponse>,
}

#[derive(Debug, Clone, Serialize)]
pub struct TagResponse {
    pub name: String,
    pub count: i64,
}
