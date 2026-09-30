from fastapi import APIRouter, Depends
from app.core.logging import get_module_logger
from app.core.auth import require_permission, User

logger = get_module_logger('global_search')
router = APIRouter()


@router.get('/status')
async def get_status(user: User = Depends(require_permission('module.global_search.view'))):
    logger.info('Status queried for module global_search')
    return {
        'module': 'global_search',
        'name': 'Global Search',
        'status': 'skeleton',
        'version': '0.1.0'
    }
