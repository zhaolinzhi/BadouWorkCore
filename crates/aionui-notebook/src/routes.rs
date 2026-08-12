#![allow(clippy::disallowed_types)]

use axum::Json;
use axum::Router;
use axum::extract::Query;
use axum::extract::rejection::JsonRejection;
use axum::extract::{Extension, Json as ExtJson, Path, State};
use axum::http::StatusCode;
use axum::response::IntoResponse;
use axum::routing::{get, post};

use aionui_api_types::{
    ApiResponse, CreateNoteRequest, CreateNotebookRequest, ListNotesQuery, NoteResponse, NotebookResponse,
    StarToggleResponse, TagsListResponse, UpdateNoteRequest, UpdateNotebookRequest,
};
use aionui_auth::CurrentUser;
use aionui_common::ApiError;
use aionui_db::DbError;
use serde::Serialize;

use crate::error::NotebookError;
use crate::state::NotebookRouterState;

/// 将数据库层错误映射为 API 层错误。
fn db_error_to_api_error(err: DbError) -> ApiError {
    match err {
        DbError::NotFound(msg) => ApiError::NotFound(msg),
        DbError::Conflict(msg) => ApiError::Conflict(msg),
        DbError::Query(e) => ApiError::Internal(format!("Database error: {e}")),
        DbError::Migration(e) => ApiError::Internal(format!("Migration error: {e}")),
        DbError::Init(msg) => ApiError::Internal(format!("Database init error: {msg}")),
    }
}

/// 将业务层 `NotebookError` 统一映射为 HTTP 层 `ApiError`。
impl From<NotebookError> for ApiError {
    fn from(err: NotebookError) -> Self {
        match err {
            NotebookError::NotebookNotFound(msg) => ApiError::NotFound(msg),
            NotebookError::NoteNotFound(msg) => ApiError::NotFound(msg),
            NotebookError::InvalidRequest(msg) => ApiError::BadRequest(msg),
            NotebookError::WorkspaceInit(msg) => ApiError::Internal(format!("Workspace error: {msg}")),
            NotebookError::FileIo { path, source } => {
                ApiError::Internal(format!("File I/O error at '{path}': {source}"))
            }
            NotebookError::FileNotFound(_) => ApiError::Internal("File not found (auto-repaired)".into()),
            NotebookError::InvalidMetadata(msg) => ApiError::BadRequest(format!("Invalid metadata: {msg}")),
            NotebookError::DuplicateName(msg) => ApiError::Conflict(msg),
            NotebookError::Database(db_err) => db_error_to_api_error(db_err),
            NotebookError::Json(e) => ApiError::Internal(format!("JSON error: {e}")),
        }
    }
}

#[derive(Serialize)]
struct NotebookWithNotesResponse {
    notebook: NotebookResponse,
    notes: Vec<NoteResponse>,
}

#[derive(Serialize)]
struct NotebookListResponse {
    notebooks: Vec<NotebookResponse>,
}

#[derive(Serialize)]
struct NoteListResponse {
    notes: Vec<NoteResponse>,
}

/// 构建 `notebook` 子路由，挂在 Axum Router 上。
///
/// 路由前缀均为 `/api/...`，具体见 [`notebook_routes`] 中每条 `.route(...)`。
pub fn notebook_routes(state: NotebookRouterState) -> Router {
    Router::new()
        // Notebooks
        .route("/api/notebooks", get(list_notebooks).post(create_notebook))
        .route(
            "/api/notebooks/{id}",
            get(get_notebook).put(update_notebook).delete(delete_notebook),
        )
        .route(
            "/api/notebooks/{id}/notes",
            get(list_notes_by_notebook).post(create_note),
        )
        // Notes (top-level)
        .route("/api/notes", get(list_notes).post(create_note_top))
        .route("/api/notes/{id}", get(get_note).put(update_note).delete(delete_note))
        .route("/api/notes/{id}/raw", get(get_note_raw))
        .route("/api/notes/{id}/star", post(toggle_star))
        // Tags
        .route("/api/tags", get(list_tags))
        .with_state(state)
}

// ── Notebook 路由处理器 ──────────────────────────────────────────

/// `GET /api/notebooks` — 列出全部笔记本。
async fn list_notebooks(
    State(state): State<NotebookRouterState>,
    Extension(_user): Extension<CurrentUser>,
) -> Result<Json<ApiResponse<NotebookListResponse>>, ApiError> {
    let notebooks = state.service.list_notebooks().await?;
    Ok(Json(ApiResponse::ok(NotebookListResponse { notebooks })))
}

/// `POST /api/notebooks` — 创建笔记本。
async fn create_notebook(
    State(state): State<NotebookRouterState>,
    Extension(_user): Extension<CurrentUser>,
    body: Result<ExtJson<CreateNotebookRequest>, JsonRejection>,
) -> Result<(StatusCode, Json<ApiResponse<NotebookResponse>>), ApiError> {
    let ExtJson(req) = body.map_err(ApiError::from)?;
    let notebook = state.service.create_notebook(req).await?;
    Ok((StatusCode::CREATED, Json(ApiResponse::ok(notebook))))
}

/// `GET /api/notebooks/{id}` — 获取笔记本详情（含其下全部笔记）。
async fn get_notebook(
    State(state): State<NotebookRouterState>,
    Extension(_user): Extension<CurrentUser>,
    Path(id): Path<String>,
) -> Result<Json<ApiResponse<NotebookWithNotesResponse>>, ApiError> {
    let (notebook, notes) = state.service.get_notebook_with_notes(&id).await?;
    Ok(Json(ApiResponse::ok(NotebookWithNotesResponse { notebook, notes })))
}

/// `PUT /api/notebooks/{id}` — 更新笔记本元数据。
async fn update_notebook(
    State(state): State<NotebookRouterState>,
    Extension(_user): Extension<CurrentUser>,
    Path(id): Path<String>,
    body: Result<ExtJson<UpdateNotebookRequest>, JsonRejection>,
) -> Result<Json<ApiResponse<NotebookResponse>>, ApiError> {
    let ExtJson(req) = body.map_err(ApiError::from)?;
    let notebook = state.service.update_notebook(&id, req).await?;
    Ok(Json(ApiResponse::ok(notebook)))
}

/// `DELETE /api/notebooks/{id}` — 删除笔记本。
async fn delete_notebook(
    State(state): State<NotebookRouterState>,
    Extension(_user): Extension<CurrentUser>,
    Path(id): Path<String>,
) -> Result<Json<ApiResponse<()>>, ApiError> {
    state.service.delete_notebook(&id).await?;
    Ok(Json(ApiResponse::success()))
}

// ── Note 路由处理器 ──────────────────────────────────────────────

/// `GET /api/notebooks/{id}/notes` — 列出指定笔记本下的全部笔记。
async fn list_notes_by_notebook(
    State(state): State<NotebookRouterState>,
    Extension(_user): Extension<CurrentUser>,
    Path(id): Path<String>,
) -> Result<Json<ApiResponse<NoteListResponse>>, ApiError> {
    let notes = state.service.list_notes_by_notebook(&id).await?;
    Ok(Json(ApiResponse::ok(NoteListResponse { notes })))
}

/// `POST /api/notebooks/{id}/notes` — 在指定笔记本下创建笔记。
async fn create_note(
    State(state): State<NotebookRouterState>,
    Extension(_user): Extension<CurrentUser>,
    Path(id): Path<String>,
    body: Result<ExtJson<CreateNoteRequest>, JsonRejection>,
) -> Result<(StatusCode, Json<ApiResponse<NoteResponse>>), ApiError> {
    let ExtJson(req) = body.map_err(ApiError::from)?;
    let note = state.service.create_note(&id, req).await?;
    Ok((StatusCode::CREATED, Json(ApiResponse::ok(note))))
}

/// `GET /api/notes` — 按查询条件（`notebook_id`、`tag`、`starred`、`limit`、`offset`）列出笔记。
async fn list_notes(
    State(state): State<NotebookRouterState>,
    Extension(_user): Extension<CurrentUser>,
    Query(query): Query<ListNotesQuery>,
) -> Result<Json<ApiResponse<NoteListResponse>>, ApiError> {
    let notes = state.service.list_notes_filtered(&query).await?;
    Ok(Json(ApiResponse::ok(NoteListResponse { notes })))
}

/// `POST /api/notes` — 顶层入口创建笔记。`req.notebook_id` 优先，
/// 路径中的笔记本 id 会传入但被忽略（service 层实际以请求体为准）。
async fn create_note_top(
    State(state): State<NotebookRouterState>,
    Extension(_user): Extension<CurrentUser>,
    body: Result<ExtJson<CreateNoteRequest>, JsonRejection>,
) -> Result<(StatusCode, Json<ApiResponse<NoteResponse>>), ApiError> {
    let ExtJson(req) = body.map_err(ApiError::from)?;
    // Notebook id path param is irrelevant; req.notebook takes precedence.
    let note = state.service.create_note("", req).await?;
    Ok((StatusCode::CREATED, Json(ApiResponse::ok(note))))
}

/// `GET /api/notes/{id}` — 获取笔记元数据（含标签）。
async fn get_note(
    State(state): State<NotebookRouterState>,
    Extension(_user): Extension<CurrentUser>,
    Path(id): Path<String>,
) -> Result<Json<ApiResponse<NoteResponse>>, ApiError> {
    let note = state.service.get_note(&id).await?;
    Ok(Json(ApiResponse::ok(note)))
}

/// `GET /api/notes/{id}/raw` — 获取笔记的原始 Markdown 正文。
///
/// 响应 `Content-Type: text/plain; charset=utf-8`，直接返回文件正文。
/// 若磁盘文件缺失（自愈后），正文为空字符串。
async fn get_note_raw(
    State(state): State<NotebookRouterState>,
    Extension(_user): Extension<CurrentUser>,
    Path(id): Path<String>,
) -> Result<axum::response::Response, ApiError> {
    let raw = state.service.get_note_raw(&id).await?;
    Ok((
        StatusCode::OK,
        [(axum::http::header::CONTENT_TYPE, "text/plain; charset=utf-8")],
        raw.content,
    )
        .into_response())
}

/// `PUT /api/notes/{id}` — 更新笔记。
async fn update_note(
    State(state): State<NotebookRouterState>,
    Extension(_user): Extension<CurrentUser>,
    Path(id): Path<String>,
    body: Result<ExtJson<UpdateNoteRequest>, JsonRejection>,
) -> Result<Json<ApiResponse<NoteResponse>>, ApiError> {
    let ExtJson(req) = body.map_err(ApiError::from)?;
    let note = state.service.update_note(&id, req).await?;
    Ok(Json(ApiResponse::ok(note)))
}

/// `DELETE /api/notes/{id}` — 删除笔记。
async fn delete_note(
    State(state): State<NotebookRouterState>,
    Extension(_user): Extension<CurrentUser>,
    Path(id): Path<String>,
) -> Result<Json<ApiResponse<()>>, ApiError> {
    state.service.delete_note(&id).await?;
    Ok(Json(ApiResponse::success()))
}

/// `POST /api/notes/{id}/star` — 切换笔记星标状态。
async fn toggle_star(
    State(state): State<NotebookRouterState>,
    Extension(_user): Extension<CurrentUser>,
    Path(id): Path<String>,
) -> Result<Json<ApiResponse<StarToggleResponse>>, ApiError> {
    let resp = state.service.toggle_star(&id).await?;
    Ok(Json(ApiResponse::ok(resp)))
}

/// `GET /api/tags` — 列出全部标签及其被引用次数。
async fn list_tags(
    State(state): State<NotebookRouterState>,
    Extension(_user): Extension<CurrentUser>,
) -> Result<Json<ApiResponse<TagsListResponse>>, ApiError> {
    let tags = state.service.list_tags().await?;
    Ok(Json(ApiResponse::ok(tags)))
}
