"""FastAPI router for quiz curriculum topics and taxonomy."""

from fastapi import APIRouter

from quiz.contracts.taxonomy import TopicInfo, get_available_topics

router = APIRouter()


@router.get("/topics", response_model=list[TopicInfo])
def list_topics() -> list[TopicInfo]:
    """Returns curriculum hierarchy of math topics, subconcepts, and diagnostic misconceptions."""
    return get_available_topics()
