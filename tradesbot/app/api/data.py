"""
REST API endpoints for Jobs, Quotes, and Invoices.
"""
from fastapi import APIRouter, Query
from sqlalchemy import text
from app.models.database import async_session
from app.utils.logger import get_logger

log = get_logger("api_data")
router = APIRouter(prefix="/api")


@router.get("/jobs")
async def list_jobs(status: str = None, limit: int = Query(20, le=100)):
    """List jobs with optional status filter."""
    async with async_session() as session:
        query = "SELECT id, description, status, scheduled_at, location, created_at FROM jobs"
        params = {}
        if status:
            query += " WHERE status = :status"
            params["status"] = status
        query += " ORDER BY created_at DESC LIMIT :limit"
        params["limit"] = limit
        result = await session.execute(text(query), params)
        rows = result.fetchall()
        return [{"id": str(r[0]), "description": r[1], "status": r[2],
                 "scheduled_at": str(r[3]) if r[3] else None, "location": r[4],
                 "created_at": str(r[5])} for r in rows]


@router.get("/quotes")
async def list_quotes(status: str = None, limit: int = Query(20, le=100)):
    """List quotes with optional status filter."""
    async with async_session() as session:
        query = "SELECT id, items, grand_total, status, valid_until, created_at FROM quotes"
        params = {}
        if status:
            query += " WHERE status = :status"
            params["status"] = status
        query += " ORDER BY created_at DESC LIMIT :limit"
        params["limit"] = limit
        result = await session.execute(text(query), params)
        rows = result.fetchall()
        return [{"id": str(r[0]), "items": r[1], "grand_total": float(r[2]) if r[2] else 0,
                 "status": r[3], "valid_until": str(r[4]) if r[4] else None,
                 "created_at": str(r[5])} for r in rows]


@router.get("/invoices")
async def list_invoices(status: str = None, limit: int = Query(20, le=100)):
    """List invoices with optional status filter."""
    async with async_session() as session:
        query = "SELECT id, invoice_number, grand_total, payment_status, created_at FROM invoices"
        params = {}
        if status:
            query += " WHERE payment_status = :status"
            params["status"] = status
        query += " ORDER BY created_at DESC LIMIT :limit"
        params["limit"] = limit
        result = await session.execute(text(query), params)
        rows = result.fetchall()
        return [{"id": str(r[0]), "invoice_number": r[1], "grand_total": float(r[2]) if r[2] else 0,
                 "payment_status": r[3], "created_at": str(r[4])} for r in rows]


@router.get("/conversations")
async def list_conversations(limit: int = Query(30, le=100)):
    """List recent conversations."""
    async with async_session() as session:
        result = await session.execute(
            text("SELECT id, phone_from, direction, message_type, LEFT(content, 100), created_at FROM conversations ORDER BY created_at DESC LIMIT :limit"),
            {"limit": limit},
        )
        rows = result.fetchall()
        return [{"id": str(r[0]), "phone_from": r[1], "direction": r[2],
                 "message_type": r[3], "content_preview": r[4],
                 "created_at": str(r[5])} for r in rows]
