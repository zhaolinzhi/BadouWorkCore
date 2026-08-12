use aionui_common::TimestampMs;
use serde::{Deserialize, Serialize};

/// Row mapping for the `notebooks` table.
///
/// `name` is UNIQUE — enforced at the SQL level. Notes reference
/// notebooks by `id`. Service-layer code validates the reference at
/// write time (no SQL-level FK; see spec §2).
#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct NotebookRow {
    pub id: String,
    pub name: String,
    pub description: Option<String>,
    pub created_at: TimestampMs,
    pub updated_at: TimestampMs,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn notebook_row_serialization_roundtrip() {
        let row = NotebookRow {
            id: "nb_abc".into(),
            name: "Travel".into(),
            description: Some("Travel plans".into()),
            created_at: 1000,
            updated_at: 2000,
        };
        let json = serde_json::to_string(&row).expect("serialize");
        let restored: NotebookRow = serde_json::from_str(&json).expect("deserialize");
        assert_eq!(restored.id, row.id);
        assert_eq!(restored.name, row.name);
        assert_eq!(restored.description, row.description);
    }

    #[test]
    fn notebook_row_without_description_is_valid() {
        let row = NotebookRow {
            id: "nb_min".into(),
            name: "Inbox".into(),
            description: None,
            created_at: 100,
            updated_at: 100,
        };
        assert!(row.description.is_none());
    }
}
