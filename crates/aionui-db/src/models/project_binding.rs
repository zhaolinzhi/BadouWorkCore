use aionui_common::TimestampMs;
use serde::{Deserialize, Serialize};

/// Row mapping for the `project_binding` table.
///
/// `project_id` and `assistant_id` are opaque client strings (not
/// FK-validated). `folder_path` is the raw absolute path the client supplied;
/// existence is the client's responsibility. Composite PK
/// `(owner_user_id, project_id)` enforces one binding per user per project.
#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct ProjectBindingRow {
    pub owner_user_id: String,
    pub project_id: String,
    pub assistant_id: String,
    pub folder_path: String,
    pub updated_at: TimestampMs,
}
