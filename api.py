"""
TreeWatch Melbourne — Backend API
Polls VicEmergency GeoJSON feed for fallen tree incidents.
Deploy to Railway: railway up
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
from datetime import datetime, timezone
import re

app = FastAPI(title="TreeWatch Melbourne API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict to your Netlify URL in production
    allow_methods=["GET"],
    allow_headers=["*"],
)

VIC_EMERGENCY_FEED = "https://data.emergency.vic.gov.au/Show?pageId=getIncidentJSON"

TREE_KEYWORDS = [
    "fallen tree", "tree down", "tree fallen",
    "tree on", "uprooted tree", "tree blocking",
    "branch down", "tree collapse"
]

HIGH_PRIORITY_KEYWORDS = ["powerline", "power line", "roof", "structure", "car", "vehicle", "school"]
MED_PRIORITY_KEYWORDS  = ["road", "blocking", "driveway", "footpath", "path"]


def is_tree_incident(props: dict) -> bool:
    text = " ".join([
        props.get("category1", ""),
        props.get("category2", ""),
        props.get("title", ""),
        props.get("description", ""),
    ]).lower()
    return any(kw in text for kw in TREE_KEYWORDS)


def score_priority(props: dict) -> str:
    text = str(props).lower()
    if any(kw in text for kw in HIGH_PRIORITY_KEYWORDS):
        return "high"
    if any(kw in text for kw in MED_PRIORITY_KEYWORDS):
        return "med"
    return "low"


def minutes_ago(iso_string: str) -> int:
    """Convert ISO timestamp to minutes since now."""
    try:
        if not iso_string:
            return 0
        # Handle various ISO formats from VicEmergency
        iso_clean = re.sub(r'\.\d+', '', iso_string).replace('Z', '+00:00')
        dt = datetime.fromisoformat(iso_clean)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        delta = datetime.now(timezone.utc) - dt
        return max(0, int(delta.total_seconds() / 60))
    except Exception:
        return 0


@app.get("/")
def root():
    return {"status": "ok", "service": "TreeWatch Melbourne API"}


@app.get("/incidents")
def get_incidents():
    """
    Fetch and return fallen tree incidents from VicEmergency.
    Falls back to empty list on error — frontend handles gracefully.
    """
    try:
        resp = requests.get(VIC_EMERGENCY_FEED, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return {"incidents": [], "error": str(e), "updated": datetime.now().isoformat()}

    results = []
    features = data.get("features", [])

    for feature in features:
        props = feature.get("properties", {})
        geometry = feature.get("geometry", {})

        if not is_tree_incident(props):
            continue

        coords = geometry.get("coordinates", [None, None])
        lng, lat = (coords[0], coords[1]) if len(coords) >= 2 else (None, None)

        suburb = (
            props.get("suburb") or
            props.get("location") or
            props.get("area") or
            "Melbourne"
        )

        results.append({
            "id":       props.get("id") or feature.get("id"),
            "suburb":   suburb,
            "desc":     props.get("title") or props.get("description", "Fallen tree incident"),
            "detail":   props.get("description", ""),
            "priority": score_priority(props),
            "type":     "ses",
            "lat":      lat,
            "lng":      lng,
            "ago":      minutes_ago(props.get("created") or props.get("updated", "")),
            "source_url": props.get("sourceUri", ""),
        })

    # Sort by priority then recency
    priority_order = {"high": 0, "med": 1, "low": 2}
    results.sort(key=lambda x: (priority_order.get(x["priority"], 3), x["ago"]))

    return {
        "incidents": results,
        "count":     len(results),
        "updated":   datetime.now(timezone.utc).isoformat(),
        "source":    "VicEmergency"
    }


@app.get("/health")
def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}
