use aionui_common::TimestampMs;
use serde::{Deserialize, Serialize};

/// Row mapping for the `notes` table.
///
/// Note body lives in a Markdown file at `file_path` (relative to the
/// notebook workspace root). The DB stores only metadata: title, optional
/// notebook id reference, summary, star flag, timestamps.
///
/// `notebook_id` references `notebooks.id` (text, prefixed e.g. `nb_...`).
/// The reference is intentionally NOT a SQL FOREIGN KEY (see spec §2);
/// service-layer code validates existence at write time.
#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct NoteRow {
    pub id: String,
    pub file_path: String,
    pub title: String,
    pub notebook_id: Option<String>,
    pub summary: Option<String>,
    pub star: i64,
    pub created_at: TimestampMs,
    pub updated_at: TimestampMs,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn note_row_serialization_roundtrip() {
        let row = NoteRow {
            id: "nt_abc".into(),
            file_path: "notes/nt_abc.md".into(),
            title: "Tokyo".into(),
            notebook_id: Some("nb_xyz".into()),
            summary: Some("Day 1 plan".into()),
            star: 0,
            created_at: 1000,
            updated_at: 2000,
        };
        let json = serde_json::to_string(&row).expect("serialize");
        let restored: NoteRow = serde_json::from_str(&json).expect("deserialize");
        assert_eq!(restored.id, row.id);
        assert_eq!(restored.file_path, row.file_path);
        assert_eq!(restored.notebook_id, row.notebook_id);
        assert_eq!(restored.summary, row.summary);
        assert_eq!(restored.star, row.star);
    }

    #[test]
    fn note_row_without_notebook_is_valid() {
        let row = NoteRow {
            id: "nt_min".into(),
            file_path: "notes/nt_min.md".into(),
            title: "Inbox".into(),
            notebook_id: None,
            summary: None,
            star: 0,
            created_at: 100,
            updated_at: 100,
        };
        assert!(row.notebook_id.is_none());
        assert_eq!(row.star, 0);
    }
}
