from fastapi import APIRouter, Depends
from app.core.logging import get_module_logger
from app.core.auth import require_permission, User

logger = get_module_logger('infra_map')
router = APIRouter()


@router.get('/status')
async def get_status(user: User = Depends(require_permission('module.infra_map.view'))):
    logger.info('Status queried for module infra_map')
    return {
        'module': 'infra_map',
        'name': 'Infrastructure Map',
        'status': 'skeleton',
        'version': '0.1.0'
    }
