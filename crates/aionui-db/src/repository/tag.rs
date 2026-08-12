use crate::error::DbError;
use crate::models::{NoteTagRow, TagRow, TagWithCountRow};

#[async_trait::async_trait]
pub trait ITagRepository: Send + Sync {
    /// Insert tags ignoring duplicates (`INSERT OR IGNORE`).
    async fn insert_ignore_all(&self, names: &[String]) -> Result<(), DbError>;

    /// Return all `(tag_name, count)` rows for tags that have at least
    /// one note. Ordered by count descending, then name ascending.
    async fn list_with_counts(&self) -> Result<Vec<TagWithCountRow>, DbError>;

    /// Set the tags attached to a single note. Inserts missing tag
    /// rows first. Replaces any prior association.
    async fn set_note_tags(&self, note_id: &str, names: &[String]) -> Result<(), DbError>;

    /// Return tag names attached to a single note, ordered alphabetically.
    async fn tags_for_note(&self, note_id: &str) -> Result<Vec<TagRow>, DbError>;

    /// Return tag names attached to many notes in one query.
    /// Result map: note_id → Vec<tag_name>.
    async fn tags_for_notes(&self, note_ids: &[String]) -> Result<Vec<(String, Vec<String>)>, DbError>;

    /// Return tags currently attached to no note. Used by cleanup.
    async fn find_orphans(&self) -> Result<Vec<TagRow>, DbError>;

    /// Delete tags that have no associated notes. Returns rows removed.
    async fn cleanup_orphans(&self) -> Result<Vec<TagRow>, DbError>;

    /// Fetch all `(note_id, tag_name)` rows. Used by sync to rebuild
    /// the in-memory association when re-parsing a file.
    async fn list_all_note_tags(&self) -> Result<Vec<NoteTagRow>, DbError>;
}
