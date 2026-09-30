from fastapi import APIRouter, Depends
from app.core.logging import get_module_logger
from app.core.auth import require_permission, User

logger = get_module_logger('problems')
router = APIRouter()


@router.get('/status')
async def get_status(user: User = Depends(require_permission('module.problems.view'))):
    logger.info('Status queried for module problems')
    return {
        'module': 'problems',
        'name': 'Problems',
        'status': 'skeleton',
        'version': '0.1.0'
    }
