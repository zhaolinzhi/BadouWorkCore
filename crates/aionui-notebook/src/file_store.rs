use std::path::{Path, PathBuf};

use crate::error::NotebookError;
use crate::workspace;

/// 在 workspace 的按账号隔离目录下读写 Markdown 文件。
///
/// 每个账号的正文文件放在 `<workspace_root>/users/<user_dir>/notes/` 下，
/// 账号之间互不可见。
///
/// 写入采用原子方式：先写到 `<path>.tmp`，再 rename 到目标文件。
/// 这样即使进程在写入途中被中断也不会留下半截文件。
#[derive(Clone, Debug)]
pub struct MdFileStore {
    workspace_root: PathBuf,
}

impl MdFileStore {
    /// 用指定的 workspace 根目录构造文件存储。
    ///
    /// 目录本身不需要预先存在：写入时会自动创建缺失的父目录。
    pub fn new(workspace_root: PathBuf) -> Self {
        Self { workspace_root }
    }

    /// 当前用户的 Markdown 文件目录。
    pub fn notes_dir_for(&self, user_id: &str) -> PathBuf {
        workspace::user_notes_dir(&self.workspace_root, user_id)
    }

    /// 把相对路径 `file_path`（形如 `notes/<uuid>.md`）解析为绝对路径，
    /// 并拒绝包含 `..` 的逃逸路径。
    fn resolve(&self, file_path: &str, user_id: &str) -> Result<PathBuf, NotebookError> {
        let joined = self.notes_dir_for(user_id).join(strip_notes_prefix(file_path));
        if joined
            .components()
            .any(|c| matches!(c, std::path::Component::ParentDir))
        {
            return Err(NotebookError::FileIo {
                path: file_path.into(),
                source: std::io::Error::new(std::io::ErrorKind::InvalidInput, "path contains '..'"),
            });
        }
        Ok(joined)
    }

    /// 把 `content` 写到 `file_path` 指向的文件，必要时自动创建父目录。
    pub async fn write(&self, file_path: &str, content: &str, user_id: &str) -> Result<(), NotebookError> {
        let abs = self.resolve(file_path, user_id)?;
        let tmp = abs.with_extension("md.tmp");
        let bytes = content.as_bytes().to_vec();
        let abs_clone = abs.clone();
        let tmp_clone = tmp.clone();

        tokio::task::spawn_blocking(move || -> std::io::Result<()> {
            if let Some(parent) = abs_clone.parent() {
                std::fs::create_dir_all(parent)?;
            }
            std::fs::write(&tmp_clone, &bytes)?;
            std::fs::rename(&tmp_clone, &abs_clone)?;
            Ok(())
        })
        .await
        .map_err(|e| NotebookError::FileIo {
            path: file_path.into(),
            source: std::io::Error::other(format!("join error: {e}")),
        })?
        .map_err(|e| NotebookError::FileIo {
            path: file_path.into(),
            source: e,
        })?;
        Ok(())
    }

    /// 读取 `file_path` 指向的 Markdown 文件内容。
    ///
    /// 文件不存在时返回 `NotebookError::FileNotFound`。
    pub async fn read(&self, file_path: &str, user_id: &str) -> Result<String, NotebookError> {
        let abs = self.resolve(file_path, user_id)?;
        let path_for_task = abs.clone();
        let result = tokio::task::spawn_blocking(move || std::fs::read_to_string(&path_for_task))
            .await
            .map_err(|e| NotebookError::FileIo {
                path: file_path.into(),
                source: std::io::Error::other(format!("join error: {e}")),
            })?;
        match result {
            Ok(s) => Ok(s),
            Err(e) if e.kind() == std::io::ErrorKind::NotFound => Err(NotebookError::FileNotFound(file_path.into())),
            Err(e) => Err(NotebookError::FileIo {
                path: file_path.into(),
                source: e,
            }),
        }
    }

    /// 删除 `file_path` 指向的文件；文件不存在时视为 noop，不返回错误。
    pub async fn delete(&self, file_path: &str, user_id: &str) -> Result<(), NotebookError> {
        let abs = self.resolve(file_path, user_id)?;
        let result = tokio::task::spawn_blocking(move || match std::fs::remove_file(&abs) {
            Ok(()) => Ok(()),
            Err(e) if e.kind() == std::io::ErrorKind::NotFound => Ok(()),
            Err(e) => Err(e),
        })
        .await
        .map_err(|e| NotebookError::FileIo {
            path: file_path.into(),
            source: std::io::Error::other(format!("join error: {e}")),
        })?;
        result.map_err(|e| NotebookError::FileIo {
            path: file_path.into(),
            source: e,
        })?;
        Ok(())
    }

    /// 枚举当前账号目录下所有 `.md` 文件，返回 `(文件名, 绝对路径, mtime_ms)` 三元组列表。
    ///
    /// 供同步层扫描磁盘笔记使用。
    pub async fn list_md_files(&self, user_id: &str) -> Result<Vec<(String, PathBuf, i64)>, NotebookError> {
        self.list_md_files_in_dir(&self.notes_dir_for(user_id)).await
    }

    /// 枚举指定目录下所有 `.md` 文件，返回 `(相对路径, 绝对路径, mtime_ms)` 三元组列表。
    ///
    /// 相对路径以 `/` 分隔，相对于 `dir` 本身（不含目录名）。
    /// 供同步层扫描旧版共享目录时使用。
    pub async fn list_md_files_in_dir(&self, dir: &Path) -> Result<Vec<(String, PathBuf, i64)>, NotebookError> {
        let notes_dir = dir.to_path_buf();
        let notes_dir_for_err = notes_dir.clone();
        let result = tokio::task::spawn_blocking(move || -> std::io::Result<Vec<(String, PathBuf, i64)>> {
            let mut out = Vec::new();
            walk_md(&notes_dir, &notes_dir, &mut out)?;
            Ok(out)
        })
        .await
        .map_err(|e| NotebookError::FileIo {
            path: notes_dir_for_err.display().to_string(),
            source: std::io::Error::other(format!("join error: {e}")),
        })?;
        result.map_err(|e| NotebookError::FileIo {
            path: notes_dir_for_err.display().to_string(),
            source: e,
        })
    }
}

/// 去掉路径前的 `notes` 前缀；不存在前缀则原样返回。
fn strip_notes_prefix(file_path: &str) -> PathBuf {
    let p = Path::new(file_path);
    if let Ok(rest) = p.strip_prefix("notes") {
        rest.to_path_buf()
    } else {
        p.to_path_buf()
    }
}

/// 递归遍历 `dir`，把所有 `.md` 文件的 `(相对路径, 绝对路径, mtime_ms)` 收集到 `out`。
///
/// 相对路径相对于 `root`（即 `dir` 本身），用 `/` 分隔。
fn walk_md(dir: &Path, root: &Path, out: &mut Vec<(String, PathBuf, i64)>) -> std::io::Result<()> {
    if !dir.is_dir() {
        return Ok(());
    }
    for entry in std::fs::read_dir(dir)? {
        let entry = entry?;
        let path = entry.path();
        if path.is_dir() {
            walk_md(&path, root, out)?;
        } else if path.extension().and_then(|s| s.to_str()) == Some("md") {
            let abs = path.clone();
            let mtime = entry
                .metadata()
                .and_then(|m| m.modified())
                .ok()
                .and_then(|t| t.duration_since(std::time::UNIX_EPOCH).ok())
                .map(|d| d.as_millis() as i64)
                .unwrap_or(0);
            let rel = path
                .strip_prefix(root)
                .unwrap_or(&path)
                .components()
                .map(|c| c.as_os_str().to_string_lossy().into_owned())
                .collect::<Vec<_>>()
                .join("/");
            out.push((rel, abs, mtime));
        }
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    /// 测试使用的账号 ID。
    const TEST_USER: &str = "user_alice";

    /// 构造测试夹具：返回 `(存储, workspace 根目录)`。
    fn store_fixture() -> (MdFileStore, tempfile::TempDir) {
        let tmp = tempfile::tempdir().unwrap();
        (MdFileStore::new(tmp.path().to_path_buf()), tmp)
    }

    /// 写入后再读应原样往返。
    #[tokio::test]
    async fn write_then_read_roundtrips() {
        let (store, _tmp) = store_fixture();
        store.write("notes/abc.md", "hello", TEST_USER).await.unwrap();
        let content = store.read("notes/abc.md", TEST_USER).await.unwrap();
        assert_eq!(content, "hello");
    }

    /// 读取不存在的文件应返回 `FileNotFound`。
    #[tokio::test]
    async fn read_missing_file_returns_file_not_found() {
        let (store, _tmp) = store_fixture();
        let err = store.read("notes/missing.md", TEST_USER).await.unwrap_err();
        assert!(matches!(err, NotebookError::FileNotFound(_)));
    }

    /// 删除不存在的文件应视为 noop，不报错。
    #[tokio::test]
    async fn delete_missing_file_is_noop() {
        let (store, _tmp) = store_fixture();
        store.delete("notes/missing.md", TEST_USER).await.unwrap();
    }

    /// 写入到带子目录的路径时，应自动创建缺失的父目录。
    #[tokio::test]
    async fn write_creates_parent_dirs() {
        let (store, _tmp) = store_fixture();
        store.write("notes/sub/nested/x.md", "x", TEST_USER).await.unwrap();
        let dir = store.notes_dir_for(TEST_USER);
        assert!(dir.join("sub").join("nested").join("x.md").is_file());
    }

    /// 含 `..` 的路径必须被拒绝（防止跳出账号目录）。
    #[tokio::test]
    async fn write_rejects_path_traversal() {
        let (store, _tmp) = store_fixture();
        let err = store.write("../escape.md", "x", TEST_USER).await.unwrap_err();
        assert!(matches!(err, NotebookError::FileIo { .. }));
    }

    /// `list_md_files` 仅枚举 `.md`，忽略其他扩展名。
    #[tokio::test]
    async fn list_md_files_returns_only_md_files() {
        let (store, _tmp) = store_fixture();
        store.write("notes/a.md", "x", TEST_USER).await.unwrap();
        store.write("notes/b.md", "y", TEST_USER).await.unwrap();
        let dir = store.notes_dir_for(TEST_USER);
        std::fs::create_dir_all(&dir).unwrap();
        std::fs::write(dir.join("c.txt"), "ignore me").unwrap();

        let files = store.list_md_files(TEST_USER).await.unwrap();
        assert_eq!(files.len(), 2);
        assert!(files.iter().any(|(n, _, _)| n == "a.md"));
        assert!(files.iter().any(|(n, _, _)| n == "b.md"));
    }

    /// 重复写入应原子覆盖，且不应残留 `.tmp` 文件。
    #[tokio::test]
    async fn write_overwrites_existing_file_atomically() {
        let (store, _tmp) = store_fixture();
        store.write("notes/a.md", "first", TEST_USER).await.unwrap();
        store.write("notes/a.md", "second", TEST_USER).await.unwrap();
        let content = store.read("notes/a.md", TEST_USER).await.unwrap();
        assert_eq!(content, "second");
        assert!(!store.notes_dir_for(TEST_USER).join("a.md.tmp").exists());
    }

    /// 删除后再读应返回 `FileNotFound`。
    #[tokio::test]
    async fn delete_then_read_returns_file_not_found() {
        let (store, _tmp) = store_fixture();
        store.write("notes/a.md", "x", TEST_USER).await.unwrap();
        store.delete("notes/a.md", TEST_USER).await.unwrap();
        let err = store.read("notes/a.md", TEST_USER).await.unwrap_err();
        assert!(matches!(err, NotebookError::FileNotFound(_)));
    }

    /// 不同账号的正文文件必须落在不同目录里。
    #[tokio::test]
    async fn writes_of_two_users_are_separated() {
        let (store, tmp) = store_fixture();
        store.write("notes/a.md", "alice", "user_alice").await.unwrap();
        store.write("notes/a.md", "bob", "user_bob").await.unwrap();

        let alice_dir = store.notes_dir_for("user_alice");
        let bob_dir = store.notes_dir_for("user_bob");
        assert_ne!(alice_dir, bob_dir);
        assert_eq!(std::fs::read_to_string(alice_dir.join("a.md")).unwrap(), "alice");
        assert_eq!(std::fs::read_to_string(bob_dir.join("a.md")).unwrap(), "bob");
        // 共享的 notes/ 目录下不应留下正文文件。
        assert!(!tmp.path().join("notes").join("a.md").exists());
    }

    /// `list_md_files` 只返回当前账号目录下的文件。
    #[tokio::test]
    async fn list_md_files_is_scoped_to_the_user() {
        let (store, _tmp) = store_fixture();
        store.write("notes/a.md", "x", "user_alice").await.unwrap();
        store.write("notes/b.md", "y", "user_bob").await.unwrap();

        let alice_files = store.list_md_files("user_alice").await.unwrap();
        assert_eq!(alice_files.len(), 1);
        assert_eq!(alice_files[0].0, "a.md");
    }
}
