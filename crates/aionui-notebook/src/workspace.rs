use std::path::{Path, PathBuf};

use crate::error::NotebookError;

const NOTES_SUBDIR: &str = "notes";
const ASSETS_SUBDIR: &str = "assets";
const BACKUP_SUBDIR: &str = "backup";
const INDEX_DB: &str = ".index.db";

/// Resolved absolute paths for the notebook workspace.
#[derive(Debug, Clone)]
pub struct WorkspaceConfig {
    pub root: PathBuf,
    pub notes_dir: PathBuf,
    pub assets_dir: PathBuf,
    pub backup_dir: PathBuf,
    pub index_db: PathBuf,
}

impl WorkspaceConfig {
    /// 解析默认工作区，与 `/api/system/info` 中使用的系统 `work_dir` 对齐，
    /// 让笔记本模块与系统其他模块共用同一份用户内容落盘位置。
    ///
    /// 解析顺序：
    /// 1. `AIONUI_WORK_DIR` 环境变量（由 bootstrap 层从 `--work-dir` / 显式 env / `data_dir` 设置）。
    /// 2. `dirs::data_dir()/aionui`（OS 用户数据目录）。
    /// 3. `$HOME/.aionui`（旧版兜底路径）。
    ///
    /// 解析后会在根目录下创建 `notes/`、`assets/`、`backup/` 子目录。
    pub fn resolve_default() -> Result<Self, NotebookError> {
        let root = if let Some(work_dir) = std::env::var_os("AIONUI_WORK_DIR") {
            let path = PathBuf::from(work_dir);
            if path.as_os_str().is_empty() {
                Self::default_root_from_data_dir()?
            } else {
                path
            }
        } else {
            Self::default_root_from_data_dir()?
        };
        Self::resolve(&root)
    }

    /// 当未设置 `AIONUI_WORK_DIR` 时，备用的根目录解析逻辑：
    /// 优先 `dirs::data_dir()/aionui`，否则回退到 `$HOME/.aionui`。
    fn default_root_from_data_dir() -> Result<PathBuf, NotebookError> {
        if let Some(data_dir) = dirs::data_dir() {
            Ok(data_dir.join("aionui"))
        } else {
            let home = std::env::var_os("HOME")
                .or_else(|| std::env::var_os("USERPROFILE"))
                .ok_or_else(|| {
                    NotebookError::WorkspaceInit(
                        "could not resolve a workspace directory (no AIONUI_WORK_DIR, \
                         no dirs::data_dir, no HOME/USERPROFILE)"
                            .into(),
                    )
                })?;
            Ok(PathBuf::from(home).join(".aionui"))
        }
    }

    /// 在指定的根目录下解析工作区，并确保 `notes/`、`assets/`、`backup/` 子目录存在。
    pub fn resolve(root: &Path) -> Result<Self, NotebookError> {
        let root = root.to_path_buf();
        let notes_dir = root.join(NOTES_SUBDIR);
        let assets_dir = root.join(ASSETS_SUBDIR);
        let backup_dir = root.join(BACKUP_SUBDIR);
        let index_db = root.join(INDEX_DB);

        for dir in [&root, &notes_dir, &assets_dir, &backup_dir] {
            std::fs::create_dir_all(dir)
                .map_err(|e| NotebookError::WorkspaceInit(format!("failed to create {}: {e}", dir.display())))?;
        }

        Ok(Self {
            root,
            notes_dir,
            assets_dir,
            backup_dir,
            index_db,
        })
    }

    /// 把绝对路径转为相对工作区的路径（用作笔记的 `file_path`）。
    ///
    /// 若路径不在 `notes_dir` 下则返回 `None`。返回值会保留 `notes/` 前缀
    /// （例如 `notes/<uuid>.md`），以便与 `to_absolute` 互相往返。
    pub fn to_relative(&self, abs: &Path) -> Option<String> {
        let rel = abs.strip_prefix(&self.root).ok()?;
        // Verify it's actually under notes_dir (not e.g. under assets/).
        if !abs.starts_with(&self.notes_dir) {
            return None;
        }
        Some(rel.to_string_lossy().into_owned())
    }

    /// 把存储的相对 `file_path` 解析回磁盘上的绝对路径。
    pub fn to_absolute(&self, file_path: &str) -> PathBuf {
        self.root.join(file_path)
    }
}

/// 生成基于 UUID v4 的 Markdown 文件名。
///
/// 格式：`<32 个十六进制字符>.md`（小写、无连字符的 UUID v4）。
pub fn generate_md_filename() -> String {
    let id = uuid::Uuid::new_v4().simple().to_string();
    format!("{id}.md")
}

#[cfg(test)]
mod tests {
    use super::*;

    /// `resolve` 应创建根目录与全部子目录。
    #[test]
    fn resolve_creates_all_subdirectories() {
        let tmp = tempfile::tempdir().unwrap();
        let root = tmp.path().join("ws");
        let cfg = WorkspaceConfig::resolve(&root).unwrap();
        assert!(cfg.root.is_dir());
        assert!(cfg.notes_dir.is_dir());
        assert!(cfg.assets_dir.is_dir());
        assert!(cfg.backup_dir.is_dir());
        assert_eq!(cfg.index_db, root.join(".index.db"));
    }

    /// 重复 `resolve` 应保持幂等。
    #[test]
    fn resolve_is_idempotent() {
        let tmp = tempfile::tempdir().unwrap();
        let root = tmp.path().join("ws");
        let _ = WorkspaceConfig::resolve(&root).unwrap();
        let cfg2 = WorkspaceConfig::resolve(&root).unwrap();
        assert_eq!(cfg2.notes_dir, root.join("notes"));
    }

    /// `to_relative` 与 `to_absolute` 应能正确互相往返。
    #[test]
    fn to_relative_and_back_roundtrip() {
        let tmp = tempfile::tempdir().unwrap();
        let cfg = WorkspaceConfig::resolve(tmp.path()).unwrap();
        let abs = cfg.notes_dir.join("abc.md");
        let rel = cfg.to_relative(&abs).unwrap();
        assert_eq!(rel, "notes/abc.md");
        let back = cfg.to_absolute(&rel);
        assert_eq!(back, abs);
    }

    /// `to_relative` 对 `notes_dir` 之外的路径应返回 `None`。
    #[test]
    fn to_relative_rejects_paths_outside_notes_dir() {
        let tmp = tempfile::tempdir().unwrap();
        let cfg = WorkspaceConfig::resolve(tmp.path()).unwrap();
        let outside = tmp.path().join("elsewhere").join("x.md");
        assert!(cfg.to_relative(&outside).is_none());
    }

    /// `generate_md_filename` 应生成 32 字符小写十六进制 + `.md` 后缀。
    #[test]
    fn generate_md_filename_has_correct_shape() {
        let f = generate_md_filename();
        assert!(f.ends_with(".md"));
        let stem = &f[..f.len() - 3];
        assert_eq!(stem.len(), 32);
        assert!(stem.chars().all(|c| c.is_ascii_hexdigit() && !c.is_ascii_uppercase()));
    }

    /// `resolve_default` 应识别 `AIONUI_WORK_DIR` 环境变量。
    #[test]
    fn resolve_default_honors_aionui_work_dir_env() {
        let tmp = tempfile::tempdir().unwrap();
        // SAFETY: tests are single-threaded wrt env mutation at this layer;
        // concurrent tests should not be reading AIONUI_WORK_DIR.
        unsafe { std::env::set_var("AIONUI_WORK_DIR", tmp.path()) };
        let cfg = WorkspaceConfig::resolve_default().unwrap();
        unsafe { std::env::remove_var("AIONUI_WORK_DIR") };

        assert_eq!(cfg.root, tmp.path());
        assert!(cfg.notes_dir.is_dir());
        assert!(cfg.assets_dir.is_dir());
        assert!(cfg.backup_dir.is_dir());
    }

    /// 未设置 `AIONUI_WORK_DIR` 时，`resolve_default` 仍应能解析到 `dirs::data_dir` 或 `$HOME`。
    #[test]
    fn resolve_default_falls_back_when_env_unset() {
        // Ensure env var is not set.
        unsafe { std::env::remove_var("AIONUI_WORK_DIR") };
        let cfg = WorkspaceConfig::resolve_default().expect("resolve_default must succeed");
        // Root should be either dirs::data_dir()/aionui or $HOME/.aionui.
        // The exact path depends on the host; we only assert it exists.
        assert!(cfg.root.is_dir());
        assert!(cfg.notes_dir.is_dir());
    }
}
