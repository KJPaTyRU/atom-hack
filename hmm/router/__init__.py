from fastapi import APIRouter

from hmm.config import get_settings
from .main import get_router
from .auth import get_router as auth_router
from .expedition import get_router as expedition_router
from .hero import get_router as hero_router
from .tasks import get_router as tasks_router

__all__ = ["router"]

router = APIRouter(prefix=get_settings().api.cdn_prefix)

router.include_router(get_router())
router.include_router(tasks_router())
router.include_router(hero_router())
router.include_router(expedition_router())
router.include_router(auth_router())
