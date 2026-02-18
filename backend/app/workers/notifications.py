"""Notification Celery task for alerts."""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional

from celery import shared_task
from sqlalchemy import select
from asgiref.sync import async_to_sync

from app.workers.celery_app import celery_app
from app.core.config import settings
from app.core.logging import get_logger
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.alert import Alert
from app.models.rule import Rule
from app.models.device import Device

logger = get_logger(__name__)


def get_alert_with_relations_sync(alert_id: int) -> dict:
    """Get alert with rule, device, and factory info."""
    async def _fetch():
        async with AsyncSessionLocal() as db:
            from sqlalchemy.orm import selectinload
            
            result = await db.execute(
                select(Alert)
                .options(selectinload(Alert.rule))
                .options(selectinload(Alert.device))
                .where(Alert.id == alert_id)
            )
            alert = result.scalar_one_or_none()
            
            if not alert:
                return None
            
            return {
                "id": alert.id,
                "factory_id": alert.factory_id,
                "rule_id": alert.rule_id,
                "device_id": alert.device_id,
                "triggered_at": alert.triggered_at,
                "severity": alert.severity,
                "message": alert.message,
                "telemetry_snapshot": alert.telemetry_snapshot,
                "rule_name": alert.rule.name if alert.rule else None,
                "device_name": alert.device.name if alert.device else None,
            }
    
    return async_to_sync(_fetch)()


def get_factory_users_sync(factory_id: int) -> list:
    """Get all active users for a factory."""
    async def _fetch():
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(User).where(
                    User.factory_id == factory_id,
                    User.is_active == True,
                )
            )
            users = result.scalars().all()
            return [
                {
                    "id": u.id,
                    "email": u.email,
                    "whatsapp_number": u.whatsapp_number,
                }
                for u in users
            ]
    
    return async_to_sync(_fetch)()


def mark_notification_sent_sync(alert_id: int) -> None:
    """Mark alert as notification sent."""
    async def _mark():
        async with AsyncSessionLocal() as db:
            from sqlalchemy import update
            await db.execute(
                update(Alert)
                .where(Alert.id == alert_id)
                .values(notification_sent=True)
            )
            await db.commit()
    
    async_to_sync(_mark)()


def send_email(to_email: str, alert: dict) -> None:
    """Send email notification."""
    if not settings.smtp_host:
        logger.debug("smtp.not_configured", email=to_email)
        return
    
    try:
        msg = MIMEMultipart()
        msg['From'] = settings.smtp_from
        msg['To'] = to_email
        msg['Subject'] = f"[{alert['severity'].upper()}] FactoryOps Alert - {alert['rule_name']}"
        
        body = f"""
FactoryOps Alert Notification

Rule: {alert['rule_name']}
Device: {alert['device_name'] or 'Unknown'}
Severity: {alert['severity'].upper()}
Time: {alert['triggered_at']}

{alert['message']}

Telemetry Snapshot:
{alert.get('telemetry_snapshot', {})}

---
This is an automated alert from FactoryOps AI Engineering.
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(settings.smtp_host, settings.smtp_port)
        server.starttls()
        if settings.smtp_user and settings.smtp_password:
            server.login(settings.smtp_user, settings.smtp_password)
        
        server.send_message(msg)
        server.quit()
        
        logger.info("email.sent", to=to_email, alert_id=alert['id'])
        
    except Exception as e:
        logger.error("email.failed", to=to_email, alert_id=alert['id'], error=str(e))
        raise


def send_whatsapp(to_number: str, alert: dict) -> None:
    """Send WhatsApp notification via Twilio."""
    if not settings.twilio_account_sid:
        logger.debug("twilio.not_configured", number=to_number)
        return
    
    try:
        from twilio.rest import Client
        
        client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
        
        message = f"""
FactoryOps Alert [{alert['severity'].upper()}]
Rule: {alert['rule_name']}
Device: {alert['device_name'] or 'Unknown'}
{alert['message']}
        """.strip()
        
        from_number = settings.twilio_whatsapp_from or f"whatsapp:{settings.twilio_whatsapp_from}"
        to_whatsapp = f"whatsapp:{to_number}"
        
        message = client.messages.create(
            body=message,
            from_=from_number,
            to=to_whatsapp,
        )
        
        logger.info("whatsapp.sent", to=to_number, alert_id=alert['id'], sid=message.sid)
        
    except Exception as e:
        logger.error("whatsapp.failed", to=to_number, alert_id=alert['id'], error=str(e))
        raise


@celery_app.task(
    name="send_notifications",
    bind=True,
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def send_notifications_task(
    self,
    alert_id: int,
    channels: dict,
):
    """
    Send notifications for an alert to all factory users.
    Skips gracefully if SMTP/Twilio not configured.
    """
    try:
        alert = get_alert_with_relations_sync(alert_id)
        if not alert:
            logger.error("alert.not_found", alert_id=alert_id)
            return
        
        users = get_factory_users_sync(alert["factory_id"])
        
        for user in users:
            # Send email
            if channels.get("email") and user.get("email"):
                try:
                    send_email(user["email"], alert)
                except Exception as e:
                    logger.error(
                        "notification.email_failed",
                        user_id=user["id"],
                        alert_id=alert_id,
                        error=str(e),
                    )
            
            # Send WhatsApp
            if channels.get("whatsapp") and user.get("whatsapp_number"):
                try:
                    send_whatsapp(user["whatsapp_number"], alert)
                except Exception as e:
                    logger.error(
                        "notification.whatsapp_failed",
                        user_id=user["id"],
                        alert_id=alert_id,
                        error=str(e),
                    )
        
        # Mark as sent
        mark_notification_sent_sync(alert_id)
        
        logger.info(
            "notifications.completed",
            alert_id=alert_id,
            user_count=len(users),
        )
        
    except Exception as exc:
        logger.error(
            "notifications.failed",
            alert_id=alert_id,
            error=str(exc),
        )
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
