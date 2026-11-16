use std::collections::HashMap;

use sqlx::SqlitePool;

use crate::error::DbError;
use crate::models::{NoteTagRow, TagRow, TagWithCountRow};
use crate::repository::tag::ITagRepository;

#[derive(Clone, Debug)]
pub struct SqliteTagRepository {
    pool: SqlitePool,
}

impl SqliteTagRepository {
    pub fn new(pool: SqlitePool) -> Self {
        Self { pool }
    }
}

#[async_trait::async_trait]
impl ITagRepository for SqliteTagRepository {
    async fn insert_ignore_all(&self, names: &[String], _user_id: &str) -> Result<(), DbError> {
        if names.is_empty() {
            return Ok(());
        }
        let mut tx = self.pool.begin().await?;
        for name in names {
            // The vocabulary is global: the tag name is written once and
            // shared by every account. Per-account ownership lives on the
            // `note_tags` association rows instead.
            sqlx::query("INSERT OR IGNORE INTO tags (name) VALUES (?)")
                .bind(name)
                .execute(&mut *tx)
                .await?;
        }
        tx.commit().await?;
        Ok(())
    }

    async fn list_with_counts(&self, user_id: &str) -> Result<Vec<TagWithCountRow>, DbError> {
        let rows = sqlx::query_as::<_, TagWithCountRow>(
            "SELECT nt.tag_name AS name, COUNT(*) AS count \
             FROM note_tags nt \
             JOIN notes n ON n.id = nt.note_id AND n.user_id = nt.user_id \
             WHERE nt.user_id = ? \
             GROUP BY nt.tag_name \
             ORDER BY count DESC, nt.tag_name ASC",
        )
        .bind(user_id)
        .fetch_all(&self.pool)
        .await?;
        Ok(rows)
    }

    async fn set_note_tags(&self, note_id: &str, names: &[String], user_id: &str) -> Result<(), DbError> {
        let mut tx = self.pool.begin().await?;
        sqlx::query("DELETE FROM note_tags WHERE note_id = ? AND user_id = ?")
            .bind(note_id)
            .bind(user_id)
            .execute(&mut *tx)
            .await?;
        for name in names {
            sqlx::query("INSERT OR IGNORE INTO tags (name) VALUES (?)")
                .bind(name)
                .execute(&mut *tx)
                .await?;
            sqlx::query("INSERT OR IGNORE INTO note_tags (note_id, tag_name, user_id) VALUES (?, ?, ?)")
                .bind(note_id)
                .bind(name)
                .bind(user_id)
                .execute(&mut *tx)
                .await?;
        }
        tx.commit().await?;
        Ok(())
    }

    async fn tags_for_note(&self, note_id: &str, user_id: &str) -> Result<Vec<TagRow>, DbError> {
        let rows = sqlx::query_as::<_, TagRow>(
            "SELECT t.name AS name \
             FROM note_tags nt \
             JOIN tags t ON t.name = nt.tag_name \
             JOIN notes n ON n.id = nt.note_id AND n.user_id = nt.user_id \
             WHERE nt.note_id = ? AND nt.user_id = ? \
             ORDER BY t.name ASC",
        )
        .bind(note_id)
        .bind(user_id)
        .fetch_all(&self.pool)
        .await?;
        Ok(rows)
    }

    async fn tags_for_notes(
        &self,
        note_ids: &[String],
        user_id: &str,
    ) -> Result<HashMap<String, Vec<TagRow>>, DbError> {
        if note_ids.is_empty() {
            return Ok(HashMap::new());
        }
        let placeholders = std::iter::repeat_n("?", note_ids.len()).collect::<Vec<_>>().join(",");
        let sql = format!(
            "SELECT nt.note_id AS note_id, nt.tag_name AS tag_name \
             FROM note_tags nt \
             JOIN notes n ON n.id = nt.note_id AND n.user_id = nt.user_id \
             WHERE nt.note_id IN ({placeholders}) AND nt.user_id = ? \
             ORDER BY nt.note_id, nt.tag_name"
        );
        let mut query = sqlx::query_as::<_, (String, String)>(&sql);
        for id in note_ids {
            query = query.bind(id);
        }
        let rows = query.bind(user_id).fetch_all(&self.pool).await?;
        let mut out: HashMap<String, Vec<TagRow>> = HashMap::new();
        for (note_id, tag_name) in rows {
            out.entry(note_id).or_default().push(TagRow { name: tag_name });
        }
        Ok(out)
    }

    async fn find_orphans(&self) -> Result<Vec<TagRow>, DbError> {
        let rows = sqlx::query_as::<_, TagRow>(
            "SELECT t.name AS name FROM tags t \
             LEFT JOIN note_tags nt ON nt.tag_name = t.name \
             WHERE nt.note_id IS NULL",
        )
        .fetch_all(&self.pool)
        .await?;
        Ok(rows)
    }

    async fn cleanup_orphans(&self) -> Result<Vec<TagRow>, DbError> {
        let orphans = self.find_orphans().await?;
        if orphans.is_empty() {
            return Ok(Vec::new());
        }
        let mut tx = self.pool.begin().await?;
        for tag in &orphans {
            sqlx::query("DELETE FROM tags WHERE name = ?")
                .bind(&tag.name)
                .execute(&mut *tx)
                .await?;
        }
        tx.commit().await?;
        Ok(orphans)
    }

    async fn list_all_note_tags(&self) -> Result<Vec<NoteTagRow>, DbError> {
        let rows = sqlx::query_as::<_, NoteTagRow>("SELECT * FROM note_tags")
            .fetch_all(&self.pool)
            .await?;
        Ok(rows)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::init_database_memory;

    const USER: &str = "user_alice";

    async fn setup() -> (SqliteTagRepository, crate::Database) {
        let db = init_database_memory().await.expect("init db");
        let repo = SqliteTagRepository::new(db.pool().clone());
        (repo, db)
    }

    async fn insert_note(db: &crate::Database, id: &str, file_path: &str, user_id: &str) {
        let now = aionui_common::now_ms();
        sqlx::query(
            "INSERT INTO notes (id, file_path, title, star, user_id, created_at, updated_at) \
             VALUES (?, ?, ?, 0, ?, ?, ?)",
        )
        .bind(id)
        .bind(file_path)
        .bind("title")
        .bind(user_id)
        .bind(now)
        .bind(now)
        .execute(db.pool())
        .await
        .unwrap();
    }

    #[tokio::test]
    async fn insert_ignore_all_is_idempotent() {
        let (repo, _db) = setup().await;
        repo.insert_ignore_all(&["a".into(), "b".into()], USER).await.unwrap();
        repo.insert_ignore_all(&["a".into(), "c".into()], USER).await.unwrap();
        let with_counts = repo.list_with_counts(USER).await.unwrap();
        // No notes attached, so list_with_counts returns nothing.
        assert!(with_counts.is_empty());

        let orphans = repo.find_orphans().await.unwrap();
        assert_eq!(orphans.len(), 3);
    }

    #[tokio::test]
    async fn set_note_tags_replaces_existing() {
        let (repo, db) = setup().await;
        insert_note(&db, "nt_1", "notes/nt_1.md", USER).await;
        repo.set_note_tags("nt_1", &["x".into(), "y".into()], USER)
            .await
            .unwrap();
        let tags_after_first = repo.tags_for_note("nt_1", USER).await.unwrap();
        assert_eq!(tags_after_first.len(), 2);

        repo.set_note_tags("nt_1", &["z".into()], USER).await.unwrap();
        let tags_after_second = repo.tags_for_note("nt_1", USER).await.unwrap();
        assert_eq!(tags_after_second.len(), 1);
        assert_eq!(tags_after_second[0].name, "z");
    }

    #[tokio::test]
    async fn list_with_counts_orders_by_count_then_name() {
        let (repo, db) = setup().await;
        insert_note(&db, "nt_1", "notes/nt_1.md", USER).await;
        insert_note(&db, "nt_2", "notes/nt_2.md", USER).await;
        insert_note(&db, "nt_3", "notes/nt_3.md", USER).await;

        repo.set_note_tags("nt_1", &["popular".into(), "alpha".into()], USER)
            .await
            .unwrap();
        repo.set_note_tags("nt_2", &["popular".into(), "beta".into()], USER)
            .await
            .unwrap();
        repo.set_note_tags("nt_3", &["popular".into()], USER).await.unwrap();

        let rows = repo.list_with_counts(USER).await.unwrap();
        assert_eq!(rows.len(), 3);
        assert_eq!(rows[0].name, "popular");
        assert_eq!(rows[0].count, 3);
        assert_eq!(rows[1].name, "alpha");
        assert_eq!(rows[2].name, "beta");
    }

    #[tokio::test]
    async fn tags_for_notes_batches_results() {
        let (repo, db) = setup().await;
        insert_note(&db, "nt_1", "notes/nt_1.md", USER).await;
        insert_note(&db, "nt_2", "notes/nt_2.md", USER).await;
        repo.set_note_tags("nt_1", &["a".into(), "b".into()], USER)
            .await
            .unwrap();
        repo.set_note_tags("nt_2", &["c".into()], USER).await.unwrap();

        let grouped = repo
            .tags_for_notes(&["nt_1".into(), "nt_2".into(), "nt_missing".into()], USER)
            .await
            .unwrap();
        assert_eq!(grouped.len(), 2);
        let names = |tags: &[TagRow]| tags.iter().map(|t| t.name.clone()).collect::<Vec<_>>();
        assert_eq!(names(&grouped["nt_1"]), vec!["a".to_string(), "b".to_string()]);
        assert_eq!(names(&grouped["nt_2"]), vec!["c".to_string()]);
    }

    #[tokio::test]
    async fn cleanup_orphans_removes_unused_tags() {
        let (repo, db) = setup().await;
        insert_note(&db, "nt_1", "notes/nt_1.md", USER).await;
        repo.insert_ignore_all(&["orphan".into(), "kept".into()], USER)
            .await
            .unwrap();
        repo.set_note_tags("nt_1", &["kept".into()], USER).await.unwrap();

        let removed = repo.cleanup_orphans().await.unwrap();
        assert_eq!(removed.len(), 1);
        assert_eq!(removed[0].name, "orphan");
    }

    #[tokio::test]
    async fn list_all_note_tags_returns_all() {
        let (repo, db) = setup().await;
        insert_note(&db, "nt_1", "notes/nt_1.md", USER).await;
        insert_note(&db, "nt_2", "notes/nt_2.md", USER).await;
        repo.set_note_tags("nt_1", &["a".into()], USER).await.unwrap();
        repo.set_note_tags("nt_2", &["b".into()], USER).await.unwrap();

        let rows = repo.list_all_note_tags().await.unwrap();
        assert_eq!(rows.len(), 2);
    }
}
