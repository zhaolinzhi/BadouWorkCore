-- Project binding: per-user assistant + folder preference for a project_id.
-- One row per (owner_user_id, project_id). project_id and assistant_id are opaque
-- client strings; not FK-validated (see AGENTS.md). folder_path is the raw
-- absolute path the client supplied; existence is the client's responsibility
-- (validated via /api/fs/exists before apply).
------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS project_binding (
    owner_user_id  TEXT    NOT NULL,
    project_id     TEXT    NOT NULL,
    assistant_id   TEXT    NOT NULL,
    folder_path    TEXT    NOT NULL CHECK (length(folder_path) > 0 AND length(folder_path) <= 4096),
    updated_at     INTEGER NOT NULL,

    PRIMARY KEY (owner_user_id, project_id)
);

CREATE INDEX IF NOT EXISTS idx_project_binding_owner ON project_binding(owner_user_id);
