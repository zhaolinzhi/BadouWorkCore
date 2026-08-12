-- Create notebook feature tables: notebooks (top-level groupings), notes
-- (Markdown metadata indexed by file_path), and tags / note_tags for label
-- associations.
--
-- This is a single combined migration instead of the original two-step
-- (036_create_notes_with_file_index.sql -> 037_rename_notes_notebook_to_notebook_id.sql)
-- because BadouWorkCore already had a different 036/037 by the time the
-- notebook feature landed — so the rename step in the source repo's
-- 037 doesn't apply. The schema here matches the *post-rename* final shape
-- (notes.notebook_id, not notes.notebook).

-- Update Aion CLI agent icon to the new brand logo.
UPDATE agent_metadata
SET icon = '/api/assets/logos/brand/badoucli.svg',
    name = 'Badou Cli',
    updated_at = unixepoch('now','subsec')*1000
WHERE id = '632f31d2';

UPDATE assistant_definitions
SET
    name = REPLACE(name, 'AionUi', 'BadouWork'),
    name_i18n = REPLACE(name_i18n, 'AionUi', 'BadouWork'),
    description = REPLACE(description, 'AionUi', 'BadouWork'),
    description_i18n = REPLACE(description_i18n, 'AionUi', 'BadouWork'),
    recommended_prompts = REPLACE(recommended_prompts, 'AionUi', 'BadouWork'),
    recommended_prompts_i18n = REPLACE(recommended_prompts_i18n, 'AionUi', 'BadouWork')
WHERE assistant_id = 'aionui-assistant';

CREATE TABLE IF NOT EXISTS notebooks (
    id TEXT PRIMARY KEY NOT NULL,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS notes (
    id TEXT PRIMARY KEY NOT NULL,
    file_path TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    notebook_id TEXT,
    summary TEXT,
    star INTEGER NOT NULL DEFAULT 0,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_notes_notebook_id ON notes(notebook_id);
CREATE INDEX IF NOT EXISTS idx_notes_updated_at ON notes(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_notes_star ON notes(star);

CREATE TABLE IF NOT EXISTS tags (
    name TEXT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS note_tags (
    note_id TEXT NOT NULL,
    tag_name TEXT NOT NULL,
    PRIMARY KEY (note_id, tag_name),
    FOREIGN KEY (note_id) REFERENCES notes(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_name) REFERENCES tags(name) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_note_tags_tag ON note_tags(tag_name);
