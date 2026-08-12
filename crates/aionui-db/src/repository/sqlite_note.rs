use aionui_common::now_ms;
use sqlx::SqlitePool;

use crate::error::DbError;
use crate::models::NoteRow;
use crate::repository::note::{INoteRepository, ListNotesFilter, UpdateNoteParams};

#[derive(Clone, Debug)]
pub struct SqliteNoteRepository {
    pool: SqlitePool,
}

impl SqliteNoteRepository {
    pub fn new(pool: SqlitePool) -> Self {
        Self { pool }
    }
}

#[async_trait::async_trait]
impl INoteRepository for SqliteNoteRepository {
    async fn insert(&self, row: &NoteRow) -> Result<(), DbError> {
        sqlx::query(
            "INSERT INTO notes (id, file_path, title, notebook_id, summary, star, created_at, updated_at) \
             VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        )
        .bind(&row.id)
        .bind(&row.file_path)
        .bind(&row.title)
        .bind(&row.notebook_id)
        .bind(&row.summary)
        .bind(row.star)
        .bind(row.created_at)
        .bind(row.updated_at)
        .execute(&self.pool)
        .await?;
        Ok(())
    }

    async fn update(&self, id: &str, params: &UpdateNoteParams) -> Result<(), DbError> {
        let mut set_parts: Vec<String> = Vec::new();
        let mut binds: Vec<BindValue> = Vec::new();

        if let Some(ref v) = params.title {
            set_parts.push("title = ?".into());
            binds.push(BindValue::Str(v.clone()));
        }
        if let Some(ref v) = params.file_path {
            set_parts.push("file_path = ?".into());
            binds.push(BindValue::Str(v.clone()));
        }
        if let Some(ref v) = params.notebook_id {
            set_parts.push("notebook_id = ?".into());
            binds.push(BindValue::OptStr(v.clone()));
        }
        if let Some(ref v) = params.summary {
            set_parts.push("summary = ?".into());
            binds.push(BindValue::OptStr(v.clone()));
        }
        if let Some(v) = params.star {
            set_parts.push("star = ?".into());
            binds.push(BindValue::I64(v));
        }

        if set_parts.is_empty() {
            return Ok(());
        }

        set_parts.push("updated_at = ?".into());
        binds.push(BindValue::I64(now_ms()));

        let sql = format!("UPDATE notes SET {} WHERE id = ?", set_parts.join(", "));
        let mut query = sqlx::query(&sql);
        for bind in &binds {
            query = bind_value(query, bind);
        }
        query = query.bind(id);

        let result = query.execute(&self.pool).await?;
        if result.rows_affected() == 0 {
            return Err(DbError::NotFound(format!("note '{id}'")));
        }
        Ok(())
    }

    async fn delete(&self, id: &str) -> Result<(), DbError> {
        let result = sqlx::query("DELETE FROM notes WHERE id = ?")
            .bind(id)
            .execute(&self.pool)
            .await?;
        if result.rows_affected() == 0 {
            return Err(DbError::NotFound(format!("note '{id}'")));
        }
        Ok(())
    }

    async fn get_by_id(&self, id: &str) -> Result<Option<NoteRow>, DbError> {
        let row = sqlx::query_as::<_, NoteRow>("SELECT * FROM notes WHERE id = ?")
            .bind(id)
            .fetch_optional(&self.pool)
            .await?;
        Ok(row)
    }

    async fn list_filtered(&self, filter: &ListNotesFilter) -> Result<Vec<NoteRow>, DbError> {
        let mut sql = String::from("SELECT notes.* FROM notes");
        let mut wheres: Vec<String> = Vec::new();
        let mut binds: Vec<BindValue> = Vec::new();

        if filter.tag.is_some() {
            sql.push_str(" INNER JOIN note_tags nt ON nt.note_id = notes.id");
        }
        if let Some(ref nb) = filter.notebook_id {
            wheres.push("notes.notebook_id = ?".into());
            binds.push(BindValue::Str(nb.clone()));
        }
        if let Some(tag) = &filter.tag {
            wheres.push("nt.tag_name = ?".into());
            binds.push(BindValue::Str(tag.clone()));
        }
        if let Some(starred) = filter.starred {
            wheres.push("notes.star = ?".into());
            binds.push(BindValue::I64(if starred { 1 } else { 0 }));
        }
        if !wheres.is_empty() {
            sql.push_str(" WHERE ");
            sql.push_str(&wheres.join(" AND "));
        }
        sql.push_str(" ORDER BY notes.updated_at DESC");
        if let Some(limit) = filter.limit {
            sql.push_str(&format!(" LIMIT {limit}"));
        }
        if let Some(offset) = filter.offset {
            sql.push_str(&format!(" OFFSET {offset}"));
        }

        let mut query = sqlx::query_as::<_, NoteRow>(&sql);
        for bind in &binds {
            query = bind_value_as_note(query, bind);
        }
        let rows = query.fetch_all(&self.pool).await?;
        Ok(rows)
    }

    async fn get_by_file_path(&self, file_path: &str) -> Result<Option<NoteRow>, DbError> {
        let row = sqlx::query_as::<_, NoteRow>("SELECT * FROM notes WHERE file_path = ?")
            .bind(file_path)
            .fetch_optional(&self.pool)
            .await?;
        Ok(row)
    }

    async fn list_by_notebook(&self, notebook_id: &str) -> Result<Vec<NoteRow>, DbError> {
        let rows = sqlx::query_as::<_, NoteRow>("SELECT * FROM notes WHERE notebook_id = ? ORDER BY updated_at DESC")
            .bind(notebook_id)
            .fetch_all(&self.pool)
            .await?;
        Ok(rows)
    }

    async fn list_all_paths(&self) -> Result<Vec<(String, String, i64)>, DbError> {
        let rows: Vec<(String, String, i64)> = sqlx::query_as("SELECT id, file_path, updated_at FROM notes")
            .fetch_all(&self.pool)
            .await?;
        Ok(rows)
    }

    async fn upsert_by_file_path(&self, row: &NoteRow) -> Result<NoteRow, DbError> {
        let mut tx = self.pool.begin().await?;
        sqlx::query(
            "INSERT INTO notes (id, file_path, title, notebook_id, summary, star, created_at, updated_at) \
             VALUES (?, ?, ?, ?, ?, ?, ?, ?) \
             ON CONFLICT(file_path) DO UPDATE SET \
               title = excluded.title, \
               notebook_id = excluded.notebook_id, \
               summary = excluded.summary, \
               star = excluded.star, \
               updated_at = excluded.updated_at",
        )
        .bind(&row.id)
        .bind(&row.file_path)
        .bind(&row.title)
        .bind(&row.notebook_id)
        .bind(&row.summary)
        .bind(row.star)
        .bind(row.created_at)
        .bind(row.updated_at)
        .execute(&mut *tx)
        .await?;
        let stored = sqlx::query_as::<_, NoteRow>("SELECT * FROM notes WHERE file_path = ?")
            .bind(&row.file_path)
            .fetch_one(&mut *tx)
            .await?;
        tx.commit().await?;
        Ok(stored)
    }
}

// ── Dynamic bind helpers ────────────────────────────────────────────

#[derive(Debug, Clone)]
enum BindValue {
    Str(String),
    OptStr(Option<String>),
    I64(i64),
}

fn bind_value<'q>(
    query: sqlx::query::Query<'q, sqlx::Sqlite, sqlx::sqlite::SqliteArguments<'q>>,
    val: &'q BindValue,
) -> sqlx::query::Query<'q, sqlx::Sqlite, sqlx::sqlite::SqliteArguments<'q>> {
    match val {
        BindValue::Str(s) => query.bind(s.as_str()),
        BindValue::OptStr(s) => query.bind(s.as_deref()),
        BindValue::I64(n) => query.bind(*n),
    }
}

fn bind_value_as_note<'q>(
    query: sqlx::query::QueryAs<'q, sqlx::Sqlite, NoteRow, sqlx::sqlite::SqliteArguments<'q>>,
    val: &'q BindValue,
) -> sqlx::query::QueryAs<'q, sqlx::Sqlite, NoteRow, sqlx::sqlite::SqliteArguments<'q>> {
    match val {
        BindValue::Str(s) => query.bind(s.as_str()),
        BindValue::OptStr(s) => query.bind(s.as_deref()),
        BindValue::I64(n) => query.bind(*n),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::init_database_memory;

    async fn setup() -> (SqliteNoteRepository, crate::Database) {
        let db = init_database_memory().await.expect("init db");
        let repo = SqliteNoteRepository::new(db.pool().clone());
        (repo, db)
    }

    fn make_row(id: &str, file_path: &str, notebook_id: Option<&str>) -> NoteRow {
        let now = now_ms();
        NoteRow {
            id: id.into(),
            file_path: file_path.into(),
            title: "Tokyo".into(),
            notebook_id: notebook_id.map(|s| s.to_string()),
            summary: Some("Day 1 plan".into()),
            star: 0,
            created_at: now,
            updated_at: now,
        }
    }

    #[tokio::test]
    async fn insert_and_get_by_id() {
        let (repo, _db) = setup().await;
        let row = make_row("nt_1", "notes/nt_1.md", Some("nb_parent"));
        repo.insert(&row).await.unwrap();

        let found = repo.get_by_id("nt_1").await.unwrap().expect("found");
        assert_eq!(found.id, "nt_1");
        assert_eq!(found.file_path, "notes/nt_1.md");
        assert_eq!(found.title, "Tokyo");
        assert_eq!(found.notebook_id.as_deref(), Some("nb_parent"));
        assert_eq!(found.summary.as_deref(), Some("Day 1 plan"));
        assert_eq!(found.star, 0);
    }

    #[tokio::test]
    async fn get_by_id_returns_none_for_missing() {
        let (repo, _db) = setup().await;
        let result = repo.get_by_id("nt_missing").await.unwrap();
        assert!(result.is_none());
    }

    #[tokio::test]
    async fn get_by_file_path_roundtrips() {
        let (repo, _db) = setup().await;
        let row = make_row("nt_2", "notes/nt_2.md", Some("nb_parent"));
        repo.insert(&row).await.unwrap();

        let found = repo.get_by_file_path("notes/nt_2.md").await.unwrap().expect("found");
        assert_eq!(found.id, "nt_2");
    }

    #[tokio::test]
    async fn list_by_notebook_filters_correctly() {
        let (repo, _db) = setup().await;
        repo.insert(&make_row("nt_a", "notes/nt_a.md", Some("nb_parent")))
            .await
            .unwrap();
        repo.insert(&make_row("nt_b", "notes/nt_b.md", Some("nb_parent")))
            .await
            .unwrap();
        repo.insert(&make_row("nt_c", "notes/nt_c.md", Some("nb_other")))
            .await
            .unwrap();

        let parent_notes = repo.list_by_notebook("nb_parent").await.unwrap();
        assert_eq!(parent_notes.len(), 2);
        assert!(
            parent_notes
                .iter()
                .all(|n| n.notebook_id.as_deref() == Some("nb_parent"))
        );

        let other_notes = repo.list_by_notebook("nb_other").await.unwrap();
        assert_eq!(other_notes.len(), 1);
        assert_eq!(other_notes[0].id, "nt_c");
    }

    #[tokio::test]
    async fn list_filtered_with_starred_only() {
        let (repo, _db) = setup().await;
        let mut starred = make_row("nt_s1", "notes/nt_s1.md", Some("nb_parent"));
        starred.star = 1;
        repo.insert(&starred).await.unwrap();
        repo.insert(&make_row("nt_s2", "notes/nt_s2.md", Some("nb_parent")))
            .await
            .unwrap();

        let filter = ListNotesFilter {
            starred: Some(true),
            ..Default::default()
        };
        let only_starred = repo.list_filtered(&filter).await.unwrap();
        assert_eq!(only_starred.len(), 1);
        assert_eq!(only_starred[0].id, "nt_s1");
    }

    #[tokio::test]
    async fn list_filtered_with_limit_and_offset() {
        let (repo, _db) = setup().await;
        for i in 0..5 {
            repo.insert(&make_row(&format!("nt_lim_{i}"), &format!("notes/nt_lim_{i}.md"), None))
                .await
                .unwrap();
        }
        let filter = ListNotesFilter {
            limit: Some(2),
            offset: Some(1),
            ..Default::default()
        };
        let page = repo.list_filtered(&filter).await.unwrap();
        assert_eq!(page.len(), 2);
    }

    #[tokio::test]
    async fn update_partial_fields() {
        let (repo, _db) = setup().await;
        repo.insert(&make_row("nt_u1", "notes/nt_u1.md", Some("nb_parent")))
            .await
            .unwrap();

        let params = UpdateNoteParams {
            title: Some("Renamed".into()),
            ..Default::default()
        };
        repo.update("nt_u1", &params).await.unwrap();

        let updated = repo.get_by_id("nt_u1").await.unwrap().unwrap();
        assert_eq!(updated.title, "Renamed");
        assert!(updated.updated_at >= updated.created_at);
    }

    #[tokio::test]
    async fn update_clears_optional_notebook() {
        let (repo, _db) = setup().await;
        repo.insert(&make_row("nt_u2", "notes/nt_u2.md", Some("nb_parent")))
            .await
            .unwrap();

        let params = UpdateNoteParams {
            notebook_id: Some(None),
            ..Default::default()
        };
        repo.update("nt_u2", &params).await.unwrap();

        let updated = repo.get_by_id("nt_u2").await.unwrap().unwrap();
        assert!(updated.notebook_id.is_none());
    }

    #[tokio::test]
    async fn update_nonexistent_returns_not_found() {
        let (repo, _db) = setup().await;
        let params = UpdateNoteParams {
            title: Some("X".into()),
            ..Default::default()
        };
        let err = repo.update("nt_nope", &params).await.unwrap_err();
        assert!(matches!(err, DbError::NotFound(_)));
    }

    #[tokio::test]
    async fn delete_removes_row() {
        let (repo, _db) = setup().await;
        repo.insert(&make_row("nt_d1", "notes/nt_d1.md", None)).await.unwrap();

        repo.delete("nt_d1").await.unwrap();
        let result = repo.get_by_id("nt_d1").await.unwrap();
        assert!(result.is_none());
    }

    #[tokio::test]
    async fn delete_nonexistent_returns_not_found() {
        let (repo, _db) = setup().await;
        let err = repo.delete("nt_nope").await.unwrap_err();
        assert!(matches!(err, DbError::NotFound(_)));
    }

    #[tokio::test]
    async fn list_all_paths_returns_all_rows() {
        let (repo, _db) = setup().await;
        repo.insert(&make_row("nt_p1", "notes/nt_p1.md", None)).await.unwrap();
        repo.insert(&make_row("nt_p2", "notes/nt_p2.md", None)).await.unwrap();

        let paths = repo.list_all_paths().await.unwrap();
        assert_eq!(paths.len(), 2);
    }

    #[tokio::test]
    async fn upsert_by_file_path_inserts_then_updates() {
        let (repo, _db) = setup().await;
        let row = make_row("nt_up1", "notes/nt_up1.md", Some("nb_parent"));
        let stored = repo.upsert_by_file_path(&row).await.unwrap();
        assert_eq!(stored.id, "nt_up1");
        assert_eq!(stored.notebook_id.as_deref(), Some("nb_parent"));

        // Same file_path, different id → UPDATE on conflict.
        let mut update = make_row("nt_up2", "notes/nt_up1.md", Some("nb_other"));
        update.title = "Renamed".into();
        let stored2 = repo.upsert_by_file_path(&update).await.unwrap();
        assert_eq!(stored2.file_path, "notes/nt_up1.md");
        assert_eq!(stored2.title, "Renamed");
        // ON CONFLICT keeps the original id; notebook_id is updated.
        assert_eq!(stored2.id, "nt_up1");
        assert_eq!(stored2.notebook_id.as_deref(), Some("nb_other"));
    }
}
