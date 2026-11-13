//! The notes feature must be user-scoped.
//!
//! `notebooks`, `notes` and `note_tags` used to be global tables: every
//! account on the machine saw the same notebooks and notes. Migration 041
//! rebuilds them with a `user_id` ownership column, which is what
//! `adopt_system_default_data` discovers when it re-owns local data to the
//! first external account.
//!
//! `tags` stays global on purpose — it is a shared vocabulary, and
//! `note_tags` carries the per-account ownership instead.

use aionui_db::init_database_memory;

async fn has_column(pool: &sqlx::SqlitePool, table: &str, column: &str) -> bool {
    let count: i64 = sqlx::query_scalar("SELECT COUNT(*) FROM pragma_table_info(?) WHERE name = ?")
        .bind(table)
        .bind(column)
        .fetch_one(pool)
        .await
        .unwrap();
    count > 0
}

#[tokio::test]
async fn notes_tables_carry_a_user_id_column() {
    let db = init_database_memory().await.unwrap();
    let pool = db.pool();

    for table in ["notebooks", "notes", "note_tags"] {
        assert!(
            has_column(pool, table, "user_id").await,
            "{table} must have a user_id column"
        );
    }

    db.close().await;
}

#[tokio::test]
async fn existing_notes_rows_default_to_the_local_default_user() {
    // A fresh database has no rows; verify the column default instead.
    let db = init_database_memory().await.unwrap();
    let pool = db.pool();

    for table in ["notebooks", "notes", "note_tags"] {
        let default: Option<String> =
            sqlx::query_scalar("SELECT dflt_value FROM pragma_table_info(?) WHERE name = 'user_id'")
                .bind(table)
                .fetch_one(pool)
                .await
                .unwrap();
        let default = default.unwrap_or_default();
        assert!(
            default.contains("system_default_user"),
            "{table} rows must stay owned by system_default_user, got: {default}"
        );
    }

    db.close().await;
}

#[tokio::test]
async fn a_row_inserted_without_user_id_belongs_to_the_local_default_user() {
    let db = init_database_memory().await.unwrap();
    let pool = db.pool();

    // The existing repositories insert without a user_id column — the
    // DEFAULT must cover them.
    sqlx::query(
        "INSERT INTO notebooks (id, name, description, created_at, updated_at) VALUES ('nb1', 'Ideas', NULL, 1, 1)",
    )
    .execute(pool)
    .await
    .unwrap();
    sqlx::query("INSERT INTO notes (id, file_path, title, star, created_at, updated_at) VALUES ('n1', '/tmp/n1.md', 'Note', 0, 1, 1)")
        .execute(pool)
        .await
        .unwrap();
    sqlx::query("INSERT INTO tags (name) VALUES ('t1')")
        .execute(pool)
        .await
        .unwrap();
    sqlx::query("INSERT OR IGNORE INTO note_tags (note_id, tag_name) VALUES ('n1', 't1')")
        .execute(pool)
        .await
        .unwrap();

    for (table, column, key) in [
        ("notebooks", "id", "nb1"),
        ("notes", "id", "n1"),
        ("note_tags", "note_id", "n1"),
    ] {
        let user_id: String = sqlx::query_scalar(&format!("SELECT user_id FROM {table} WHERE {column} = ?"))
            .bind(key)
            .fetch_one(pool)
            .await
            .unwrap();
        assert_eq!(
            user_id, "system_default_user",
            "{table} must default to system_default_user"
        );
    }

    db.close().await;
}

#[tokio::test]
async fn notebook_names_are_unique_per_user_not_globally() {
    let db = init_database_memory().await.unwrap();
    let pool = db.pool();

    sqlx::query(
        "INSERT INTO notebooks (id, name, user_id, created_at, updated_at) VALUES ('nb1', 'Ideas', 'user-a', 1, 1)",
    )
    .execute(pool)
    .await
    .unwrap();
    // Same name, different account — must be allowed.
    sqlx::query(
        "INSERT INTO notebooks (id, name, user_id, created_at, updated_at) VALUES ('nb2', 'Ideas', 'user-b', 1, 1)",
    )
    .execute(pool)
    .await
    .unwrap();

    // Same name, same account — must be rejected.
    let duplicate = sqlx::query(
        "INSERT INTO notebooks (id, name, user_id, created_at, updated_at) VALUES ('nb3', 'Ideas', 'user-a', 1, 1)",
    )
    .execute(pool)
    .await;
    assert!(duplicate.is_err(), "duplicate name for the same user must be rejected");

    db.close().await;
}
