use std::collections::HashMap;

use crate::error::DbError;
use crate::models::{NoteTagRow, TagRow, TagWithCountRow};

/// Data access abstraction for the tag vocabulary and its per-account
/// associations.
///
/// The `tags` table itself stays **global** — it is a shared vocabulary.
/// Ownership lives on the `note_tags` association rows, which carry a
/// `user_id`. Every method that reads or writes an association is scoped
/// by the owning `user_id`.
#[async_trait::async_trait]
pub trait ITagRepository: Send + Sync {
    /// Insert tags into the global vocabulary ignoring duplicates
    /// (`INSERT OR IGNORE`). The `user_id` is recorded on the
    /// `note_tags` association rows, not on the tag names themselves.
    async fn insert_ignore_all(&self, names: &[String], user_id: &str) -> Result<(), DbError>;

    /// Return all `(tag_name, count)` rows for tags that have at least
    /// one note **of the calling account**. Ordered by count descending,
    /// then name ascending.
    async fn list_with_counts(&self, user_id: &str) -> Result<Vec<TagWithCountRow>, DbError>;

    /// Set the tags attached to a single note. Inserts missing tag
    /// rows first. Replaces any prior association of that account.
    async fn set_note_tags(&self, note_id: &str, names: &[String], user_id: &str) -> Result<(), DbError>;

    /// Return tag names attached to a single note, ordered alphabetically.
    async fn tags_for_note(&self, note_id: &str, user_id: &str) -> Result<Vec<TagRow>, DbError>;

    /// Return tag names attached to many notes in one query.
    /// Result map: note_id → Vec<tag>.
    async fn tags_for_notes(&self, note_ids: &[String], user_id: &str)
    -> Result<HashMap<String, Vec<TagRow>>, DbError>;

    /// Return tags currently attached to no note. Used by cleanup.
    async fn find_orphans(&self) -> Result<Vec<TagRow>, DbError>;

    /// Delete tags that have no associated notes. Returns rows removed.
    async fn cleanup_orphans(&self) -> Result<Vec<TagRow>, DbError>;

    /// Fetch all `(note_id, tag_name)` rows. Used by sync to rebuild
    /// the in-memory association when re-parsing a file.
    async fn list_all_note_tags(&self) -> Result<Vec<NoteTagRow>, DbError>;
}
