use std::path::{Path, PathBuf};

use crate::error::NotebookError;

/// 在 workspace 的 `notes_dir` 下读写 Markdown 文件。
///
/// 写入采用原子方式：先写到 `<path>.tmp`，再 rename 到目标文件。
/// 这样即使进程在写入途中被中断也不会留下半截文件。
#[derive(Clone, Debug)]
pub struct MdFileStore {
    notes_dir: PathBuf,
}

impl MdFileStore {
    /// 用指定的 `notes_dir` 构造文件存储。调用方需自行保证目录存在。
    pub fn new(notes_dir: PathBuf) -> Self {
        Self { notes_dir }
    }

    /// 把相对路径 `file_path`（形如 `notes/<uuid>.md`）解析为绝对路径，
    /// 并拒绝包含 `..` 的逃逸路径。
    fn resolve(&self, file_path: &str) -> Result<PathBuf, NotebookError> {
        let joined = self.notes_dir.join(strip_notes_prefix(file_path));
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
    pub async fn write(&self, file_path: &str, content: &str) -> Result<(), NotebookError> {
        let abs = self.resolve(file_path)?;
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
    pub async fn read(&self, file_path: &str) -> Result<String, NotebookError> {
        let abs = self.resolve(file_path)?;
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
    pub async fn delete(&self, file_path: &str) -> Result<(), NotebookError> {
        let abs = self.resolve(file_path)?;
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

    /// 枚举 `notes_dir` 下所有 `.md` 文件，返回 `(文件名, 绝对路径, mtime_ms)` 三元组列表。
    ///
    /// 供同步层扫描磁盘笔记使用。
    pub async fn list_md_files(&self) -> Result<Vec<(String, PathBuf, i64)>, NotebookError> {
        let notes_dir = self.notes_dir.clone();
        let notes_dir_for_err = notes_dir.clone();
        let result = tokio::task::spawn_blocking(move || -> std::io::Result<Vec<(String, PathBuf, i64)>> {
            let mut out = Vec::new();
            walk_md(&notes_dir, &mut out)?;
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

/// 递归遍历 `dir`，把所有 `.md` 文件的 `(文件名, 绝对路径, mtime_ms)` 收集到 `out`。
fn walk_md(dir: &Path, out: &mut Vec<(String, PathBuf, i64)>) -> std::io::Result<()> {
    if !dir.is_dir() {
        return Ok(());
    }
    for entry in std::fs::read_dir(dir)? {
        let entry = entry?;
        let path = entry.path();
        if path.is_dir() {
            walk_md(&path, out)?;
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
                .file_name()
                .map(|n| n.to_string_lossy().into_owned())
                .unwrap_or_default();
            out.push((rel, abs, mtime));
        }
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    /// 生成临时目录下的 `notes/` 子目录路径，用于测试夹具。
    fn notes_dir() -> PathBuf {
        tempfile::tempdir().unwrap().path().join("notes")
    }

    /// 写入后再读应原样往返。
    #[tokio::test]
    async fn write_then_read_roundtrips() {
        let dir = notes_dir();
        std::fs::create_dir_all(&dir).unwrap();
        let store = MdFileStore::new(dir.clone());
        store.write("notes/abc.md", "hello").await.unwrap();
        let content = store.read("notes/abc.md").await.unwrap();
        assert_eq!(content, "hello");
    }

    /// 读取不存在的文件应返回 `FileNotFound`。
    #[tokio::test]
    async fn read_missing_file_returns_file_not_found() {
        let dir = notes_dir();
        std::fs::create_dir_all(&dir).unwrap();
        let store = MdFileStore::new(dir);
        let err = store.read("notes/missing.md").await.unwrap_err();
        assert!(matches!(err, NotebookError::FileNotFound(_)));
    }

    /// 删除不存在的文件应视为 noop，不报错。
    #[tokio::test]
    async fn delete_missing_file_is_noop() {
        let dir = notes_dir();
        std::fs::create_dir_all(&dir).unwrap();
        let store = MdFileStore::new(dir);
        store.delete("notes/missing.md").await.unwrap();
    }

    /// 写入到带子目录的路径时，应自动创建缺失的父目录。
    #[tokio::test]
    async fn write_creates_parent_dirs() {
        let dir = notes_dir();
        std::fs::create_dir_all(&dir).unwrap();
        let store = MdFileStore::new(dir.clone());
        store.write("notes/sub/nested/x.md", "x").await.unwrap();
        assert!(dir.join("sub").join("nested").join("x.md").is_file());
    }

    /// 含 `..` 的路径必须被拒绝（防止跳出 `notes_dir`）。
    #[tokio::test]
    async fn write_rejects_path_traversal() {
        let dir = notes_dir();
        std::fs::create_dir_all(&dir).unwrap();
        let store = MdFileStore::new(dir);
        let err = store.write("../escape.md", "x").await.unwrap_err();
        assert!(matches!(err, NotebookError::FileIo { .. }));
    }

    /// `list_md_files` 仅枚举 `.md`，忽略其他扩展名。
    #[tokio::test]
    async fn list_md_files_returns_only_md_files() {
        let dir = notes_dir();
        std::fs::create_dir_all(&dir).unwrap();
        let store = MdFileStore::new(dir.clone());
        store.write("notes/a.md", "x").await.unwrap();
        store.write("notes/b.md", "y").await.unwrap();
        std::fs::write(dir.join("c.txt"), "ignore me").unwrap();

        let files = store.list_md_files().await.unwrap();
        assert_eq!(files.len(), 2);
        assert!(files.iter().any(|(n, _, _)| n == "a.md"));
        assert!(files.iter().any(|(n, _, _)| n == "b.md"));
    }

    /// 重复写入应原子覆盖，且不应残留 `.tmp` 文件。
    #[tokio::test]
    async fn write_overwrites_existing_file_atomically() {
        let dir = notes_dir();
        std::fs::create_dir_all(&dir).unwrap();
        let store = MdFileStore::new(dir.clone());
        store.write("notes/a.md", "first").await.unwrap();
        store.write("notes/a.md", "second").await.unwrap();
        let content = store.read("notes/a.md").await.unwrap();
        assert_eq!(content, "second");
        assert!(!dir.join("a.md.tmp").exists());
    }

    /// 删除后再读应返回 `FileNotFound`。
    #[tokio::test]
    async fn delete_then_read_returns_file_not_found() {
        let dir = notes_dir();
        std::fs::create_dir_all(&dir).unwrap();
        let store = MdFileStore::new(dir);
        store.write("notes/a.md", "x").await.unwrap();
        store.delete("notes/a.md").await.unwrap();
        let err = store.read("notes/a.md").await.unwrap_err();
        assert!(matches!(err, NotebookError::FileNotFound(_)));
    }
}
