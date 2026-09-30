from fastapi import APIRouter, Depends
from app.core.logging import get_module_logger
from app.core.auth import require_permission, User

logger = get_module_logger('top_n')
router = APIRouter()


@router.get('/status')
async def get_status(user: User = Depends(require_permission('module.top_n.view'))):
    logger.info('Status queried for module top_n')
    return {
        'module': 'top_n',
        'name': 'Top N',
        'status': 'skeleton',
        'version': '0.1.0'
    }
