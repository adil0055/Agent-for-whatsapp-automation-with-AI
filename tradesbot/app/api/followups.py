"""
Follow-up management API endpoints.
"""
from fastapi import APIRouter
from sqlalchemy import text
from app.models.database import async_session
from app.services.followup_scheduler import check_and_send_reminders, cancel_follow_up
from app.utils.logger import get_logger

log = get_logger("api_followups")
router = APIRouter(prefix="/api")


@router.get("/followups")
async def list_follow_ups(status: str = "pending"):
    """List follow-ups by status."""
    async with async_session() as session:
        result = await session.execute(
            text("""
                SELECT f.id, f.reference_type, f.reference_id, f.status,
                       f.reminder_count, f.max_reminders, f.next_reminder_at, f.created_at
                FROM follow_ups f
                WHERE f.status = :status
                ORDER BY f.next_reminder_at ASC
                LIMIT 50
            """),
            {"status": status},
        )
        rows = result.fetchall()
        return [
            {
                "id": str(r[0]), "reference_type": r[1],
                "reference_id": str(r[2]), "status": r[3],
                "reminder_count": r[4], "max_reminders": r[5],
                "next_reminder_at": str(r[6]) if r[6] else None,
                "created_at": str(r[7]),
            } for r in rows
        ]


@router.post("/followups/trigger")
async def trigger_reminders():
    """Manually trigger a follow-up check."""
    count = await check_and_send_reminders()
    return {"status": "ok", "reminders_sent": count}


@router.post("/followups/{reference_type}/{reference_id}/cancel")
async def cancel(reference_type: str, reference_id: str):
    """Cancel follow-ups for a reference (when customer responds)."""
    await cancel_follow_up(reference_type, reference_id)
    return {"status": "cancelled"}
