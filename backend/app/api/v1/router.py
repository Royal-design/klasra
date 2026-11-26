from fastapi import APIRouter

from app.api.v1.academic import router as academic_router
from app.api.v1.auth import router as auth_router
from app.api.v1.health import router as health_router
from app.api.v1.imports import router as imports_router
from app.api.v1.memberships import router as memberships_router
from app.api.v1.registrations import router as registrations_router
from app.api.v1.schools import router as schools_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(schools_router)
api_router.include_router(memberships_router)
api_router.include_router(academic_router)
api_router.include_router(imports_router)
api_router.include_router(registrations_router)
