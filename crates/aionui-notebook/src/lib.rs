#![warn(clippy::disallowed_types)]

//! Notebook storage: SQLite for metadata, MD files for note bodies.
//!
//! Notes are stored as plain Markdown files on disk under the workspace
//! `notes_dir`. SQLite holds only the metadata (title, notebook_id, tags,
//! summary, star, timestamps). The MD file IS the body — no embedded
//! metadata block.

pub mod error;
pub mod file_store;
pub mod routes;
pub mod service;
pub mod state;
pub mod sync;
pub mod workspace;

pub use routes::notebook_routes;
pub use state::NotebookRouterState;
