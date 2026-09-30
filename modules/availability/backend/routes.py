from fastapi import APIRouter, Depends
from app.core.logging import get_module_logger
from app.core.auth import require_permission, User

logger = get_module_logger('availability')
router = APIRouter()


@router.get('/status')
async def get_status(user: User = Depends(require_permission('module.availability.view'))):
    logger.info('Status queried for module availability')
    return {
        'module': 'availability',
        'name': 'Availability',
        'status': 'skeleton',
        'version': '0.1.0'
    }
