from fastapi import APIRouter, Depends
from app.core.logging import get_module_logger
from app.core.auth import require_permission, User

logger = get_module_logger('capacity')
router = APIRouter()


@router.get('/status')
async def get_status(user: User = Depends(require_permission('module.capacity.view'))):
    logger.info('Status queried for module capacity')
    return {
        'module': 'capacity',
        'name': 'Capacity Planning',
        'status': 'skeleton',
        'version': '0.1.0'
    }
