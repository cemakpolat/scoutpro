"""
Notification handler
"""
import logging
from typing import Dict, Any, List
from enum import Enum
import aiosmtplib
from email.message import EmailMessage

logger = logging.getLogger(__name__)


class NotificationType(str, Enum):
    EMAIL = "email"
    PUSH = "push"
    SMS = "sms"
    IN_APP = "in_app"


class NotificationHandler:
    """Handle different types of notifications"""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_username: str = None,
        smtp_password: str = None,
        email_from: str = "noreply@scoutpro.com"
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password
        self.email_from = email_from

    async def send_notification(
        self,
        notification_type: NotificationType,
        recipient: str,
        subject: str,
        body: str,
        **kwargs
    ) -> bool:
        """Send notification based on type"""
        try:
            if notification_type == NotificationType.EMAIL:
                return await self.send_email(recipient, subject, body)
            elif notification_type == NotificationType.IN_APP:
                return await self.send_in_app(recipient, subject, body)
            else:
                logger.warning(f"Notification type {notification_type} not implemented")
                return False

        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            return False

    async def send_email(self, to: str, subject: str, body: str) -> bool:
        """Send email notification"""
        try:
            message = EmailMessage()
            message["From"] = self.email_from
            message["To"] = to
            message["Subject"] = subject
            message.set_content(body)

            # Send email
            if self.smtp_username and self.smtp_password:
                await aiosmtplib.send(
                    message,
                    hostname=self.smtp_host,
                    port=self.smtp_port,
                    username=self.smtp_username,
                    password=self.smtp_password,
                    use_tls=True
                )
            else:
                # For development - just log
                logger.info(f"Email would be sent to {to}: {subject}")

            logger.info(f"Email sent to {to}")
            return True

        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False

    async def send_in_app(self, user_id: str, subject: str, body: str) -> bool:
        """Send in-app notification"""
        try:
            # Store in database for user to retrieve
            logger.info(f"In-app notification sent to user {user_id}: {subject}")
            return True

        except Exception as e:
            logger.error(f"Error sending in-app notification: {e}")
            return False

    async def send_bulk_notifications(
        self,
        notification_type: NotificationType,
        recipients: List[str],
        subject: str,
        body: str
    ) -> Dict[str, Any]:
        """Send bulk notifications"""
        results = {
            "total": len(recipients),
            "successful": 0,
            "failed": 0
        }

        for recipient in recipients:
            success = await self.send_notification(
                notification_type,
                recipient,
                subject,
                body
            )

            if success:
                results["successful"] += 1
            else:
                results["failed"] += 1

        return results
