"""Notification Center API — in-app notifications for the review workflow."""

from fastapi import APIRouter
from app.services.notifications import notification_service

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("")
def list_notifications(recipient: str | None = None):
    """Return all notifications, optionally filtered by recipient."""
    return {
        "count": len(notification_service.get_pending_notifications(recipient)),
        "notifications": notification_service.get_pending_notifications(recipient),
    }
