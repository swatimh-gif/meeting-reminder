import os
import logging
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from reminders.models import NotificationLog, Meeting

logger = logging.getLogger(__name__)


def is_whatsapp_configured():
    """Checks if WhatsApp Business / Twilio credentials are configured in environment."""
    twilio_sid = os.getenv('TWILIO_ACCOUNT_SID')
    twilio_token = os.getenv('TWILIO_AUTH_TOKEN')
    twilio_num = os.getenv('TWILIO_WHATSAPP_NUMBER')
    meta_token = os.getenv('WHATSAPP_API_TOKEN')
    return bool((twilio_sid and twilio_token and twilio_num) or meta_token)


def is_gmail_configured():
    """Checks if Gmail / SMTP credentials are configured in environment."""
    email_user = os.getenv('EMAIL_HOST_USER')
    email_pass = os.getenv('EMAIL_HOST_PASSWORD')
    return bool(email_user and email_pass)


def send_whatsapp_message(to_phone, message_text):
    """
    Sends WhatsApp message via Twilio or Meta WhatsApp Cloud API if configured.
    Returns (success: bool, status_message: str).
    """
    if not is_whatsapp_configured():
        return False, "NOT_CONFIGURED: Twilio/WhatsApp credentials not set in .env"

    try:
        # Twilio WhatsApp integration
        from twilio.rest import Client
        sid = os.getenv('TWILIO_ACCOUNT_SID')
        token = os.getenv('TWILIO_AUTH_TOKEN')
        from_num = os.getenv('TWILIO_WHATSAPP_NUMBER', 'whatsapp:+14155238886')
        
        # Format target phone
        target = to_phone if to_phone.startswith('whatsapp:') else f"whatsapp:{to_phone}"
        client = Client(sid, token)
        msg = client.messages.create(body=message_text, from_=from_num, to=target)
        return True, f"DELIVERED: Twilio SID {msg.sid}"
    except ImportError:
        # Twilio library not installed, but credentials exist
        logger.warning("Twilio library not installed. Install with `pip install twilio`")
        return False, "FAILED: twilio python library not installed"
    except Exception as e:
        logger.error(f"WhatsApp dispatch error: {e}")
        return False, f"FAILED: {str(e)}"


def send_gmail_message(to_email, subject, plain_body, html_body=None):
    """
    Sends Gmail / Email message via Django SMTP if configured.
    Returns (success: bool, status_message: str).
    """
    if not is_gmail_configured():
        return False, "NOT_CONFIGURED: Gmail SMTP credentials (EMAIL_HOST_USER, EMAIL_HOST_PASSWORD) not set in .env"

    try:
        from_email = os.getenv('DEFAULT_FROM_EMAIL', os.getenv('EMAIL_HOST_USER', 'noreply@meetcue.io'))
        send_mail(
            subject=subject,
            message=plain_body,
            from_email=from_email,
            recipient_list=[to_email],
            html_message=html_body,
            fail_silently=False,
        )
        return True, "DELIVERED: Sent via Gmail SMTP"
    except Exception as e:
        logger.error(f"Gmail dispatch error: {e}")
        return False, f"FAILED: {str(e)}"


def build_auth_links(meeting, token, base_url):
    """Constructs absolute URLs for Accept, Reject, and Reschedule."""
    clean_base = base_url.rstrip('/')
    return {
        'accept': f"{clean_base}/auth-action/{token}/accept/",
        'reject': f"{clean_base}/auth-action/{token}/reject/",
        'reschedule': f"{clean_base}/auth-action/{token}/reschedule/",
    }


def format_authorization_message(meeting, recipient_name, recipient_role, token, base_url, is_reschedule=False):
    """
    Constructs the required authorization payload containing:
    - Meeting purpose
    - Participant names (Host and Client)
    - Client name
    - Proposed meeting date & time
    - Action links: Accept, Reject, Reschedule
    """
    links = build_auth_links(meeting, token, base_url)
    target_time = meeting.rescheduled_date_time if is_reschedule and meeting.rescheduled_date_time else meeting.start_time
    date_str = target_time.strftime("%A, %b %d, %Y")
    time_str = target_time.strftime("%I:%M %p UTC")

    headline_prefix = "Revised Timing Confirmation" if is_reschedule else "Meeting Timing Authorization"
    
    # WhatsApp plain-text formatted message
    whatsapp_text = (
        f"👋 *MeetCue – {headline_prefix}*\n\n"
        f"Hello *{recipient_name}* ({recipient_role}),\n\n"
        f"A meeting requires your confirmation:\n"
        f"📌 *Purpose:* {meeting.purpose}\n"
        f"👤 *Client Name:* {meeting.client_name}\n"
        f"👥 *Host:* {meeting.p1_name} ({meeting.p1_role})\n"
        f"👥 *Client:* {meeting.p2_name} ({meeting.p2_role})\n"
        f"📅 *Proposed Date:* {date_str}\n"
        f"⏰ *Proposed Time:* {time_str} ({meeting.duration_minutes} mins)\n"
        f"📍 *Location:* {meeting.location}\n"
    )

    if is_reschedule and meeting.reschedule_reason:
        whatsapp_text += f"💬 *Reschedule Note:* \"{meeting.reschedule_reason}\" (by {meeting.rescheduled_by})\n"

    whatsapp_text += (
        f"\n👉 *Please select your response:*\n\n"
        f"1️⃣ *ACCEPT* (Approve proposed date & time):\n{links['accept']}\n\n"
        f"2️⃣ *REJECT* (Decline meeting):\n{links['reject']}\n\n"
        f"3️⃣ *RESCHEDULE* (Suggest different timing):\n{links['reschedule']}\n\n"
        f"_Note: Both participants must confirm before reminders are activated._"
    )

    # Gmail Subject & HTML message
    email_subject = f"MeetCue Authorization: {meeting.purpose} ({date_str} at {time_str})"
    email_html = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; max-width: 580px; margin: 0 auto; padding: 24px; border: 1px solid #e2e8f0; border-radius: 8px; background-color: #ffffff; color: #1e293b;">
        <div style="margin-bottom: 20px; border-bottom: 1px solid #f1f5f9; padding-bottom: 12px;">
            <span style="font-weight: 700; font-size: 18px; color: #0f172a;">Meet<span style="color: #4f46e5; font-weight: 600;">Cue</span></span>
            <span style="font-size: 12px; color: #64748b; margin-left: 8px;">{headline_prefix}</span>
        </div>
        <p style="font-size: 14px; margin-top: 0;">Hello <strong>{recipient_name}</strong>,</p>
        <p style="font-size: 13px; color: #475569;">Please review and authorize the proposed meeting schedule below. Both participants must confirm before reminders are scheduled.</p>
        
        <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 16px; margin: 20px 0; font-size: 13px;">
            <div style="margin-bottom: 8px;"><strong>Purpose:</strong> {meeting.purpose}</div>
            <div style="margin-bottom: 8px;"><strong>Client:</strong> {meeting.client_name}</div>
            <div style="margin-bottom: 8px;"><strong>Participants:</strong> {meeting.p1_name} (Host) &amp; {meeting.p2_name} (Client)</div>
            <div style="margin-bottom: 8px;"><strong>Proposed Date:</strong> {date_str}</div>
            <div style="margin-bottom: 8px;"><strong>Proposed Time:</strong> {time_str} ({meeting.duration_minutes} mins)</div>
            <div><strong>Location:</strong> {meeting.location}</div>
        </div>

        <div style="margin: 24px 0; text-align: center;">
            <a href="{links['accept']}" style="display: inline-block; background-color: #4f46e5; color: #ffffff; padding: 10px 20px; border-radius: 6px; text-decoration: none; font-size: 13px; font-weight: 600; margin-right: 8px;">Accept Meeting</a>
            <a href="{links['reschedule']}" style="display: inline-block; background-color: #ffffff; color: #4f46e5; border: 1px solid #cbd5e1; padding: 9px 18px; border-radius: 6px; text-decoration: none; font-size: 13px; font-weight: 600; margin-right: 8px;">Reschedule</a>
            <a href="{links['reject']}" style="display: inline-block; background-color: #ffffff; color: #b91c1c; border: 1px solid #fecaca; padding: 9px 18px; border-radius: 6px; text-decoration: none; font-size: 13px; font-weight: 600;">Reject</a>
        </div>

        <p style="font-size: 11px; color: #94a3b8; margin-top: 24px; border-top: 1px solid #f1f5f9; padding-top: 12px;">
            Automated delivery via MeetCue Meeting Authorization System.
        </p>
    </div>
    """

    return {
        'whatsapp_text': whatsapp_text,
        'email_subject': email_subject,
        'email_plain': whatsapp_text,
        'email_html': email_html
    }


def send_authorization_requests_to_both(meeting, base_url="http://127.0.0.1:8000"):
    """
    Dispatches authorization messages to BOTH participants via WhatsApp and Gmail.
    Records delivery or NOT_CONFIGURED audit logs.
    """
    targets = [
        ('Host', meeting.p1_name, meeting.p1_phone, meeting.p1_email, meeting.p1_token),
        ('Client', meeting.p2_name, meeting.p2_phone, meeting.p2_email, meeting.p2_token),
    ]

    is_reschedule = (meeting.overall_status == Meeting.OverallStatus.RESCHEDULE_REQUESTED)

    results = []
    for role, name, phone, email, token in targets:
        payload = format_authorization_message(meeting, name, role, token, base_url, is_reschedule=is_reschedule)

        # 1. WhatsApp Dispatch
        wa_success, wa_status = send_whatsapp_message(phone, payload['whatsapp_text'])
        wa_log_status = 'DELIVERED' if wa_success else ('NOT_CONFIGURED' if 'NOT_CONFIGURED' in wa_status else 'FAILED')
        NotificationLog.objects.create(
            meeting=meeting,
            channel="WHATSAPP",
            action_type=NotificationLog.ActionType.AUTH_REQUEST,
            recipient_name=name,
            recipient_role=role,
            recipient_contact=phone,
            subject_or_headline="WhatsApp Authorization Request",
            content_preview=payload['whatsapp_text'][:300] + "...",
            status=wa_log_status
        )
        results.append({'target': name, 'channel': 'WhatsApp', 'status': wa_log_status, 'detail': wa_status})

        # 2. Gmail Dispatch
        gm_success, gm_status = send_gmail_message(email, payload['email_subject'], payload['email_plain'], payload['email_html'])
        gm_log_status = 'DELIVERED' if gm_success else ('NOT_CONFIGURED' if 'NOT_CONFIGURED' in gm_status else 'FAILED')
        NotificationLog.objects.create(
            meeting=meeting,
            channel="EMAIL",
            action_type=NotificationLog.ActionType.AUTH_REQUEST,
            recipient_name=name,
            recipient_role=role,
            recipient_contact=email,
            subject_or_headline=payload['email_subject'],
            content_preview=payload['email_plain'][:300] + "...",
            status=gm_log_status
        )
        results.append({'target': name, 'channel': 'Gmail', 'status': gm_log_status, 'detail': gm_status})

    return results


def notify_other_participant(meeting, actor_role, actor_name, action, detail=""):
    """
    Notifies the other participant when one responds (Accept, Reject, or Reschedule).
    """
    if actor_role == 'Host':
        recipient_name = meeting.p2_name
        recipient_role = 'Client'
        recipient_phone = meeting.p2_phone
        recipient_email = meeting.p2_email
    else:
        recipient_name = meeting.p1_name
        recipient_role = 'Host'
        recipient_phone = meeting.p1_phone
        recipient_email = meeting.p1_email

    time_str = meeting.start_time.strftime("%A, %b %d, %Y at %I:%M %p UTC")

    if action == 'ACCEPTED':
        if meeting.is_confirmed:
            headline = f"Meeting Confirmed: Both participants accepted"
            body = (
                f"✅ *MeetCue Confirmation*\n\n"
                f"Great news {recipient_name}! Both participants have approved the meeting timing for:\n"
                f"📌 *\"{meeting.purpose}\"* on {time_str}.\n\n"
                f"WhatsApp and Gmail reminders are now officially active."
            )
        else:
            headline = f"Timing Update: {actor_name} accepted"
            body = (
                f"ℹ️ *MeetCue Update*\n\n"
                f"Hello {recipient_name},\n"
                f"{actor_name} ({actor_role}) has accepted the meeting *\"{meeting.purpose}\"* on {time_str}.\n"
                f"Awaiting your response before reminders can be scheduled."
            )
    elif action == 'REJECTED':
        headline = f"Meeting Cancelled: Declined by {actor_name}"
        body = (
            f"❌ *MeetCue Notice*\n\n"
            f"Hello {recipient_name},\n"
            f"{actor_name} ({actor_role}) has declined the meeting *\"{meeting.purpose}\"* on {time_str}.\n"
            f"This session has been marked as Rejected and all reminders are cancelled."
        )
    elif action == 'RESCHEDULE':
        new_time_str = meeting.rescheduled_date_time.strftime("%A, %b %d, %Y at %I:%M %p UTC") if meeting.rescheduled_date_time else "revised time"
        headline = f"Reschedule Requested by {actor_name}"
        body = (
            f"🗓 *MeetCue Reschedule Request*\n\n"
            f"Hello {recipient_name},\n"
            f"{actor_name} ({actor_role}) has suggested moving *\"{meeting.purpose}\"* to *{new_time_str}*.\n"
            f"Reason: {detail or 'Not specified'}\n\n"
            f"Revised authorization requests have been dispatched to both participants for confirmation."
        )
    else:
        headline = f"Meeting Notification"
        body = f"Update for {meeting.purpose} by {actor_name}."

    # Dispatch to other participant via WhatsApp & Gmail
    send_whatsapp_message(recipient_phone, body)
    NotificationLog.objects.create(
        meeting=meeting,
        channel="WHATSAPP",
        action_type=NotificationLog.ActionType.AUTH_RESPONSE,
        recipient_name=recipient_name,
        recipient_role=recipient_role,
        recipient_contact=recipient_phone,
        subject_or_headline=headline,
        content_preview=body,
        status="DELIVERED" if is_whatsapp_configured() else "NOT_CONFIGURED"
    )

    send_gmail_message(recipient_email, headline, body)
    NotificationLog.objects.create(
        meeting=meeting,
        channel="EMAIL",
        action_type=NotificationLog.ActionType.AUTH_RESPONSE,
        recipient_name=recipient_name,
        recipient_role=recipient_role,
        recipient_contact=recipient_email,
        subject_or_headline=headline,
        content_preview=body,
        status="DELIVERED" if is_gmail_configured() else "NOT_CONFIGURED"
    )
