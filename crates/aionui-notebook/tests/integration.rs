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
    let file_store = MdFileStore::new(tmp.path().to_path_buf());

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
    let file_store = MdFileStore::new(tmp.path().to_path_buf());
    let notebook_repo: Arc<dyn INotebookRepository> = Arc::new(SqliteNotebookRepository::new(pool.clone()));
    let note_repo: Arc<dyn INoteRepository> = Arc::new(SqliteNoteRepository::new(pool.clone()));
    let tag_repo: Arc<dyn ITagRepository> = Arc::new(SqliteTagRepository::new(pool.clone()));

    // Drop an external MD file in the workspace before reconcile.
    // New behavior: stray files are NOT auto-ingested.
    // 正文按账号存放，因此文件要落在被 reconcile 的账号目录里。
    let raw_path = aionui_notebook::workspace::user_notes_dir(tmp.path(), "system_default_user").join("external.md");
    std::fs::create_dir_all(raw_path.parent().unwrap()).unwrap();
    std::fs::write(&raw_path, "manually written body").unwrap();

    let sync = WorkspaceSync::new(
        workspace.clone(),
        file_store,
        note_repo.clone(),
        notebook_repo,
        tag_repo.clone(),
    );
    let report = sync.reconcile_for("system_default_user").await.unwrap();
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
    let file_store = MdFileStore::new(tmp.path().to_path_buf());
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
    let report = sync.reconcile_for("system_default_user").await.unwrap();
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
    let (service, _workspace, tmp) = setup().await;
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
    // 正文落在账号自己的目录里，删除时要用该目录拼出绝对路径。
    let abs = aionui_notebook::workspace::user_notes_dir(tmp.path(), TEST_USER)
        .join(note.file_path.rsplit('/').next().unwrap());
    std::fs::remove_file(&abs).unwrap();

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

/// 笔记正文必须落在所属账号自己的目录里，而不是共享的 `notes/`。
#[tokio::test]
async fn note_files_land_in_the_owning_users_directory() {
    let (service, _ws, tmp) = setup().await;

    let nb = service
        .create_notebook(
            CreateNotebookRequest {
                name: "Ideas".into(),
                description: None,
            },
            USER_ALICE,
        )
        .await
        .unwrap();

    let note = service
        .create_note(
            &nb.id,
            CreateNoteRequest {
                title: "Hello".into(),
                content: "body".into(),
                notebook_id: None,
                tags: vec![],
                summary: None,
            },
            USER_ALICE,
        )
        .await
        .unwrap();

    // 正文必须位于 <root>/users/alice/notes/ 下，而不是共享的 notes/。
    let expected = tmp.path().join("users").join("alice").join("notes");
    let file_name = note.file_path.rsplit('/').next().unwrap();
    assert!(
        expected.join(file_name).exists(),
        "the note body must be written under the owner's directory: {}",
        expected.display()
    );
}

/// 两个账号的笔记正文必须落在不同的目录里。
#[tokio::test]
async fn note_files_of_two_users_do_not_share_a_directory() {
    let (service, _ws, tmp) = setup().await;

    let alice_note = service
        .create_note(
            "",
            CreateNoteRequest {
                title: "A".into(),
                content: "alice body".into(),
                notebook_id: None,
                tags: vec![],
                summary: None,
            },
            USER_ALICE,
        )
        .await
        .unwrap();
    let bob_note = service
        .create_note(
            "",
            CreateNoteRequest {
                title: "B".into(),
                content: "bob body".into(),
                notebook_id: None,
                tags: vec![],
                summary: None,
            },
            USER_BOB,
        )
        .await
        .unwrap();

    let alice_dir = tmp.path().join("users").join("alice").join("notes");
    let bob_dir = tmp.path().join("users").join("bob").join("notes");
    let alice_file = alice_note.file_path.rsplit('/').next().unwrap();
    let bob_file = bob_note.file_path.rsplit('/').next().unwrap();

    assert!(
        alice_dir.join(alice_file).exists(),
        "alice's body must be under her own directory"
    );
    assert!(
        bob_dir.join(bob_file).exists(),
        "bob's body must be under his own directory"
    );
    // 共享的 notes/ 目录下不应出现任何正文文件。
    assert!(!tmp.path().join("notes").join(alice_file).exists());
    assert!(!tmp.path().join("notes").join(bob_file).exists());
}

/// 数据库里保存的 `file_path` 仍然是相对路径 `notes/<uuid>.md`。
#[tokio::test]
async fn stored_file_path_stays_relative_to_the_workspace_root() {
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
            USER_ALICE,
        )
        .await
        .unwrap();

    assert!(
        note.file_path.starts_with("notes/"),
        "unexpected file_path: {}",
        note.file_path
    );
    assert!(
        !note.file_path.contains("users/"),
        "unexpected file_path: {}",
        note.file_path
    );
}

// ── 按账号 reconcile ────────────────────────────────────────────

/// 构造一份独立的 sync 夹具，返回 `(sync, note_repo, 临时目录)`。
async fn sync_fixture() -> (WorkspaceSync, Arc<dyn INoteRepository>, TempDir) {
    let db = init_database_memory().await.unwrap();
    let pool = db.pool().clone();
    let tmp = tempfile::tempdir().unwrap();
    let workspace = WorkspaceConfig::resolve(tmp.path()).unwrap();
    let file_store = MdFileStore::new(tmp.path().to_path_buf());
    let notebook_repo: Arc<dyn INotebookRepository> = Arc::new(SqliteNotebookRepository::new(pool.clone()));
    let note_repo: Arc<dyn INoteRepository> = Arc::new(SqliteNoteRepository::new(pool.clone()));
    let tag_repo: Arc<dyn ITagRepository> = Arc::new(SqliteTagRepository::new(pool.clone()));

    let sync = WorkspaceSync::new(workspace, file_store, note_repo.clone(), notebook_repo, tag_repo);
    (sync, note_repo, tmp)
}

/// 插入一行笔记（不落盘），用于构造“磁盘上没有正文”的孤儿行。
async fn insert_note_row(note_repo: &Arc<dyn INoteRepository>, id: &str, file_path: &str, user_id: &str) {
    note_repo
        .insert(&NoteRow {
            id: id.into(),
            file_path: file_path.into(),
            title: id.into(),
            notebook_id: None,
            summary: None,
            star: 0,
            user_id: user_id.into(),
            created_at: aionui_common::now_ms(),
            updated_at: aionui_common::now_ms(),
        })
        .await
        .unwrap();
}

/// 为某个账号在磁盘上写一个正文文件，并插入对应的数据库行。
async fn seed_note(note_repo: &Arc<dyn INoteRepository>, tmp: &TempDir, id: &str, file_name: &str, user_id: &str) {
    let dir = aionui_notebook::workspace::user_notes_dir(tmp.path(), user_id);
    std::fs::create_dir_all(&dir).unwrap();
    std::fs::write(dir.join(file_name), "body").unwrap();
    insert_note_row(note_repo, id, &format!("notes/{file_name}"), user_id).await;
}

/// 为某个账号在**旧版共享目录**里写一个正文文件，并插入对应的数据库行。
///
/// 模拟多账号改造之前的状态：所有账号的正文都写在同一个共享的 `notes/` 目录里。
async fn seed_legacy_note(
    note_repo: &Arc<dyn INoteRepository>,
    tmp: &TempDir,
    id: &str,
    file_name: &str,
    user_id: &str,
) {
    let legacy_dir = tmp.path().join("notes");
    std::fs::create_dir_all(&legacy_dir).unwrap();
    std::fs::write(legacy_dir.join(file_name), "legacy body").unwrap();
    insert_note_row(note_repo, id, &format!("notes/{file_name}"), user_id).await;
}

/// reconcile 一个账号，绝不能删掉另一个账号的行。
#[tokio::test]
async fn reconcile_for_one_user_keeps_another_users_rows() {
    let (sync, note_repo, tmp) = sync_fixture().await;
    seed_note(&note_repo, &tmp, "nt_alice", "alice.md", USER_ALICE).await;
    seed_note(&note_repo, &tmp, "nt_bob", "bob.md", USER_BOB).await;

    let report = sync.reconcile_for(USER_ALICE).await.unwrap();

    // Alice 的正文在自己的目录里，行必须保留。
    assert_eq!(report.removed, 0);
    assert!(note_repo.get_by_id("nt_alice", USER_ALICE).await.unwrap().is_some());
    // Bob 的正文在 Bob 自己的目录里，Alice 的 reconcile 不得动它。
    assert!(note_repo.get_by_id("nt_bob", USER_BOB).await.unwrap().is_some());
}

/// reconcile 一个账号时，只清理这个账号自己的孤儿行。
#[tokio::test]
async fn reconcile_for_one_user_only_deletes_its_own_orphan_rows() {
    let (sync, note_repo, _tmp) = sync_fixture().await;
    insert_note_row(&note_repo, "nt_ghost_alice", "notes/missing_alice.md", USER_ALICE).await;
    insert_note_row(&note_repo, "nt_ghost_bob", "notes/missing_bob.md", USER_BOB).await;

    let report = sync.reconcile_for(USER_ALICE).await.unwrap();

    assert_eq!(report.removed, 1);
    assert!(
        note_repo
            .get_by_id("nt_ghost_alice", USER_ALICE)
            .await
            .unwrap()
            .is_none()
    );
    // Bob 的孤儿行不在 Alice 的作用域内，必须保留。
    assert!(note_repo.get_by_id("nt_ghost_bob", USER_BOB).await.unwrap().is_some());
}

/// 旧版共享目录里的正文必须被迁移进拥有它的账号目录。
#[tokio::test]
async fn legacy_shared_notes_are_migrated_into_the_owning_users_directory() {
    let (sync, note_repo, tmp) = sync_fixture().await;
    seed_legacy_note(&note_repo, &tmp, "nt_legacy", "legacy.md", TEST_USER).await;

    let legacy_file = tmp.path().join("notes").join("legacy.md");
    let target_file = aionui_notebook::workspace::user_notes_dir(tmp.path(), TEST_USER).join("legacy.md");
    assert!(legacy_file.exists());

    sync.reconcile_for(TEST_USER).await.unwrap();

    // 正文已经搬进该账号的目录，旧目录里不再有它。
    assert!(
        target_file.exists(),
        "legacy body must be migrated into the owner's directory"
    );
    assert!(
        !legacy_file.exists(),
        "the legacy shared directory must not keep the body"
    );
    // 行必须保留（正文没有丢）。
    assert!(note_repo.get_by_id("nt_legacy", TEST_USER).await.unwrap().is_some());
}

/// 别的账号不能把旧版共享目录里的正文抢走。
#[tokio::test]
async fn legacy_shared_notes_are_not_stolen_by_another_user() {
    let (sync, note_repo, tmp) = sync_fixture().await;
    seed_legacy_note(&note_repo, &tmp, "nt_legacy", "legacy.md", USER_ALICE).await;

    let legacy_file = tmp.path().join("notes").join("legacy.md");

    // Bob 的 reconcile 不能动 Alice 的正文。
    sync.reconcile_for(USER_BOB).await.unwrap();
    assert!(legacy_file.exists(), "another user must not steal the legacy body");
    assert!(note_repo.get_by_id("nt_legacy", USER_ALICE).await.unwrap().is_some());

    // 真正的主人 reconcile 时才搬走。
    sync.reconcile_for(USER_ALICE).await.unwrap();
    let target_file = aionui_notebook::workspace::user_notes_dir(tmp.path(), USER_ALICE).join("legacy.md");
    assert!(target_file.exists(), "the owning user must receive the legacy body");
    assert!(!legacy_file.exists());
}

/// 行级 adopt 把行改属新主人之后，正文要跟着搬到新主人目录里。
///
/// `adopt_system_default_data` 只改数据库里的归属，正文还在默认账号目录下；
/// 新主人第一次读笔记时把正文接过来，否则 reconcile 会把它当成孤儿删掉。
#[tokio::test]
async fn adopted_notes_are_handed_over_to_the_new_owner() {
    let (sync, note_repo, tmp) = sync_fixture().await;

    // 正文在默认账号目录下，行已经属于 Alice（模拟 adopt 之后的状态）。
    let default_dir = aionui_notebook::workspace::user_notes_dir(tmp.path(), TEST_USER);
    std::fs::create_dir_all(&default_dir).unwrap();
    std::fs::write(default_dir.join("adopted.md"), "body").unwrap();
    insert_note_row(&note_repo, "nt_adopted", "notes/adopted.md", USER_ALICE).await;

    let report = sync.reconcile_for(USER_ALICE).await.unwrap();

    // 正文搬到了 Alice 自己的目录，行也保住了。
    let alice_dir = aionui_notebook::workspace::user_notes_dir(tmp.path(), USER_ALICE);
    assert!(
        alice_dir.join("adopted.md").exists(),
        "the adopted body must be handed over to the new owner"
    );
    assert_eq!(report.removed, 0);
    assert!(note_repo.get_by_id("nt_adopted", USER_ALICE).await.unwrap().is_some());
}

/// 旧版目录迁移只做一次：迁移完成后第二个账号的 reconcile 不会再动它。
#[tokio::test]
async fn legacy_migration_runs_at_most_once() {
    let (sync, note_repo, tmp) = sync_fixture().await;
    seed_legacy_note(&note_repo, &tmp, "nt_legacy", "legacy.md", TEST_USER).await;

    sync.reconcile_for(TEST_USER).await.unwrap();
    let target_file = aionui_notebook::workspace::user_notes_dir(tmp.path(), TEST_USER).join("legacy.md");
    assert!(target_file.exists());

    // 迁移标记已经落盘，重复的 reconcile 不会再搬动任何东西。
    let marker = tmp.path().join(".notes-legacy-migrated");
    assert!(marker.exists(), "the one-shot migration marker must be written");

    // 之后再造一个旧目录文件，重复 reconcile 也不该被搬走（迁移已结束）。
    let stray = tmp.path().join("notes").join("stray.md");
    std::fs::create_dir_all(tmp.path().join("notes")).unwrap();
    std::fs::write(&stray, "stray").unwrap();
    sync.reconcile_for(TEST_USER).await.unwrap();
    assert!(
        stray.exists(),
        "the legacy migration must not run again after the marker is written"
    );
}

/// 全新安装（没有旧版目录）时，reconcile 不会失败。
#[tokio::test]
async fn reconcile_without_legacy_directory_is_a_noop() {
    let (sync, note_repo, tmp) = sync_fixture().await;
    seed_note(&note_repo, &tmp, "nt_alice", "alice.md", USER_ALICE).await;

    // 删掉旧版共享目录，模拟全新安装。
    std::fs::remove_dir_all(tmp.path().join("notes")).unwrap();

    let report = sync.reconcile_for(USER_ALICE).await.unwrap();
    assert_eq!(report.removed, 0);
    assert!(note_repo.get_by_id("nt_alice", USER_ALICE).await.unwrap().is_some());
}

// ── service 层的按账号同步 ──────────────────────────────────────

/// 读路径会触发一次按账号的 reconcile，并且只跑一次。
#[tokio::test]
async fn read_paths_sync_the_user_workspace_once() {
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
            USER_ALICE,
        )
        .await
        .unwrap();

    // 第一次读会触发 reconcile：把磁盘上的正文删掉后，行应当被清理掉。
    service
        .list_notes_filtered(&ListNotesQuery::default(), USER_ALICE)
        .await
        .unwrap();
    service.ensure_user_workspace_synced(USER_ALICE).await.unwrap();
    // 第二次 sync 已经被记住，不会重复执行。
    service.ensure_user_workspace_synced(USER_ALICE).await.unwrap();
    assert!(service.get_note(&note.id, USER_ALICE).await.is_ok());
}
