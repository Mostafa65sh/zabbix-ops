from fastapi import APIRouter, Depends
from app.core.logging import get_module_logger
from app.core.auth import require_permission, User

logger = get_module_logger('graph_explorer')
router = APIRouter()


@router.get('/status')
async def get_status(user: User = Depends(require_permission('module.graph_explorer.view'))):
    logger.info('Status queried for module graph_explorer')
    return {
        'module': 'graph_explorer',
        'name': 'Graph Explorer',
        'status': 'skeleton',
        'version': '0.1.0'
    }
