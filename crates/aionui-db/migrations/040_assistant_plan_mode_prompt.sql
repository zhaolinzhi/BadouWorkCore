-- Allow assistant authors (including per-row overrides on built-in rows
-- such as the BadouCli agent) to override the default plan-mode system
-- prompt for the underlying aionrs CLI agent.
-- NULL = fall back to upstream aionrs default
--   (aionrs crates/aion-agent/src/plan/prompt.rs::plan_mode_instructions()).
ALTER TABLE assistant_definitions
    ADD COLUMN plan_mode_prompt_template TEXT;
