from fastapi import APIRouter, Depends
from app.core.logging import get_module_logger
from app.core.auth import require_permission, User

logger = get_module_logger('reports')
router = APIRouter()


@router.get('/status')
async def get_status(user: User = Depends(require_permission('module.reports.view'))):
    logger.info('Status queried for module reports')
    return {
        'module': 'reports',
        'name': 'Reports',
        'status': 'skeleton',
        'version': '0.1.0'
    }
