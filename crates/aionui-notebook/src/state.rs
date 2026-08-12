use std::sync::Arc;

use crate::file_store::MdFileStore;
use crate::service::NotebookService;
use crate::workspace::WorkspaceConfig;

#[derive(Clone)]
pub struct NotebookRouterState {
    pub service: Arc<NotebookService>,
    pub workspace: Arc<WorkspaceConfig>,
    pub file_store: Arc<MdFileStore>,
}
