from fastapi import APIRouter, Depends
from app.core.logging import get_module_logger
from app.core.auth import require_permission, User

logger = get_module_logger('trend_detection')
router = APIRouter()


@router.get('/status')
async def get_status(user: User = Depends(require_permission('module.trend_detection.view'))):
    logger.info('Status queried for module trend_detection')
    return {
        'module': 'trend_detection',
        'name': 'Trend Detection',
        'status': 'skeleton',
        'version': '0.1.0'
    }
