-- Give the notes feature a user scope.
--
-- `notebooks`, `notes` and `note_tags` were global: every account on the
-- machine saw the same notebooks and notes. The `tags` table stays global
-- on purpose — it is a shared vocabulary, and `note_tags` carries the
-- per-account ownership instead.
--
-- The default keeps existing rows owned by `system_default_user`, which is
-- what the adoption mechanism (`adopt_system_default_data`) looks for when
-- it re-owns local data to the first external account.
--
-- All three tables are rebuilt because their uniqueness constraints are
-- declared inline, so SQLite stores them as `sqlite_autoindex_*` entries
-- that `DROP INDEX` cannot remove.

PRAGMA foreign_keys = OFF;

-- notebooks: `name` was globally UNIQUE; scope it to the owning user so two
-- accounts can each have a notebook called "Ideas".
CREATE TABLE notebooks_new (
    id           TEXT PRIMARY KEY NOT NULL,
    name         TEXT NOT NULL,
    description  TEXT,
    user_id      TEXT NOT NULL DEFAULT 'system_default_user',
    created_at   INTEGER NOT NULL,
    updated_at   INTEGER NOT NULL,
    UNIQUE(user_id, name)
);
INSERT INTO notebooks_new (id, name, description, user_id, created_at, updated_at)
    SELECT id, name, description, 'system_default_user', created_at, updated_at FROM notebooks;
DROP TABLE notebooks;
ALTER TABLE notebooks_new RENAME TO notebooks;

-- notes: `file_path` stays globally UNIQUE — the filename is a UUIDv4
-- (`aionui-notebook/src/workspace.rs:107-110`), so collisions do not occur.
CREATE TABLE notes_new (
    id           TEXT PRIMARY KEY NOT NULL,
    file_path    TEXT NOT NULL UNIQUE,
    title        TEXT NOT NULL,
    notebook_id  TEXT,
    summary      TEXT,
    star         INTEGER NOT NULL DEFAULT 0,
    user_id      TEXT NOT NULL DEFAULT 'system_default_user',
    created_at   INTEGER NOT NULL,
    updated_at   INTEGER NOT NULL
);
INSERT INTO notes_new (id, file_path, title, notebook_id, summary, star, user_id, created_at, updated_at)
    SELECT id, file_path, title, notebook_id, summary, star, 'system_default_user', created_at, updated_at FROM notes;
DROP TABLE notes;
ALTER TABLE notes_new RENAME TO notes;

-- note_tags: the primary key becomes (user_id, note_id, tag_name).
CREATE TABLE note_tags_new (
    note_id  TEXT NOT NULL,
    tag_name TEXT NOT NULL,
    user_id  TEXT NOT NULL DEFAULT 'system_default_user',
    PRIMARY KEY (user_id, note_id, tag_name),
    FOREIGN KEY (note_id) REFERENCES notes(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_name) REFERENCES tags(name) ON DELETE CASCADE
);
INSERT INTO note_tags_new (note_id, tag_name, user_id)
    SELECT note_id, tag_name, 'system_default_user' FROM note_tags;
DROP TABLE note_tags;
ALTER TABLE note_tags_new RENAME TO note_tags;

CREATE INDEX IF NOT EXISTS idx_notes_notebook_id ON notes(notebook_id);
CREATE INDEX IF NOT EXISTS idx_notes_updated_at ON notes(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_notes_star ON notes(star);
CREATE INDEX IF NOT EXISTS idx_note_tags_tag ON note_tags(tag_name);

CREATE INDEX IF NOT EXISTS idx_notebooks_user_id ON notebooks(user_id);
CREATE INDEX IF NOT EXISTS idx_notes_user_id ON notes(user_id);
CREATE INDEX IF NOT EXISTS idx_note_tags_user_id ON note_tags(user_id);

PRAGMA foreign_keys = ON;
