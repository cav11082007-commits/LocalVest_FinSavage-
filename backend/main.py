"""
LocalVest Backend — Enterprise Modular Python FastAPI Application
Architected by Senior Backend Architect for 0-Cost MVP Student Deployment.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.services.realtime import realtime_manager
from app.api import auth, campaigns, payments, location, ai_flag, admin

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API hệ thống gọi vốn cộng đồng minh bạch LocalVest (MVP Vòng 2)",
    version=settings.VERSION
)

# Enable CORS for Frontend HTML/JS Client Integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Modular API Routers (8 Core Services)
app.include_router(auth.router, prefix=settings.API_PREFIX)
app.include_router(campaigns.router, prefix=settings.API_PREFIX)
app.include_router(payments.router, prefix=settings.API_PREFIX)
app.include_router(location.router, prefix=settings.API_PREFIX)
app.include_router(ai_flag.router, prefix=settings.API_PREFIX)
app.include_router(admin.router, prefix=settings.API_PREFIX)

# WebSocket Endpoint for Realtime Live Feed
@app.websocket("/ws/live-feed")
async def websocket_live_feed(websocket: WebSocket):
    await realtime_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # Keep connection alive
    except WebSocketDisconnect:
        realtime_manager.disconnect(websocket)

@app.get("/", tags=["Health Check"])
def root_health_check():
    return {
        "status": "online",
        "system": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs"
    }
