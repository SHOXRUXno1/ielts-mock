"""Per-task Writing feedback endpoint — calls Gemini immediately and returns feedback."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.deps import Actor, get_current_actor
from app.services.llm import evaluate_writing

router = APIRouter(
    prefix="/admin",
    tags=["Feedback"],
)


class WritingFeedbackRequest(BaseModel):
    task: int = Field(..., ge=1, le=2, description="1 or 2")
    prompt: str
    text: str
    image_url: str | None = None


class CriterionResult(BaseModel):
    band: float
    feedback: str


class WritingFeedbackResponse(BaseModel):
    overall_band: float
    task_achievement: CriterionResult | None = None
    coherence_cohesion: CriterionResult | None = None
    lexical_resource: CriterionResult | None = None
    grammatical_range: CriterionResult | None = None
    strengths: list[str] = []
    improvements: list[str] = []
    errors: list[dict] = []
    word_count: int


@router.post(
    "/feedback/writing",
    response_model=WritingFeedbackResponse,
    status_code=status.HTTP_200_OK,
)
async def writing_feedback(
    payload: WritingFeedbackRequest,
    _actor: Actor = Depends(get_current_actor),
):
    if not payload.text.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Text must not be empty",
        )

    task_key = f"task_{payload.task}"
    images = {task_key: payload.image_url} if payload.image_url else {}

    try:
        result = await evaluate_writing(
            answers={task_key: payload.text},
            prompts={task_key: payload.prompt},
            images=images or None,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI evaluation failed: {exc}",
        ) from exc

    # evaluate_writing returns {"tasks": {"task_1": {...}}, "overall_band": X}
    tasks = result.get("tasks", {})
    task_data = tasks.get(task_key, {})

    def _criterion(key: str) -> CriterionResult | None:
        val = task_data.get(key)
        if isinstance(val, dict):
            return CriterionResult(
                band=float(val.get("band", 0)),
                feedback=str(val.get("feedback", "")),
            )
        return None

    return WritingFeedbackResponse(
        overall_band=float(task_data.get("overall_band", result.get("overall_band", 0))),
        task_achievement=_criterion("task_achievement"),
        coherence_cohesion=_criterion("coherence_cohesion"),
        lexical_resource=_criterion("lexical_resource"),
        grammatical_range=_criterion("grammatical_range"),
        strengths=list(task_data.get("strengths", [])),
        improvements=list(task_data.get("improvements", [])),
        errors=list(task_data.get("errors", [])),
        word_count=int(task_data.get("word_count", 0)),
    )
