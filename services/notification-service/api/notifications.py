"""
Notification API Endpoints
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from typing import List
import sys
sys.path.append('/app')
from shared.models.base import APIResponse
from notifications.notifier import NotificationHandler, NotificationType
from config.settings import get_settings

router = APIRouter(prefix="/api/v2/notifications", tags=["notifications"])

# Initialize notification handler
settings = get_settings()
notifier = NotificationHandler(
    smtp_host=settings.smtp_host,
    smtp_port=settings.smtp_port,
    smtp_username=settings.smtp_username,
    smtp_password=settings.smtp_password,
    email_from=settings.email_from
)


class NotificationRequest(BaseModel):
    notification_type: NotificationType
    recipient: str
    subject: str
    body: str


class BulkNotificationRequest(BaseModel):
    notification_type: NotificationType
    recipients: List[str]
    subject: str
    body: str


@router.post("/send", response_model=APIResponse)
async def send_notification(request: NotificationRequest):
    """Send a single notification"""
    try:
        success = await notifier.send_notification(
            request.notification_type,
            request.recipient,
            request.subject,
            request.body
        )

        if not success:
            raise HTTPException(status_code=500, detail="Failed to send notification")

        return APIResponse(
            success=True,
            message="Notification sent successfully"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send/bulk", response_model=APIResponse)
async def send_bulk_notifications(request: BulkNotificationRequest):
    """Send bulk notifications"""
    try:
        results = await notifier.send_bulk_notifications(
            request.notification_type,
            request.recipients,
            request.subject,
            request.body
        )

        return APIResponse(
            success=True,
            data=results,
            message=f"Sent {results['successful']} notifications"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send/email", response_model=APIResponse)
async def send_email(
    to: EmailStr,
    subject: str,
    body: str
):
    """Send email notification"""
    try:
        success = await notifier.send_email(to, subject, body)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to send email")

        return APIResponse(
            success=True,
            message=f"Email sent to {to}"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
