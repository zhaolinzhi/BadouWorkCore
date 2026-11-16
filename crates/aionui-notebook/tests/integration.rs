use std::sync::Arc;

use aionui_api_types::{CreateNoteRequest, CreateNotebookRequest, ListNotesQuery, UpdateNoteRequest};
use aionui_db::{
    INoteRepository, INotebookRepository, ITagRepository, NoteRow, SqliteNoteRepository, SqliteNotebookRepository,
    SqliteTagRepository, init_database_memory,
};
use aionui_notebook::error::NotebookError;
use aionui_notebook::file_store::MdFileStore;
use aionui_notebook::service::NotebookService;
use aionui_notebook::sync::WorkspaceSync;
use aionui_notebook::workspace::WorkspaceConfig;
use tempfile::TempDir;

async fn setup() -> (NotebookService, WorkspaceConfig, TempDir) {
    let db = init_database_memory().await.expect("init db");
    let pool = db.pool().clone();
    let tmp = tempfile::tempdir().unwrap();
    let workspace = WorkspaceConfig::resolve(tmp.path()).expect("workspace");
    let file_store = MdFileStore::new(workspace.notes_dir.clone());

    let notebook_repo: Arc<dyn INotebookRepository> = Arc::new(SqliteNotebookRepository::new(pool.clone()));
    let note_repo: Arc<dyn INoteRepository> = Arc::new(SqliteNoteRepository::new(pool.clone()));
    let tag_repo: Arc<dyn ITagRepository> = Arc::new(SqliteTagRepository::new(pool.clone()));

    let service = NotebookService::new(notebook_repo, note_repo, tag_repo, file_store, workspace.clone(), pool);
    (service, workspace, tmp)
}

/// 与隔离性无关的测试统一使用的账号 ID。
const TEST_USER: &str = "system_default_user";

#[tokio::test]
async fn create_and_read_note_roundtrips() {
    let (service, _ws, _tmp) = setup().await;
    let nb = service
        .create_notebook(
            CreateNotebookRequest {
                name: "Travel".into(),
                description: None,
            },
            TEST_USER,
        )
        .await
        .unwrap();
    let note = service
        .create_note(
            "",
            CreateNoteRequest {
                title: "Tokyo".into(),
                content: "Day 1 plan".into(),
                notebook_id: Some(nb.id.clone()),
                tags: vec!["japan".into()],
                summary: Some("Day 1".into()),
            },
            TEST_USER,
        )
        .await
        .unwrap();
    assert_eq!(note.title, "Tokyo");
    assert_eq!(note.notebook_id.as_deref(), Some(nb.id.as_str()));
    assert_eq!(note.tags, vec!["japan".to_string()]);

    let raw = service.get_note_raw(&note.id, TEST_USER).await.unwrap();
    // Body is the raw markdown content — no metadata block.
    assert_eq!(raw.content, "Day 1 plan");
    assert!(!raw.content.contains("<!-- aionui-meta"));
    assert!(!raw.content.contains("notebook:"));
}

#[tokio::test]
async fn update_note_overwrites_md_file() {
    let (service, _ws, _tmp) = setup().await;
    let note = service
        .create_note(
            "",
            CreateNoteRequest {
                title: "T".into(),
                content: "v1".into(),
                notebook_id: None,
                tags: vec![],
                summary: None,
            },
            TEST_USER,
        )
        .await
        .unwrap();
    service
        .update_note(
            &note.id,
            UpdateNoteRequest {
                title: None,
                content: Some("v2".into()),
                notebook_id: None,
                tags: None,
                summary: None,
                star: None,
            },
            TEST_USER,
        )
        .await
        .unwrap();
    let raw = service.get_note_raw(&note.id, TEST_USER).await.unwrap();
    assert!(raw.content.contains("v2"));
}

#[tokio::test]
async fn delete_note_removes_file_and_row() {
    let (service, _ws, _tmp) = setup().await;
    let note = service
        .create_note(
            "",
            CreateNoteRequest {
                title: "T".into(),
                content: "x".into(),
                notebook_id: None,
                tags: vec![],
                summary: None,
            },
            TEST_USER,
        )
        .await
        .unwrap();
    service.delete_note(&note.id, TEST_USER).await.unwrap();
    assert!(matches!(
        service.get_note(&note.id, TEST_USER).await,
        Err(NotebookError::NoteNotFound(_))
    ));
    let raw_err = service.get_note_raw(&note.id, TEST_USER).await.unwrap_err();
    assert!(matches!(raw_err, NotebookError::NoteNotFound(_)));
}

#[tokio::test]
async fn list_notes_filtered_by_notebook() {
    let (service, _ws, _tmp) = setup().await;
    let nb1 = service
        .create_notebook(
            CreateNotebookRequest {
                name: "Travel".into(),
                description: None,
            },
            TEST_USER,
        )
        .await
        .unwrap();
    let nb2 = service
        .create_notebook(
            CreateNotebookRequest {
                name: "Work".into(),
                description: None,
            },
            TEST_USER,
        )
        .await
        .unwrap();
    service
        .create_note(
            "",
            CreateNoteRequest {
                title: "T1".into(),
                content: "x".into(),
                notebook_id: Some(nb1.id.clone()),
                tags: vec![],
                summary: None,
            },
            TEST_USER,
        )
        .await
        .unwrap();
    service
        .create_note(
            "",
            CreateNoteRequest {
                title: "T2".into(),
                content: "y".into(),
                notebook_id: Some(nb1.id.clone()),
                tags: vec![],
                summary: None,
            },
            TEST_USER,
        )
        .await
        .unwrap();
    service
        .create_note(
            "",
            CreateNoteRequest {
                title: "W1".into(),
                content: "z".into(),
                notebook_id: Some(nb2.id.clone()),
                tags: vec![],
                summary: None,
            },
            TEST_USER,
        )
        .await
        .unwrap();

    let travel = service
        .list_notes_filtered(
            &ListNotesQuery {
                notebook_id: Some(nb1.id.clone()),
                ..Default::default()
            },
            TEST_USER,
        )
        .await
        .unwrap();
    assert_eq!(travel.len(), 2);
    assert!(travel.iter().all(|n| n.notebook_id.as_deref() == Some(nb1.id.as_str())));
}

#[tokio::test]
async fn toggle_star_flips() {
    let (service, _ws, _tmp) = setup().await;
    let note = service
        .create_note(
            "",
            CreateNoteRequest {
                title: "T".into(),
                content: "x".into(),
                notebook_id: None,
                tags: vec![],
                summary: None,
            },
            TEST_USER,
        )
        .await
        .unwrap();
    assert!(!note.star);
    let after = service.toggle_star(&note.id, TEST_USER).await.unwrap();
    assert!(after.star);
    let after2 = service.toggle_star(&note.id, TEST_USER).await.unwrap();
    assert!(!after2.star);
}

#[tokio::test]
async fn list_tags_returns_counts() {
    let (service, _ws, _tmp) = setup().await;
    service
        .create_note(
            "",
            CreateNoteRequest {
                title: "A".into(),
                content: "x".into(),
                notebook_id: None,
                tags: vec!["shared".into(), "a".into()],
                summary: None,
            },
            TEST_USER,
        )
        .await
        .unwrap();
    service
        .create_note(
            "",
            CreateNoteRequest {
                title: "B".into(),
                content: "y".into(),
                notebook_id: None,
                tags: vec!["shared".into(), "b".into()],
                summary: None,
            },
            TEST_USER,
        )
        .await
        .unwrap();
    let tags = service.list_tags(TEST_USER).await.unwrap();
    let shared = tags.tags.iter().find(|t| t.name == "shared").unwrap();
    assert_eq!(shared.count, 2);
}

#[tokio::test]
async fn create_note_with_unknown_notebook_id_returns_error() {
    let (service, _ws, _tmp) = setup().await;
    let err = service
        .create_note(
            "",
            CreateNoteRequest {
                title: "T".into(),
                content: "x".into(),
                notebook_id: Some("nb_does_not_exist".into()),
                tags: vec![],
                summary: None,
            },
            TEST_USER,
        )
        .await
        .unwrap_err();
    assert!(matches!(err, NotebookError::NotebookNotFound(_)));
}

#[tokio::test]
async fn update_note_can_clear_notebook_via_some_none() {
    let (service, _ws, _tmp) = setup().await;
    let nb = service
        .create_notebook(
            CreateNotebookRequest {
                name: "Travel".into(),
                description: None,
            },
            TEST_USER,
        )
        .await
        .unwrap();
    let note = service
        .create_note(
            "",
            CreateNoteRequest {
                title: "T".into(),
                content: "x".into(),
                notebook_id: Some(nb.id.clone()),
                tags: vec![],
                summary: None,
            },
            TEST_USER,
        )
        .await
        .unwrap();
    assert_eq!(note.notebook_id.as_deref(), Some(nb.id.as_str()));

    service
        .update_note(
            &note.id,
            UpdateNoteRequest {
                title: None,
                content: None,
                notebook_id: Some(None),
                tags: None,
                summary: None,
                star: None,
            },
            TEST_USER,
        )
        .await
        .unwrap();
    let updated = service.get_note(&note.id, TEST_USER).await.unwrap();
    assert!(updated.notebook_id.is_none());
}

#[tokio::test]
async fn reconcile_ignores_external_files() {
    let db = init_database_memory().await.unwrap();
    let pool = db.pool().clone();
    let tmp = tempfile::tempdir().unwrap();
    let workspace = WorkspaceConfig::resolve(tmp.path()).unwrap();
    let file_store = MdFileStore::new(workspace.notes_dir.clone());
    let notebook_repo: Arc<dyn INotebookRepository> = Arc::new(SqliteNotebookRepository::new(pool.clone()));
    let note_repo: Arc<dyn INoteRepository> = Arc::new(SqliteNoteRepository::new(pool.clone()));
    let tag_repo: Arc<dyn ITagRepository> = Arc::new(SqliteTagRepository::new(pool.clone()));

    // Drop an external MD file in the workspace before reconcile.
    // New behavior: stray files are NOT auto-ingested.
    let raw_path = workspace.notes_dir.join("external.md");
    std::fs::write(&raw_path, "manually written body").unwrap();

    let sync = WorkspaceSync::new(
        workspace.clone(),
        file_store,
        note_repo.clone(),
        notebook_repo,
        tag_repo.clone(),
    );
    let report = sync.reconcile().await.unwrap();
    // No ingestion happened.
    assert_eq!(report.inserted, 0);
    assert_eq!(report.removed, 0);
    // The file is reported as a parse failure (skipped).
    assert!(report.parse_failures.iter().any(|f| f == "notes/external.md"));

    // The DB has no record for this note.
    let found = note_repo
        .get_by_file_path("notes/external.md", "system_default_user")
        .await
        .unwrap();
    assert!(found.is_none());
}

#[tokio::test]
async fn reconcile_picks_up_external_file_removal() {
    let db = init_database_memory().await.unwrap();
    let pool = db.pool().clone();
    let tmp = tempfile::tempdir().unwrap();
    let workspace = WorkspaceConfig::resolve(tmp.path()).unwrap();
    let file_store = MdFileStore::new(workspace.notes_dir.clone());
    let notebook_repo: Arc<dyn INotebookRepository> = Arc::new(SqliteNotebookRepository::new(pool.clone()));
    let note_repo: Arc<dyn INoteRepository> = Arc::new(SqliteNoteRepository::new(pool.clone()));
    let tag_repo: Arc<dyn ITagRepository> = Arc::new(SqliteTagRepository::new(pool.clone()));

    let note_id = "nt_test_removal";
    note_repo
        .insert(&NoteRow {
            id: note_id.into(),
            file_path: "notes/missing.md".into(),
            title: "Ghost".into(),
            notebook_id: None,
            summary: None,
            star: 0,
            user_id: "system_default_user".into(),
            created_at: aionui_common::now_ms(),
            updated_at: aionui_common::now_ms(),
        })
        .await
        .unwrap();

    let sync = WorkspaceSync::new(workspace, file_store, note_repo.clone(), notebook_repo, tag_repo);
    let report = sync.reconcile().await.unwrap();
    assert_eq!(report.removed, 1);
    assert!(
        note_repo
            .get_by_id(note_id, "system_default_user")
            .await
            .unwrap()
            .is_none()
    );
}

#[tokio::test]
async fn duplicate_notebook_name_returns_error() {
    let (service, _ws, _tmp) = setup().await;
    service
        .create_notebook(
            CreateNotebookRequest {
                name: "Dup".into(),
                description: None,
            },
            TEST_USER,
        )
        .await
        .unwrap();
    let err = service
        .create_notebook(
            CreateNotebookRequest {
                name: "Dup".into(),
                description: None,
            },
            TEST_USER,
        )
        .await
        .unwrap_err();
    assert!(matches!(err, NotebookError::DuplicateName(_)));
}

#[tokio::test]
async fn get_note_raw_triggers_auto_repair_on_missing_file() {
    let (service, workspace, _tmp) = setup().await;
    let note = service
        .create_note(
            "",
            CreateNoteRequest {
                title: "T".into(),
                content: "body".into(),
                notebook_id: None,
                tags: vec![],
                summary: None,
            },
            TEST_USER,
        )
        .await
        .unwrap();
    std::fs::remove_file(workspace.to_absolute(&note.file_path)).unwrap();

    let raw = service.get_note_raw(&note.id, TEST_USER).await.unwrap();
    assert_eq!(raw.content, "");
    assert!(service.get_note(&note.id, TEST_USER).await.is_err());
}

// ── 账号隔离 ────────────────────────────────────────────────────

const USER_ALICE: &str = "user_alice";
const USER_BOB: &str = "user_bob";

#[tokio::test]
async fn list_notebooks_is_scoped_to_the_calling_user() {
    let (service, _ws, _tmp) = setup().await;
    service
        .create_notebook(
            CreateNotebookRequest {
                name: "Alice".into(),
                description: None,
            },
            USER_ALICE,
        )
        .await
        .unwrap();

    let bob_nbs = service.list_notebooks(USER_BOB).await.unwrap();
    assert!(bob_nbs.is_empty());

    let alice_nbs = service.list_notebooks(USER_ALICE).await.unwrap();
    assert_eq!(alice_nbs.len(), 1);
    assert_eq!(alice_nbs[0].name, "Alice");
}

#[tokio::test]
async fn list_notes_does_not_leak_across_users() {
    let (service, _ws, _tmp) = setup().await;
    let nb = service
        .create_notebook(
            CreateNotebookRequest {
                name: "Alice".into(),
                description: None,
            },
            USER_ALICE,
        )
        .await
        .unwrap();
    service
        .create_note(
            "",
            CreateNoteRequest {
                title: "Secret".into(),
                content: "x".into(),
                notebook_id: Some(nb.id.clone()),
                tags: vec![],
                summary: None,
            },
            USER_ALICE,
        )
        .await
        .unwrap();

    // Bob 不能在自己的笔记本视图里看到 Alice 的笔记本。
    let bob_by_nb = service.list_notes_by_notebook(&nb.id, USER_BOB).await;
    assert!(matches!(bob_by_nb, Err(NotebookError::NotebookNotFound(_))));

    // 全局过滤查询同样按账号隔离。
    let bob_all = service
        .list_notes_filtered(&ListNotesQuery::default(), USER_BOB)
        .await
        .unwrap();
    assert!(bob_all.is_empty());

    let alice_all = service
        .list_notes_filtered(&ListNotesQuery::default(), USER_ALICE)
        .await
        .unwrap();
    assert_eq!(alice_all.len(), 1);
    assert_eq!(alice_all[0].title, "Secret");
}

#[tokio::test]
async fn create_note_in_another_users_notebook_is_rejected() {
    let (service, _ws, _tmp) = setup().await;
    let nb = service
        .create_notebook(
            CreateNotebookRequest {
                name: "Alice".into(),
                description: None,
            },
            USER_ALICE,
        )
        .await
        .unwrap();

    let err = service
        .create_note(
            "",
            CreateNoteRequest {
                title: "Trespass".into(),
                content: "x".into(),
                notebook_id: Some(nb.id.clone()),
                tags: vec![],
                summary: None,
            },
            USER_BOB,
        )
        .await
        .unwrap_err();
    assert!(matches!(err, NotebookError::NotebookNotFound(_)));
}

#[tokio::test]
async fn notebook_name_uniqueness_is_per_user() {
    let (service, _ws, _tmp) = setup().await;
    let alice_nb = service
        .create_notebook(
            CreateNotebookRequest {
                name: "Ideas".into(),
                description: None,
            },
            USER_ALICE,
        )
        .await
        .unwrap();
    // 同名笔记本在另一个账号下应当允许创建。
    let bob_nb = service
        .create_notebook(
            CreateNotebookRequest {
                name: "Ideas".into(),
                description: None,
            },
            USER_BOB,
        )
        .await
        .unwrap();
    assert_ne!(alice_nb.id, bob_nb.id);

    // 同一账号下仍然保持唯一。
    let err = service
        .create_notebook(
            CreateNotebookRequest {
                name: "Ideas".into(),
                description: None,
            },
            USER_ALICE,
        )
        .await
        .unwrap_err();
    assert!(matches!(err, NotebookError::DuplicateName(_)));
}
