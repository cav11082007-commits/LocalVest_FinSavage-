"""
Location Service API Endpoints (3-5km Geofencing)
"""

from fastapi import APIRouter
from app.store import store, haversine_km

router = APIRouter(prefix="/location", tags=["4. Location Service"])

@router.get("/nearby")
def get_nearby_projects(lat: float = 10.7769, lng: float = 106.7009, radius_km: float = 5.0):
    nearby = []
    projects = store.get_projects()
    for p in projects:
        dist = haversine_km(lat, lng, p["lat"], p["lng"])
        if dist <= radius_km:
            p_copy = dict(p)
            p_copy["distanceKm"] = round(dist, 1)
            nearby.append(p_copy)
    return {"center_lat": lat, "center_lng": lng, "radius_km": radius_km, "count": len(nearby), "projects": nearby}
