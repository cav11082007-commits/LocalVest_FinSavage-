"""
Location Service API Endpoints (3-5km Geofencing)
"""

from fastapi import APIRouter
from app.store import store, haversine_km

router = APIRouter(prefix="/location", tags=["4. Location Service"])

@router.get("/nearby")
def get_nearby_projects(lat: float = 10.7769, lng: float = 106.7009, radius_km: float = 5.0):
    # Dynamic radius logic: start with requested radius, expand up to 10km if needed
    search_radiuses = [radius_km, 10.0] if radius_km < 10.0 else [radius_km]
    
    nearby = []
    final_radius = radius_km
    
    for r in search_radiuses:
        nearby = []
        # Step 1: Fast filtering using SQLite bounding box
        projects = store.get_projects_in_bounding_box(lat, lng, r)
        
        # Step 2: Precise filtering using Haversine
        for p in projects:
            dist = haversine_km(lat, lng, p["lat"], p["lng"])
            if dist <= r:
                p_copy = dict(p)
                p_copy["distanceKm"] = round(dist, 1)
                nearby.append(p_copy)
        
        # If we have some results (e.g., at least 1 project), stop expanding
        if len(nearby) > 0:
            final_radius = r
            break
            
        final_radius = r
            
    # Sort by distance
    nearby.sort(key=lambda x: x["distanceKm"])
    
    return {"center_lat": lat, "center_lng": lng, "radius_km": final_radius, "count": len(nearby), "projects": nearby}
