use serde::{Deserialize, Serialize};

/// Row mapping for the `tags` table.
#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct TagRow {
    pub name: String,
}

/// Row mapping for the `note_tags` association table.
#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct NoteTagRow {
    pub note_id: String,
    pub tag_name: String,
}

/// Row for `SELECT tags.name, COUNT(note_tags.note_id)` queries.
#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct TagWithCountRow {
    pub name: String,
    pub count: i64,
}
