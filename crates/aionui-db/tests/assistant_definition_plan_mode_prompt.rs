//! Integration tests for assistant_definitions repository plan_mode_prompt_template support.
//!
//! Run with: cargo test -p aionui-db --test assistant_definition_plan_mode_prompt

use aionui_db::{
    AssistantDefinitionRow, IAssistantDefinitionRepository, SqliteAssistantDefinitionRepository,
    UpsertAssistantDefinitionParams, init_database_memory,
};
use sqlx::SqlitePool;

fn minimal_params<'a>(id: &'a str, assistant_id: &'a str, agent_id: &'a str) -> UpsertAssistantDefinitionParams<'a> {
    UpsertAssistantDefinitionParams {
        id,
        assistant_id,
        source: "user",
        owner_type: "user",
        source_ref: None,
        name: "Test Assistant",
        name_i18n: "{}",
        description: None,
        description_i18n: "{}",
        avatar_type: "emoji",
        avatar_value: None,
        agent_id,
        rule_resource_type: "user_file",
        rule_resource_ref: None,
        recommended_prompts: "[]",
        recommended_prompts_i18n: "{}",
        default_model_mode: "auto",
        default_model_value: None,
        default_permission_mode: "auto",
        default_permission_value: None,
        default_thought_level_mode: "auto",
        default_thought_level_value: None,
        default_skills_mode: "auto",
        default_skill_ids: "[]",
        custom_skill_names: "[]",
        default_disabled_builtin_skill_ids: "[]",
        default_mcps_mode: "auto",
        default_mcp_ids: "[]",
        plan_mode_prompt_template: None,
    }
}

async fn fresh_repo() -> (SqlitePool, SqliteAssistantDefinitionRepository) {
    let db = init_database_memory().await.expect("init memory db");
    let pool = db.pool().clone();
    let repo = SqliteAssistantDefinitionRepository::new(pool.clone());
    (pool, repo)
}

#[tokio::test]
async fn upsert_persists_plan_mode_prompt_template() {
    let (_pool, repo) = fresh_repo().await;
    let params = UpsertAssistantDefinitionParams {
        plan_mode_prompt_template: Some("Always emit a 4-step plan before coding."),
        ..minimal_params("def_1", "asst_1", "agent_1")
    };

    repo.upsert_for_user("system_default_user", &params)
        .await
        .expect("upsert");

    let loaded = repo
        .get_by_assistant_id_for_user("system_default_user", "asst_1")
        .await
        .expect("get")
        .expect("row");
    assert_eq!(
        loaded.plan_mode_prompt_template.as_deref(),
        Some("Always emit a 4-step plan before coding.")
    );
}

#[tokio::test]
async fn update_plan_mode_prompt_template_writes_value() {
    let (_pool, repo) = fresh_repo().await;
    repo.upsert_for_user("system_default_user", &minimal_params("def_1", "asst_1", "agent_1"))
        .await
        .expect("upsert");

    repo.update_plan_mode_prompt_template_for_user(
        "system_default_user",
        "asst_1",
        Some("Prefer 3-step plans.".to_string()),
    )
    .await
    .expect("update");

    let loaded = repo
        .get_by_assistant_id_for_user("system_default_user", "asst_1")
        .await
        .expect("get")
        .expect("row");
    assert_eq!(
        loaded.plan_mode_prompt_template.as_deref(),
        Some("Prefer 3-step plans.")
    );
}

#[tokio::test]
async fn update_plan_mode_prompt_template_clears_to_none() {
    let (_pool, repo) = fresh_repo().await;
    let params = UpsertAssistantDefinitionParams {
        plan_mode_prompt_template: Some("Some prompt"),
        ..minimal_params("def_1", "asst_1", "agent_1")
    };
    repo.upsert_for_user("system_default_user", &params)
        .await
        .expect("upsert");

    repo.update_plan_mode_prompt_template_for_user("system_default_user", "asst_1", None)
        .await
        .expect("clear");

    let loaded: AssistantDefinitionRow = sqlx::query_as("SELECT * FROM assistant_definitions WHERE assistant_id = ?")
        .bind("asst_1")
        .fetch_one(&_pool)
        .await
        .expect("fetch");
    assert_eq!(loaded.plan_mode_prompt_template, None);
}
