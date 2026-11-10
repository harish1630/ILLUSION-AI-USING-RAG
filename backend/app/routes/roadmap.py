"""Personalized roadmap endpoints."""

from fastapi import APIRouter, HTTPException, Query
from app.schemas.roadmap import RoadmapCreate, RoadmapResponse, RoadmapTaskUpdate
from app.db.repositories import RoadmapRepository

router = APIRouter(prefix="/roadmaps", tags=["Roadmaps"])


@router.post("", response_model=RoadmapResponse)
async def create_roadmap(data: RoadmapCreate, language: str = Query("en", description="Preferred language en/ta")):
    """Generates a personalized, step-by-step launch roadmap."""
    return RoadmapRepository.create_roadmap(data, language=language)


@router.get("/{roadmap_id}", response_model=RoadmapResponse)
async def get_roadmap(roadmap_id: str):
    """Retrieves roadmap and task checklist."""
    roadmap = RoadmapRepository.get_by_id(roadmap_id)
    if not roadmap:
        raise HTTPException(status_code=404, detail="Roadmap not found")
    return roadmap


@router.patch("/{roadmap_id}/tasks/{task_id}", response_model=RoadmapResponse)
async def update_task_status(roadmap_id: str, task_id: str, body: RoadmapTaskUpdate):
    """Updates a task status (pending, in_progress, completed) and recalculates progress."""
    updated = RoadmapRepository.update_task_status(roadmap_id, task_id, body.status)
    if not updated:
        raise HTTPException(status_code=404, detail="Roadmap or task not found")
    return updated

