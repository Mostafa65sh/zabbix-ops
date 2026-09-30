from fastapi import APIRouter, Depends
from app.core.logging import get_module_logger
from app.core.auth import require_permission, User

logger = get_module_logger('alert_analytics')
router = APIRouter()


@router.get('/status')
async def get_status(user: User = Depends(require_permission('module.alert_analytics.view'))):
    logger.info('Status queried for module alert_analytics')
    return {
        'module': 'alert_analytics',
        'name': 'Alert Analytics',
        'status': 'skeleton',
        'version': '0.1.0'
    }
