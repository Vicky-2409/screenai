from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import (
    admin,
    ai,
    analytics,
    auth,
    candidates,
    jobs,
    notifications,
    reports,
    resumes,
)

api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router)
api_router.include_router(jobs.router)
api_router.include_router(resumes.router)
api_router.include_router(candidates.router)
api_router.include_router(ai.router)
api_router.include_router(analytics.router)
api_router.include_router(notifications.router)
api_router.include_router(reports.router)
api_router.include_router(admin.router)
