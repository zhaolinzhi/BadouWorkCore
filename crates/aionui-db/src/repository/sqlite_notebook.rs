use aionui_common::now_ms;
use sqlx::SqlitePool;

use crate::error::DbError;
use crate::models::NotebookRow;
use crate::repository::notebook::{INotebookRepository, UpdateNotebookParams};

#[derive(Clone, Debug)]
pub struct SqliteNotebookRepository {
    pool: SqlitePool,
}

impl SqliteNotebookRepository {
    pub fn new(pool: SqlitePool) -> Self {
        Self { pool }
    }
}

#[async_trait::async_trait]
impl INotebookRepository for SqliteNotebookRepository {
    async fn insert(&self, row: &NotebookRow) -> Result<(), DbError> {
        sqlx::query("INSERT INTO notebooks (id, name, description, created_at, updated_at) VALUES (?, ?, ?, ?, ?)")
            .bind(&row.id)
            .bind(&row.name)
            .bind(&row.description)
            .bind(row.created_at)
            .bind(row.updated_at)
            .execute(&self.pool)
            .await?;
        Ok(())
    }

    async fn update(&self, id: &str, params: &UpdateNotebookParams) -> Result<(), DbError> {
        let mut set_parts: Vec<String> = Vec::new();
        let mut binds: Vec<BindValue> = Vec::new();

        if let Some(ref v) = params.name {
            set_parts.push("name = ?".to_string());
            binds.push(BindValue::Str(v.clone()));
        }

        if let Some(ref v) = params.description {
            set_parts.push("description = ?".to_string());
            binds.push(BindValue::OptStr(v.clone()));
        }

        if set_parts.is_empty() {
            return Ok(());
        }

        set_parts.push("updated_at = ?".to_string());
        binds.push(BindValue::I64(now_ms()));

        let sql = format!("UPDATE notebooks SET {} WHERE id = ?", set_parts.join(", "));
        let mut query = sqlx::query(&sql);
        for bind in &binds {
            query = bind_value(query, bind);
        }
        query = query.bind(id);

        let result = query.execute(&self.pool).await?;
        if result.rows_affected() == 0 {
            return Err(DbError::NotFound(format!("notebook '{id}'")));
        }
        Ok(())
    }

    async fn delete(&self, id: &str) -> Result<(), DbError> {
        let result = sqlx::query("DELETE FROM notebooks WHERE id = ?")
            .bind(id)
            .execute(&self.pool)
            .await?;
        if result.rows_affected() == 0 {
            return Err(DbError::NotFound(format!("notebook '{id}'")));
        }
        Ok(())
    }

    async fn get_by_id(&self, id: &str) -> Result<Option<NotebookRow>, DbError> {
        let row = sqlx::query_as::<_, NotebookRow>("SELECT * FROM notebooks WHERE id = ?")
            .bind(id)
            .fetch_optional(&self.pool)
            .await?;
        Ok(row)
    }

    async fn find_by_name(&self, name: &str) -> Result<Option<NotebookRow>, DbError> {
        let row = sqlx::query_as::<_, NotebookRow>("SELECT * FROM notebooks WHERE name = ?")
            .bind(name)
            .fetch_optional(&self.pool)
            .await?;
        Ok(row)
    }

    async fn list_all(&self) -> Result<Vec<NotebookRow>, DbError> {
        let rows = sqlx::query_as::<_, NotebookRow>("SELECT * FROM notebooks ORDER BY created_at ASC")
            .fetch_all(&self.pool)
            .await?;
        Ok(rows)
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

#[cfg(test)]
mod tests {
    use super::*;
    use crate::init_database_memory;

    async fn setup() -> (SqliteNotebookRepository, crate::Database) {
        let db = init_database_memory().await.expect("init db");
        let repo = SqliteNotebookRepository::new(db.pool().clone());
        (repo, db)
    }

    fn make_row(id: &str) -> NotebookRow {
        let now = now_ms();
        NotebookRow {
            id: id.into(),
            name: "Travel".into(),
            description: Some("Travel plans".into()),
            created_at: now,
            updated_at: now,
        }
    }

    fn make_row_with_name(id: &str, name: &str) -> NotebookRow {
        let now = now_ms();
        NotebookRow {
            id: id.into(),
            name: name.into(),
            description: Some("Travel plans".into()),
            created_at: now,
            updated_at: now,
        }
    }

    #[tokio::test]
    async fn insert_and_get_by_id() {
        let (repo, _db) = setup().await;
        let row = make_row("nb_1");
        repo.insert(&row).await.unwrap();

        let found = repo.get_by_id("nb_1").await.unwrap().expect("found");
        assert_eq!(found.id, "nb_1");
        assert_eq!(found.name, "Travel");
        assert_eq!(found.description.as_deref(), Some("Travel plans"));
    }

    #[tokio::test]
    async fn get_by_id_returns_none_for_missing() {
        let (repo, _db) = setup().await;
        let result = repo.get_by_id("nb_missing").await.unwrap();
        assert!(result.is_none());
    }

    #[tokio::test]
    async fn list_all_returns_in_created_order() {
        let (repo, _db) = setup().await;
        repo.insert(&make_row_with_name("nb_a", "Travel-A")).await.unwrap();
        repo.insert(&make_row_with_name("nb_b", "Travel-B")).await.unwrap();

        let all = repo.list_all().await.unwrap();
        assert_eq!(all.len(), 2);
        assert_eq!(all[0].id, "nb_a");
        assert_eq!(all[1].id, "nb_b");
    }

    #[tokio::test]
    async fn update_partial_fields() {
        let (repo, _db) = setup().await;
        repo.insert(&make_row("nb_u1")).await.unwrap();

        let params = UpdateNotebookParams {
            name: Some("Renamed".into()),
            description: None,
        };
        repo.update("nb_u1", &params).await.unwrap();

        let updated = repo.get_by_id("nb_u1").await.unwrap().unwrap();
        assert_eq!(updated.name, "Renamed");
        assert!(updated.updated_at >= updated.created_at);
    }

    #[tokio::test]
    async fn update_clears_optional_description_with_none() {
        let (repo, _db) = setup().await;
        repo.insert(&make_row("nb_u2")).await.unwrap();

        // Clear description via outer-None
        let params = UpdateNotebookParams {
            description: Some(None),
            ..Default::default()
        };
        repo.update("nb_u2", &params).await.unwrap();

        let updated = repo.get_by_id("nb_u2").await.unwrap().unwrap();
        assert!(updated.description.is_none());
    }

    #[tokio::test]
    async fn update_nonexistent_returns_not_found() {
        let (repo, _db) = setup().await;
        let params = UpdateNotebookParams {
            name: Some("X".into()),
            ..Default::default()
        };
        let err = repo.update("nb_nope", &params).await.unwrap_err();
        assert!(matches!(err, DbError::NotFound(_)));
    }

    #[tokio::test]
    async fn delete_removes_row() {
        let (repo, _db) = setup().await;
        repo.insert(&make_row("nb_d1")).await.unwrap();

        repo.delete("nb_d1").await.unwrap();
        let result = repo.get_by_id("nb_d1").await.unwrap();
        assert!(result.is_none());
    }

    #[tokio::test]
    async fn delete_nonexistent_returns_not_found() {
        let (repo, _db) = setup().await;
        let err = repo.delete("nb_nope").await.unwrap_err();
        assert!(matches!(err, DbError::NotFound(_)));
    }

    #[tokio::test]
    async fn find_by_name_roundtrips() {
        let (repo, _db) = setup().await;
        repo.insert(&make_row("nb_n1")).await.unwrap();

        let found = repo.find_by_name("Travel").await.unwrap().expect("found");
        assert_eq!(found.id, "nb_n1");
        assert_eq!(found.name, "Travel");
    }

    #[tokio::test]
    async fn find_by_name_returns_none_for_missing() {
        let (repo, _db) = setup().await;
        let result = repo.find_by_name("Ghost").await.unwrap();
        assert!(result.is_none());
    }

    #[tokio::test]
    async fn duplicate_name_returns_error_on_insert() {
        let (repo, _db) = setup().await;
        repo.insert(&make_row("nb_dup1")).await.unwrap();
        let result = repo.insert(&make_row("nb_dup2")).await;
        assert!(matches!(result, Err(DbError::Query(_)) | Err(DbError::Init(_))));
    }
}
