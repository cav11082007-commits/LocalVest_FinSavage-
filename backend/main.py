"""
LocalVest Backend — Enterprise Modular Python FastAPI Application
"""

import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.services.realtime import realtime_manager
from app.api import auth, campaigns, payments, location, ai_flag, admin, test_routes

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API hệ thống gọi vốn cộng đồng minh bạch LocalVest",
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for Frontend HTML/JS Client Integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. Register Modular REST API Routers (Higher priority routes)
app.include_router(auth.router, prefix=settings.API_PREFIX)
app.include_router(campaigns.router, prefix=settings.API_PREFIX)
app.include_router(payments.router, prefix=settings.API_PREFIX)
app.include_router(location.router, prefix=settings.API_PREFIX)
app.include_router(ai_flag.router, prefix=settings.API_PREFIX)
app.include_router(admin.router, prefix=settings.API_PREFIX)

# 2. WebSocket Endpoint for Realtime Live Feed
@app.websocket("/ws/live-feed")
async def websocket_live_feed(websocket: WebSocket):
    await realtime_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # Keep connection alive
    except WebSocketDisconnect:
        realtime_manager.disconnect(websocket)

@app.get("/api/health", tags=["Health Check"])
def root_health_check():
    return {
        "status": "online",
        "system": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "branch": "testv1",
        "docs": "/docs"
    }

# 3. Mount Frontend Static Files (Serving ALL HTML/CSS/JS files on port 8000)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

if os.path.exists(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")

if settings.ENV != "prod":
    app.include_router(test_routes.router, prefix=settings.API_PREFIX)