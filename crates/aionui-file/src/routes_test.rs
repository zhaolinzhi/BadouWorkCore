// `ApiError` is the type under test in the wire-mapping cases below.
#![allow(clippy::disallowed_types)]

use aionui_auth::CurrentUser;
use aionui_db::{UserStatus, UserType};
use axum::Router;
use axum::body::Body;
use axum::http::{Request, StatusCode};
use http_body_util::BodyExt;
use serde_json::{Value, json};
use tower::ServiceExt;

use super::fs_exists_router;

async fn send(router: &Router, method: &str, uri: &str, body: Option<Value>) -> (StatusCode, Value) {
    let builder = Request::builder().method(method).uri(uri);
    let request = match body {
        Some(v) => builder
            .header("content-type", "application/json")
            .body(Body::from(v.to_string()))
            .unwrap(),
        None => builder.body(Body::empty()).unwrap(),
    };
    let response = router.clone().oneshot(request).await.unwrap();
    let status = response.status();
    let bytes = response.into_body().collect().await.unwrap().to_bytes();
    let parsed = if bytes.is_empty() {
        Value::Null
    } else {
        serde_json::from_slice(&bytes).unwrap()
    };
    (status, parsed)
}

fn build_router() -> (Router, tempfile::TempDir) {
    let router = fs_exists_router().layer(axum::Extension(CurrentUser {
        id: "system_default_user".to_owned(),
        username: "admin".to_owned(),
        user_type: UserType::Local,
        status: UserStatus::Active,
    }));
    let dir = tempfile::tempdir().unwrap();
    (router, dir)
}

#[tokio::test]
async fn fs_exists_returns_true_for_existing_dir() {
    let (router, dir) = build_router();
    let body = json!({ "path": dir.path().to_string_lossy() });
    let (status, payload) = send(&router, "POST", "/api/fs/exists", Some(body)).await;
    assert_eq!(status, StatusCode::OK);
    assert_eq!(payload["data"]["exists"], true);
}

#[tokio::test]
async fn fs_exists_returns_false_for_missing() {
    let (router, _dir) = build_router();
    let body = json!({ "path": "/nonexistent/__aionui_test__/missing" });
    let (status, payload) = send(&router, "POST", "/api/fs/exists", Some(body)).await;
    assert_eq!(status, StatusCode::OK);
    assert_eq!(payload["data"]["exists"], false);
}

#[tokio::test]
async fn fs_exists_rejects_empty_path() {
    let (router, _dir) = build_router();
    let body = json!({ "path": "" });
    let (status, _payload) = send(&router, "POST", "/api/fs/exists", Some(body)).await;
    assert_eq!(status, StatusCode::BAD_REQUEST);
}
