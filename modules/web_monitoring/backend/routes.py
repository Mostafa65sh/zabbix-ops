from fastapi import APIRouter, Depends
from app.core.logging import get_module_logger
from app.core.auth import require_permission, User

logger = get_module_logger('web_monitoring')
router = APIRouter()


@router.get('/status')
async def get_status(user: User = Depends(require_permission('module.web_monitoring.view'))):
    logger.info('Status queried for module web_monitoring')
    return {
        'module': 'web_monitoring',
        'name': 'Web Monitoring',
        'status': 'skeleton',
        'version': '0.1.0'
    }
