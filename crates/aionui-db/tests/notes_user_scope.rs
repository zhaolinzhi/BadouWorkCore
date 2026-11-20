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

const USER_ALICE: &str = "user_alice";
const USER_BOB: &str = "user_bob";

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

// ── Repository behaviour ──────────────────────────────────────────
//
// The schema-level checks above prove the `user_id` column exists. The
// tests below prove the repository layer actually honours it: every read
// and write is filtered by the owning account.

use aionui_db::{
    INoteRepository, INotebookRepository, ITagRepository, ListNotesFilter, NoteRow, NotebookRow, SqliteNoteRepository,
    SqliteNotebookRepository, SqliteTagRepository, UpdateNoteParams, UpdateNotebookParams,
};

/// Builds a repository triple over one in-memory database.
struct Repos {
    db: aionui_db::Database,
    notebook: SqliteNotebookRepository,
    note: SqliteNoteRepository,
    tag: SqliteTagRepository,
}

async fn setup() -> Repos {
    let db = init_database_memory().await.unwrap();
    let pool = db.pool().clone();
    Repos {
        notebook: SqliteNotebookRepository::new(pool.clone()),
        note: SqliteNoteRepository::new(pool.clone()),
        tag: SqliteTagRepository::new(pool),
        db,
    }
}

fn notebook_row(id: &str, name: &str, user_id: &str) -> NotebookRow {
    let now = aionui_common::now_ms();
    NotebookRow {
        id: id.into(),
        name: name.into(),
        description: None,
        user_id: user_id.into(),
        created_at: now,
        updated_at: now,
    }
}

fn note_row(id: &str, file_path: &str, user_id: &str) -> NoteRow {
    let now = aionui_common::now_ms();
    NoteRow {
        id: id.into(),
        file_path: file_path.into(),
        title: "Tokyo".into(),
        notebook_id: None,
        summary: None,
        star: 0,
        user_id: user_id.into(),
        created_at: now,
        updated_at: now,
    }
}

#[tokio::test]
async fn list_all_hides_other_users_notebooks() {
    let repos = setup().await;
    repos
        .notebook
        .insert(&notebook_row("nb_a", "Ideas", USER_ALICE))
        .await
        .unwrap();

    let alice_view = repos.notebook.list_all(USER_ALICE).await.unwrap();
    assert_eq!(alice_view.len(), 1);
    assert_eq!(alice_view[0].id, "nb_a");
    assert_eq!(alice_view[0].user_id, USER_ALICE);

    // The same call for another account must not see it.
    let bob_view = repos.notebook.list_all(USER_BOB).await.unwrap();
    assert!(bob_view.is_empty(), "user B must not see user A's notebooks");

    repos.db.close().await;
}

#[tokio::test]
async fn list_filtered_hides_other_users_notes() {
    let repos = setup().await;
    repos
        .note
        .insert(&note_row("nt_a", "notes/nt_a.md", USER_ALICE))
        .await
        .unwrap();

    let filter = ListNotesFilter::default();
    let alice_view = repos.note.list_filtered(&filter, USER_ALICE).await.unwrap();
    assert_eq!(alice_view.len(), 1);
    assert_eq!(alice_view[0].user_id, USER_ALICE);

    let bob_view = repos.note.list_filtered(&filter, USER_BOB).await.unwrap();
    assert!(bob_view.is_empty(), "user B must not see user A's notes");

    repos.db.close().await;
}

#[tokio::test]
async fn two_users_may_each_have_a_notebook_named_ideas() {
    let repos = setup().await;
    repos
        .notebook
        .insert(&notebook_row("nb_a", "Ideas", USER_ALICE))
        .await
        .unwrap();
    // The uniqueness constraint is now per-user, so this insert must succeed.
    repos
        .notebook
        .insert(&notebook_row("nb_b", "Ideas", USER_BOB))
        .await
        .unwrap();

    let alice_view = repos.notebook.list_all(USER_ALICE).await.unwrap();
    assert_eq!(alice_view.len(), 1);
    assert_eq!(alice_view[0].id, "nb_a");

    let bob_view = repos.notebook.list_all(USER_BOB).await.unwrap();
    assert_eq!(bob_view.len(), 1);
    assert_eq!(bob_view[0].id, "nb_b");

    // `find_by_name` is scoped too — each account finds only its own.
    let alice_named = repos.notebook.find_by_name("Ideas", USER_ALICE).await.unwrap().unwrap();
    assert_eq!(alice_named.id, "nb_a");
    let bob_named = repos.notebook.find_by_name("Ideas", USER_BOB).await.unwrap().unwrap();
    assert_eq!(bob_named.id, "nb_b");

    repos.db.close().await;
}

#[tokio::test]
async fn notebook_read_update_and_delete_are_scoped() {
    let repos = setup().await;
    repos
        .notebook
        .insert(&notebook_row("nb_a", "Ideas", USER_ALICE))
        .await
        .unwrap();

    // User B cannot read it.
    assert!(repos.notebook.get_by_id("nb_a", USER_BOB).await.unwrap().is_none());
    // …but user A can.
    assert!(repos.notebook.get_by_id("nb_a", USER_ALICE).await.unwrap().is_some());

    // User B cannot update it.
    let update = UpdateNotebookParams {
        name: Some("Hijacked".into()),
        ..Default::default()
    };
    let err = repos.notebook.update("nb_a", USER_BOB, &update).await.unwrap_err();
    assert!(matches!(err, aionui_db::DbError::NotFound(_)));
    let still_alice = repos.notebook.get_by_id("nb_a", USER_ALICE).await.unwrap().unwrap();
    assert_eq!(still_alice.name, "Ideas", "user B's update must not have landed");

    // User B cannot delete it.
    let err = repos.notebook.delete("nb_a", USER_BOB).await.unwrap_err();
    assert!(matches!(err, aionui_db::DbError::NotFound(_)));
    assert!(repos.notebook.get_by_id("nb_a", USER_ALICE).await.unwrap().is_some());

    // User A can update and delete it.
    repos.notebook.update("nb_a", USER_ALICE, &update).await.unwrap();
    let renamed = repos.notebook.get_by_id("nb_a", USER_ALICE).await.unwrap().unwrap();
    assert_eq!(renamed.name, "Hijacked");
    repos.notebook.delete("nb_a", USER_ALICE).await.unwrap();
    assert!(repos.notebook.get_by_id("nb_a", USER_ALICE).await.unwrap().is_none());

    repos.db.close().await;
}

#[tokio::test]
async fn note_read_update_and_delete_are_scoped() {
    let repos = setup().await;
    repos
        .note
        .insert(&note_row("nt_a", "notes/nt_a.md", USER_ALICE))
        .await
        .unwrap();

    assert!(repos.note.get_by_id("nt_a", USER_BOB).await.unwrap().is_none());
    assert!(repos.note.get_by_id("nt_a", USER_ALICE).await.unwrap().is_some());

    // `file_path` is only unique within an account's note set.
    assert!(
        repos
            .note
            .get_by_file_path("notes/nt_a.md", USER_BOB)
            .await
            .unwrap()
            .is_none()
    );
    assert!(
        repos
            .note
            .get_by_file_path("notes/nt_a.md", USER_ALICE)
            .await
            .unwrap()
            .is_some()
    );

    let update = UpdateNoteParams {
        title: Some("Hijacked".into()),
        ..Default::default()
    };
    let err = repos.note.update("nt_a", USER_BOB, &update).await.unwrap_err();
    assert!(matches!(err, aionui_db::DbError::NotFound(_)));
    let untouched = repos.note.get_by_id("nt_a", USER_ALICE).await.unwrap().unwrap();
    assert_eq!(untouched.title, "Tokyo");

    let err = repos.note.delete("nt_a", USER_BOB).await.unwrap_err();
    assert!(matches!(err, aionui_db::DbError::NotFound(_)));
    assert!(repos.note.get_by_id("nt_a", USER_ALICE).await.unwrap().is_some());

    repos.note.update("nt_a", USER_ALICE, &update).await.unwrap();
    repos.note.delete("nt_a", USER_ALICE).await.unwrap();
    assert!(repos.note.get_by_id("nt_a", USER_ALICE).await.unwrap().is_none());

    repos.db.close().await;
}

#[tokio::test]
async fn note_tags_are_scoped_while_the_tag_vocabulary_stays_global() {
    let repos = setup().await;
    repos
        .note
        .insert(&note_row("nt_a", "notes/nt_a.md", USER_ALICE))
        .await
        .unwrap();
    repos
        .note
        .insert(&note_row("nt_b", "notes/nt_b.md", USER_BOB))
        .await
        .unwrap();

    // Both accounts use the same tag name — the vocabulary is shared.
    repos
        .tag
        .set_note_tags("nt_a", &["shared".into()], USER_ALICE)
        .await
        .unwrap();
    repos
        .tag
        .set_note_tags("nt_b", &["shared".into()], USER_BOB)
        .await
        .unwrap();

    // The association rows are per-user.
    let alice_tags = repos.tag.tags_for_note("nt_a", USER_ALICE).await.unwrap();
    assert_eq!(alice_tags.len(), 1);
    assert_eq!(alice_tags[0].name, "shared");

    // User B must not see user A's association for A's note.
    let bob_tags = repos.tag.tags_for_note("nt_a", USER_BOB).await.unwrap();
    assert!(bob_tags.is_empty(), "user B must not see user A's note tags");

    // Batching is scoped as well.
    let grouped = repos
        .tag
        .tags_for_notes(&["nt_a".into(), "nt_b".into()], USER_ALICE)
        .await
        .unwrap();
    assert_eq!(grouped.len(), 1, "user A must only see their own note's tags");
    assert!(grouped.contains_key("nt_a"));
    assert!(!grouped.contains_key("nt_b"), "user A must not see user B's note tags");

    // `tags` itself stays global: one row, shared by both accounts.
    let vocabulary: i64 = sqlx::query_scalar("SELECT COUNT(*) FROM tags WHERE name = 'shared'")
        .fetch_one(repos.db.pool())
        .await
        .unwrap();
    assert_eq!(vocabulary, 1, "the tags vocabulary must remain global");

    // Counts only reflect the calling account's notes.
    let alice_counts = repos.tag.list_with_counts(USER_ALICE).await.unwrap();
    assert_eq!(alice_counts.len(), 1);
    assert_eq!(alice_counts[0].name, "shared");
    assert_eq!(alice_counts[0].count, 1);

    let bob_counts = repos.tag.list_with_counts(USER_BOB).await.unwrap();
    assert_eq!(bob_counts.len(), 1);
    assert_eq!(bob_counts[0].name, "shared");
    assert_eq!(bob_counts[0].count, 1);

    // Replacing user A's tags must not touch user B's associations.
    repos
        .tag
        .set_note_tags("nt_a", &["other".into()], USER_ALICE)
        .await
        .unwrap();
    let bob_still = repos.tag.tags_for_note("nt_b", USER_BOB).await.unwrap();
    assert_eq!(bob_still.len(), 1);
    assert_eq!(bob_still[0].name, "shared");

    repos.db.close().await;
}
