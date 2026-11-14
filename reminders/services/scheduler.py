"""
MeetCue Reminder Engine & Dual-Participant Timing Authorization
Enforces authorization rules:
- BOTH participants must accept before overall_status becomes CONFIRMED.
- Reminders trigger ONLY through WhatsApp and Gmail.
- Google Calendar and SMS are completely removed.
- If either participant rejects: overall_status = REJECTED, cancel all reminders.
- If either requests reschedule: overall_status = RESCHEDULE_REQUESTED, hold reminders.
"""
from django.utils import timezone
from datetime import timedelta
import logging

from reminders.services.notification_service import (
    send_whatsapp_message,
    send_gmail_message,
    is_whatsapp_configured,
    is_gmail_configured,
    notify_other_participant,
)

logger = logging.getLogger(__name__)


def process_participant_decision(meeting, token, action, reason="", new_datetime=None, base_url="http://127.0.0.1:8000"):
    """
    Handles a participant's response via their unique link (Accept, Reject, Reschedule).
    Prevents duplicate actions, updates individual responses and overall status,
    notifies the other participant, and manages reminder activation/cancellation.
    
    Returns (success: bool, user_message: str, meeting: Meeting, actor_role: str)
    """
    from reminders.models import Meeting, ScheduledReminder, NotificationLog
    from reminders.services.notification_service import send_authorization_requests_to_both

    # 1. Identify which participant is responding
    if token == meeting.p1_token:
        actor_role = "Host"
        actor_name = meeting.p1_name
        current_status = meeting.p1_auth_status
    elif token == meeting.p2_token:
        actor_role = "Client"
        actor_name = meeting.p2_name
        current_status = meeting.p2_auth_status
    else:
        return False, "Invalid or expired authorization link.", meeting, "Unknown"

    action = action.upper()
    now = timezone.now()

    # 2. Check for duplicate response
    if action == 'ACCEPT' and current_status == Meeting.ParticipantAuth.ACCEPTED:
        return True, f"You ({actor_name}) have already accepted this meeting.", meeting, actor_role
    if action == 'REJECT' and current_status == Meeting.ParticipantAuth.REJECTED:
        return True, f"You ({actor_name}) have already rejected this meeting.", meeting, actor_role

    # 3. Process the chosen action
    if action == 'ACCEPT':
        if actor_role == "Host":
            meeting.p1_auth_status = Meeting.ParticipantAuth.ACCEPTED
            meeting.p1_auth_updated_at = now
        else:
            meeting.p2_auth_status = Meeting.ParticipantAuth.ACCEPTED
            meeting.p2_auth_updated_at = now

        # Check if both have accepted
        other_status = meeting.p2_auth_status if actor_role == "Host" else meeting.p1_auth_status
        if other_status == Meeting.ParticipantAuth.ACCEPTED:
            meeting.overall_status = Meeting.OverallStatus.CONFIRMED
            meeting.authorization_updated_at = now
            meeting.authorization_note = f"Fully confirmed: Both {meeting.p1_name} (Host) and {meeting.p2_name} (Client) accepted."
            meeting.save()

            # Automatically activate WhatsApp and Gmail reminders
            sync_reminders_for_meeting(meeting)

            # Notify the other participant about the completion
            notify_other_participant(meeting, actor_role, actor_name, 'ACCEPTED')

            msg = f"Thank you, {actor_name}! Both participants have approved the meeting. The meeting is now fully CONFIRMED, and WhatsApp and Gmail reminders are active."
        else:
            meeting.overall_status = Meeting.OverallStatus.PENDING
            meeting.authorization_updated_at = now
            other_name = meeting.p2_name if actor_role == "Host" else meeting.p1_name
            meeting.authorization_note = f"Accepted by {actor_name} ({actor_role}). Awaiting approval from {other_name}."
            meeting.save()

            # Notify the other participant
            notify_other_participant(meeting, actor_role, actor_name, 'ACCEPTED')

            msg = f"Thank you, {actor_name}! Your acceptance has been recorded. The meeting will be confirmed once {other_name} approves."

    elif action == 'REJECT':
        if actor_role == "Host":
            meeting.p1_auth_status = Meeting.ParticipantAuth.REJECTED
            meeting.p1_auth_updated_at = now
        else:
            meeting.p2_auth_status = Meeting.ParticipantAuth.REJECTED
            meeting.p2_auth_updated_at = now

        meeting.overall_status = Meeting.OverallStatus.REJECTED
        meeting.authorization_updated_at = now
        meeting.authorization_note = f"Rejected by {actor_name} ({actor_role}). Reason: {reason or 'Not specified'}"
        meeting.save()

        # Cancel all reminders immediately
        cancel_reminders_for_meeting(meeting, reason=f"Rejected by {actor_name}")

        # Notify the other participant
        notify_other_participant(meeting, actor_role, actor_name, 'REJECTED', detail=reason)

        msg = f"Meeting has been declined. No reminders will be scheduled for this meeting."

    elif action == 'RESCHEDULE':
        if not new_datetime:
            return False, "Please provide a valid proposed date and time for rescheduling.", meeting, actor_role

        meeting.rescheduled_date_time = new_datetime
        meeting.reschedule_reason = reason
        meeting.rescheduled_by = f"{actor_name} ({actor_role})"
        
        # Reset statuses for revised timing confirmation
        if actor_role == "Host":
            meeting.p1_auth_status = Meeting.ParticipantAuth.ACCEPTED  # Submitter agrees to their own proposal
            meeting.p1_auth_updated_at = now
            meeting.p2_auth_status = Meeting.ParticipantAuth.PENDING
            meeting.p2_auth_updated_at = None
        else:
            meeting.p2_auth_status = Meeting.ParticipantAuth.ACCEPTED
            meeting.p2_auth_updated_at = now
            meeting.p1_auth_status = Meeting.ParticipantAuth.PENDING
            meeting.p1_auth_updated_at = None

        meeting.overall_status = Meeting.OverallStatus.RESCHEDULE_REQUESTED
        meeting.authorization_updated_at = now
        meeting.authorization_note = f"Reschedule requested by {actor_name} to {new_datetime.strftime('%Y-%m-%d %H:%M UTC')}. Reason: {reason}"
        meeting.save()

        # Hold all reminders until revised timing is confirmed by both
        hold_reminders_for_meeting(meeting, reason=f"Reschedule requested by {actor_name}")

        # Notify other participant and dispatch revised authorization messages
        send_authorization_requests_to_both(meeting, base_url=base_url)

        msg = f"Reschedule request submitted for {new_datetime.strftime('%b %d, %Y at %I:%M %p UTC')}. Both participants have been sent revised authorization links."

    else:
        return False, f"Unknown authorization action: {action}", meeting, actor_role

    return True, msg, meeting, actor_role


def cancel_reminders_for_meeting(meeting, reason=""):
    """Cancels all scheduled reminders for a meeting and creates audit log."""
    from reminders.models import ScheduledReminder, NotificationLog
    reminders = ScheduledReminder.objects.filter(
        meeting=meeting,
        status__in=[ScheduledReminder.Status.SCHEDULED, ScheduledReminder.Status.PENDING]
    )
    count = reminders.count()
    now_str = timezone.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    reminders.update(
        status=ScheduledReminder.Status.CANCELLED,
        dispatch_log=f"Cancelled: {reason} on {now_str}"
    )

    NotificationLog.objects.create(
        meeting=meeting,
        channel="SYSTEM",
        action_type=NotificationLog.ActionType.SYSTEM,
        recipient_name="Both Participants",
        recipient_role="Both Participants",
        recipient_contact=f"{meeting.p1_email} / {meeting.p2_email}",
        subject_or_headline="Reminders Cancelled",
        content_preview=f"All {count} scheduled reminders across WhatsApp and Gmail cancelled. Reason: {reason}",
        status="CANCELLED"
    )


def hold_reminders_for_meeting(meeting, reason=""):
    """Puts reminders on hold for unconfirmed or reschedule-pending meetings."""
    from reminders.models import ScheduledReminder
    ScheduledReminder.objects.filter(
        meeting=meeting,
        status=ScheduledReminder.Status.SCHEDULED
    ).update(
        status=ScheduledReminder.Status.PENDING,
        dispatch_log=f"Held: {reason}"
    )


def sync_reminders_for_meeting(meeting):
    """
    Generates or refreshes scheduled reminders for a CONFIRMED meeting.
    Strictly WhatsApp and Gmail only!
    """
    from reminders.models import Meeting, ReminderSetting, ScheduledReminder

    # STRICT RULE: Only CONFIRMED meetings can have active reminders
    if meeting.overall_status != Meeting.OverallStatus.CONFIRMED:
        if meeting.overall_status == Meeting.OverallStatus.REJECTED:
            cancel_reminders_for_meeting(meeting, reason="Meeting is Rejected")
        else:
            hold_reminders_for_meeting(meeting, reason="Awaiting participant confirmations")
        return []

    settings = ReminderSetting.get_settings()
    intervals = settings.get_intervals()  # e.g. [{"minutes": 15, "label": "15 minutes"}]
    target_start = meeting.rescheduled_date_time if (meeting.rescheduled_date_time and meeting.is_confirmed) else meeting.start_time

    # Determine enabled channels (ONLY WhatsApp and Gmail)
    active_channels = []
    if settings.whatsapp_enabled:
        active_channels.append(ScheduledReminder.Channel.WHATSAPP)
    if settings.email_enabled:
        active_channels.append(ScheduledReminder.Channel.EMAIL)

    created_or_updated = []

    for interval in intervals:
        offset_mins = interval.get("minutes", 15)
        label = interval.get("label", f"{offset_mins} mins before")
        scheduled_time = target_start - timedelta(minutes=offset_mins)

        for channel in active_channels:
            existing = ScheduledReminder.objects.filter(
                meeting=meeting,
                channel=channel,
                offset_minutes=offset_mins,
            ).order_by('id')

            if existing.exists():
                reminder = existing.first()
                # Clean up any accidental duplicate rows
                if existing.count() > 1:
                    existing.exclude(id=reminder.id).delete()
                if reminder.status != ScheduledReminder.Status.DISPATCHED:
                    reminder.offset_label = label
                    reminder.scheduled_time = scheduled_time
                    reminder.status = ScheduledReminder.Status.SCHEDULED
                    reminder.dispatch_log = "Re-scheduled upon full meeting confirmation"
                    reminder.save()
            else:
                reminder = ScheduledReminder.objects.create(
                    meeting=meeting,
                    channel=channel,
                    offset_minutes=offset_mins,
                    offset_label=label,
                    scheduled_time=scheduled_time,
                    status=ScheduledReminder.Status.SCHEDULED,
                    dispatch_log=f"Scheduled for {scheduled_time.strftime('%Y-%m-%d %H:%M:%S UTC')} (Both participants confirmed)"
                )

            created_or_updated.append(reminder)

    return created_or_updated


def format_reminder_payload(channel, meeting, reminder, recipient_role, recipient_name):
    """Formats 15-minute or custom reminder message for WhatsApp and Gmail."""
    target_time = meeting.rescheduled_date_time if (meeting.rescheduled_date_time and meeting.is_confirmed) else meeting.start_time
    time_str = target_time.strftime("%A, %b %d, %Y at %I:%M %p UTC")
    other_party = f"{meeting.p2_name} ({meeting.p2_role})" if recipient_role == "Host" else f"{meeting.p1_name} ({meeting.p1_role})"

    if channel == "WHATSAPP":
        headline = f"WhatsApp Reminder ({reminder.offset_label})"
        body = (
            f"⏰ *MeetCue Reminder*\n\n"
            f"Hello {recipient_name},\n"
            f"Your confirmed meeting *\"{meeting.purpose}\"* is starting in *{reminder.offset_label}* ({time_str}).\n\n"
            f"👤 *Client Name:* {meeting.client_name}\n"
            f"👥 *Meeting with:* {other_party}\n"
            f"⏱ *Duration:* {meeting.duration_minutes} mins\n"
            f"📍 *Join URL / Location:* {meeting.location}\n\n"
            f"_Sent via MeetCue Automated Reminder System._"
        )
    else:  # EMAIL (Gmail)
        headline = f"Reminder: {meeting.purpose} starts in {reminder.offset_label}"
        body = (
            f"Dear {recipient_name},\n\n"
            f"This is an automated reminder that your confirmed session is starting in {reminder.offset_label}.\n\n"
            f"SESSION DETAILS:\n"
            f"• Purpose: {meeting.purpose}\n"
            f"• Client: {meeting.client_name}\n"
            f"• Date/Time: {time_str}\n"
            f"• Duration: {meeting.duration_minutes} minutes\n"
            f"• Location / Video Link: {meeting.location}\n"
            f"• Host: {meeting.p1_name} ({meeting.p1_email})\n"
            f"• Client: {meeting.p2_name} ({meeting.p2_email})\n\n"
            f"Agenda Notes:\n{meeting.notes or 'No additional notes provided.'}\n\n"
            f"Best regards,\nMeetCue Reminder System"
        )
    return headline, body


def dispatch_reminder_to_both_participants(reminder):
    """
    Dispatches reminder to BOTH participants via WhatsApp and Gmail.
    Accurately records DELIVERED or NOT_CONFIGURED status.
    """
    from reminders.models import Meeting, ScheduledReminder, NotificationLog, ReminderSetting

    meeting = reminder.meeting

    # SECURITY CHECK: Must be confirmed by both participants
    if meeting.overall_status != Meeting.OverallStatus.CONFIRMED:
        reminder.status = ScheduledReminder.Status.CANCELLED
        reminder.dispatch_log = f"BLOCKED: Meeting overall status is {meeting.overall_status} (Both participants must confirm)."
        reminder.save()
        return False

    settings = ReminderSetting.get_settings()
    now = timezone.now()
    dispatched_targets = []

    # Participant 1 (Host)
    if settings.notify_participant1:
        contact = meeting.p1_phone if reminder.channel == 'WHATSAPP' else meeting.p1_email
        headline, body = format_reminder_payload(reminder.channel, meeting, reminder, "Host", meeting.p1_name)
        
        if reminder.channel == 'WHATSAPP':
            success, log_msg = send_whatsapp_message(contact, body)
            status = 'DELIVERED' if success else ('NOT_CONFIGURED' if 'NOT_CONFIGURED' in log_msg else 'FAILED')
        else:
            success, log_msg = send_gmail_message(contact, headline, body)
            status = 'DELIVERED' if success else ('NOT_CONFIGURED' if 'NOT_CONFIGURED' in log_msg else 'FAILED')

        NotificationLog.objects.create(
            meeting=meeting,
            reminder=reminder,
            channel=reminder.channel,
            action_type=NotificationLog.ActionType.REMINDER,
            recipient_name=meeting.p1_name,
            recipient_role=meeting.p1_role,
            recipient_contact=contact,
            subject_or_headline=headline,
            content_preview=body[:300] + "...",
            status=status
        )
        dispatched_targets.append(f"{meeting.p1_name} ({status})")

    # Participant 2 (Client)
    if settings.notify_participant2:
        contact = meeting.p2_phone if reminder.channel == 'WHATSAPP' else meeting.p2_email
        headline, body = format_reminder_payload(reminder.channel, meeting, reminder, "Client", meeting.p2_name)

        if reminder.channel == 'WHATSAPP':
            success, log_msg = send_whatsapp_message(contact, body)
            status = 'DELIVERED' if success else ('NOT_CONFIGURED' if 'NOT_CONFIGURED' in log_msg else 'FAILED')
        else:
            success, log_msg = send_gmail_message(contact, headline, body)
            status = 'DELIVERED' if success else ('NOT_CONFIGURED' if 'NOT_CONFIGURED' in log_msg else 'FAILED')

        NotificationLog.objects.create(
            meeting=meeting,
            reminder=reminder,
            channel=reminder.channel,
            action_type=NotificationLog.ActionType.REMINDER,
            recipient_name=meeting.p2_name,
            recipient_role=meeting.p2_role,
            recipient_contact=contact,
            subject_or_headline=headline,
            content_preview=body[:300] + "...",
            status=status
        )
        dispatched_targets.append(f"{meeting.p2_name} ({status})")

    reminder.status = ScheduledReminder.Status.DISPATCHED
    reminder.dispatched_at = now
    reminder.dispatch_log = f"Processed {reminder.channel} reminder for: {', '.join(dispatched_targets)} at {now.strftime('%Y-%m-%d %H:%M:%S UTC')}"
    reminder.save()
    return True


def run_scheduler_cycle():
    """Checks for due reminders on CONFIRMED meetings and processes them."""
    from reminders.models import Meeting, ScheduledReminder

    now = timezone.now()
    due_reminders = ScheduledReminder.objects.filter(
        status=ScheduledReminder.Status.SCHEDULED,
        scheduled_time__lte=now,
        meeting__overall_status=Meeting.OverallStatus.CONFIRMED
    )

    count = 0
    for reminder in due_reminders:
        if dispatch_reminder_to_both_participants(reminder):
            count += 1

    return count


# Backward-compatibility alias
def update_timing_authorization(meeting, new_status, reason=""):
    """Adapter for legacy single-status calls in views or scripts."""
    from reminders.models import Meeting
    if new_status == 'ACCEPTED':
        meeting.p1_auth_status = Meeting.ParticipantAuth.ACCEPTED
        meeting.p2_auth_status = Meeting.ParticipantAuth.ACCEPTED
        meeting.overall_status = Meeting.OverallStatus.CONFIRMED
    elif new_status == 'REJECTED':
        meeting.p1_auth_status = Meeting.ParticipantAuth.REJECTED
        meeting.overall_status = Meeting.OverallStatus.REJECTED
    else:
        meeting.p1_auth_status = Meeting.ParticipantAuth.PENDING
        meeting.p2_auth_status = Meeting.ParticipantAuth.PENDING
        meeting.overall_status = Meeting.OverallStatus.PENDING
    
    meeting.authorization_updated_at = timezone.now()
    if reason:
        meeting.authorization_note = reason
    meeting.save()

    if meeting.overall_status == Meeting.OverallStatus.CONFIRMED:
        sync_reminders_for_meeting(meeting)
    elif meeting.overall_status == Meeting.OverallStatus.REJECTED:
        cancel_reminders_for_meeting(meeting, reason=reason)
    else:
        hold_reminders_for_meeting(meeting, reason=reason)
    return meeting
