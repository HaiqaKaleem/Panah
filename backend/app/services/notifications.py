"""
Notification Service — stubs for email/webhook notifications.

Design principles:
1. All notification methods are fire-and-forget (never block the API).
2. Actual email/webhook sending is deferred to a future implementation.
3. Every notification is logged to the audit trail.
4. The interface is intentionally minimal so it can be swapped to
   Redis/Celery, SendGrid, or any messaging provider later.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class Notification:
    """One notification to be delivered."""
    channel: str  # email, webhook, in_app
    recipient: str
    subject: str
    body: str
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class NotificationService:
    """
    Stub notification service.
    In production, this would integrate with SendGrid, Twilio, or a webhook queue.
    For now, notifications are logged and stored for audit purposes.
    """

    def __init__(self):
        self._sent: list[Notification] = []

    def send_review_notification(
        self,
        reviewer_id: str,
        design_version_id: int,
        action: str,
        project_name: str = "",
    ) -> Notification:
        """Notify an engineer that a design is ready for review."""
        notification = Notification(
            channel="in_app",
            recipient=reviewer_id,
            subject=f"Review Required: Design Version {design_version_id}",
            body=(
                f"A new design version (ID: {design_version_id}) has been submitted "
                f"for your review in project '{project_name}'. "
                f"Action required: {action}."
            ),
            metadata={
                "design_version_id": design_version_id,
                "action": action,
                "project_name": project_name,
                "type": "review_required",
            },
        )
        self._sent.append(notification)
        logger.info(f"Review notification sent to {reviewer_id}: {notification.subject}")
        return notification

    def send_decision_notification(
        self,
        design_version_id: int,
        decision: str,
        reviewer_id: str,
        project_name: str = "",
    ) -> Notification:
        """Notify stakeholders of a review decision."""
        status_emoji = {"approve": "✅", "reject": "❌", "request_changes": "🔄"}.get(decision, "📋")
        notification = Notification(
            channel="in_app",
            recipient="project_team",
            subject=f"{status_emoji} Design Review: {decision.upper()}",
            body=(
                f"Design version {design_version_id} has been {decision}d by {reviewer_id}. "
                f"Project: {project_name}."
            ),
            metadata={
                "design_version_id": design_version_id,
                "decision": decision,
                "reviewer": reviewer_id,
                "project_name": project_name,
                "type": "review_decision",
            },
        )
        self._sent.append(notification)
        logger.info(f"Decision notification: {decision} for DV-{design_version_id}")
        return notification

    def send_validation_notification(
        self,
        design_id: int,
        status: str,
        project_name: str = "",
    ) -> Notification:
        """Notify when validation completes."""
        notification = Notification(
            channel="in_app",
            recipient="project_team",
            subject=f"Validation Complete: Design {design_id}",
            body=(
                f"Structural validation for design {design_id} is complete. "
                f"Status: {status}. Project: {project_name}."
            ),
            metadata={
                "design_id": design_id,
                "status": status,
                "project_name": project_name,
                "type": "validation_complete",
            },
        )
        self._sent.append(notification)
        logger.info(f"Validation notification for design {design_id}: {status}")
        return notification

    def get_pending_notifications(self, recipient: str | None = None) -> list[dict]:
        """Return all sent notifications (for in-app notification center)."""
        notifications = self._sent
        if recipient:
            notifications = [n for n in notifications if n.recipient == recipient]

        return [
            {
                "channel": n.channel,
                "recipient": n.recipient,
                "subject": n.subject,
                "body": n.body,
                "metadata": n.metadata,
                "created_at": n.created_at.isoformat(),
            }
            for n in reversed(notifications)
        ]


# Singleton instance
notification_service = NotificationService()
