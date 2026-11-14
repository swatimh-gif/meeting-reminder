import secrets
import json
from datetime import timedelta
from django.db import models
from django.utils import timezone


class Meeting(models.Model):
    class ParticipantAuth(models.TextChoices):
        PENDING = 'PENDING', 'Pending Confirmation'
        ACCEPTED = 'ACCEPTED', 'Accepted'
        REJECTED = 'REJECTED', 'Rejected'
        RESCHEDULE_REQUESTED = 'RESCHEDULE_REQUESTED', 'Reschedule Requested'

    class OverallStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending Confirmation'
        CONFIRMED = 'CONFIRMED', 'Confirmed (Reminders Active)'
        REJECTED = 'REJECTED', 'Rejected (Cancelled)'
        RESCHEDULE_REQUESTED = 'RESCHEDULE_REQUESTED', 'Reschedule Requested'

    # Legacy alias for backward compatibility
    class TimingAuth(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        ACCEPTED = 'ACCEPTED', 'Accepted'
        REJECTED = 'REJECTED', 'Rejected'

    booking_id = models.CharField(
        max_length=64, 
        unique=True, 
        help_text="Unique booking reference identifier fetched from external booking module"
    )

    # Participant 1 (Host / Organizer)
    p1_name = models.CharField(max_length=150, verbose_name="Host Name")
    p1_email = models.EmailField(verbose_name="Host Email")
    p1_phone = models.CharField(max_length=50, verbose_name="Host Phone")
    p1_role = models.CharField(max_length=100, default="Host / Organizer", verbose_name="Host Role")
    p1_auth_status = models.CharField(
        max_length=25,
        choices=ParticipantAuth.choices,
        default=ParticipantAuth.PENDING,
        verbose_name="Host Authorization Status"
    )
    p1_auth_updated_at = models.DateTimeField(null=True, blank=True)
    p1_token = models.CharField(max_length=64, unique=True, blank=True, null=True, db_index=True)

    # Participant 2 (Invitee / Client)
    p2_name = models.CharField(max_length=150, verbose_name="Client / Invitee Name")
    p2_email = models.EmailField(verbose_name="Client / Invitee Email")
    p2_phone = models.CharField(max_length=50, verbose_name="Client / Invitee Phone")
    p2_role = models.CharField(max_length=100, default="Client / Invitee", verbose_name="Client / Invitee Role")
    p2_auth_status = models.CharField(
        max_length=25,
        choices=ParticipantAuth.choices,
        default=ParticipantAuth.PENDING,
        verbose_name="Client Authorization Status"
    )
    p2_auth_updated_at = models.DateTimeField(null=True, blank=True)
    p2_token = models.CharField(max_length=64, unique=True, blank=True, null=True, db_index=True)

    # Meeting details
    purpose = models.CharField(max_length=255, verbose_name="Meeting Title & Purpose")
    start_time = models.DateTimeField(verbose_name="Start Date & Time")
    duration_minutes = models.PositiveIntegerField(default=45, verbose_name="Duration (minutes)")
    location = models.CharField(max_length=255, default="Google Meet (meet.google.com/mfl-apex-sync)", verbose_name="Location / Video Link")
    notes = models.TextField(blank=True, verbose_name="Meeting Agenda & Notes")
    source_module = models.CharField(max_length=120, default="External Booking Engine (REST API v2.4)", verbose_name="Source Module")

    # Overall Meeting Status (Confirmed ONLY when both participants accept)
    overall_status = models.CharField(
        max_length=25,
        choices=OverallStatus.choices,
        default=OverallStatus.PENDING,
        verbose_name="Overall Meeting Status"
    )

    # Rescheduling support
    rescheduled_date_time = models.DateTimeField(null=True, blank=True, verbose_name="Proposed Rescheduled Date & Time")
    reschedule_reason = models.TextField(blank=True, verbose_name="Reschedule Suggestion / Reason")
    rescheduled_by = models.CharField(max_length=150, blank=True, verbose_name="Rescheduled By")

    # Legacy field preserved for DB backward compatibility
    timing_authorization = models.CharField(
        max_length=20,
        default='PENDING',
        blank=True,
        help_text="Legacy authorization status"
    )
    authorization_updated_at = models.DateTimeField(null=True, blank=True)
    authorization_note = models.TextField(blank=True, verbose_name="Authorization Audit Notes")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['start_time']
        verbose_name = "Meeting"
        verbose_name_plural = "Meetings"

    def __str__(self):
        return f"[{self.booking_id}] {self.purpose} ({self.overall_status})"

    def save(self, *args, **kwargs):
        # Generate unique URL-safe tokens for WhatsApp and Gmail authorization links
        if not self.p1_token:
            self.p1_token = secrets.token_urlsafe(32)
        if not self.p2_token:
            self.p2_token = secrets.token_urlsafe(32)

        # Sync legacy timing_authorization field
        if self.overall_status == self.OverallStatus.CONFIRMED:
            self.timing_authorization = 'ACCEPTED'
        elif self.overall_status == self.OverallStatus.REJECTED:
            self.timing_authorization = 'REJECTED'
        else:
            self.timing_authorization = 'PENDING'

        super().save(*args, **kwargs)

    # Status check properties
    @property
    def is_confirmed(self):
        return self.overall_status == self.OverallStatus.CONFIRMED

    @property
    def is_pending(self):
        return self.overall_status == self.OverallStatus.PENDING

    @property
    def is_rejected(self):
        return self.overall_status == self.OverallStatus.REJECTED

    @property
    def is_reschedule_requested(self):
        return self.overall_status == self.OverallStatus.RESCHEDULE_REQUESTED

    @property
    def can_trigger_reminders(self):
        """Reminders can ONLY trigger when both participants have accepted (CONFIRMED)."""
        return self.is_confirmed

    # Legacy properties
    @property
    def is_accepted(self):
        return self.is_confirmed

    @property
    def p1_accepted(self):
        return self.p1_auth_status == self.ParticipantAuth.ACCEPTED

    @property
    def p2_accepted(self):
        return self.p2_auth_status == self.ParticipantAuth.ACCEPTED

    # Convenience contact properties
    @property
    def client_name(self):
        return self.p2_name

    @property
    def client_email(self):
        return self.p2_email

    @property
    def client_phone(self):
        return self.p2_phone

    @property
    def client_role(self):
        return self.p2_role

    @property
    def host_name(self):
        return self.p1_name

    @property
    def host_email(self):
        return self.p1_email

    @property
    def host_phone(self):
        return self.p1_phone

    @property
    def host_role(self):
        return self.p1_role

    @property
    def meeting_date_formatted(self):
        return self.start_time.strftime("%b %d, %Y")

    @property
    def meeting_time_formatted(self):
        return self.start_time.strftime("%I:%M %p UTC")

    @property
    def rescheduled_date_formatted(self):
        return self.rescheduled_date_time.strftime("%b %d, %Y") if self.rescheduled_date_time else ""

    @property
    def rescheduled_time_formatted(self):
        return self.rescheduled_date_time.strftime("%I:%M %p UTC") if self.rescheduled_date_time else ""

    @property
    def end_time(self):
        return self.start_time + timedelta(minutes=self.duration_minutes)

    @property
    def reminder_status(self):
        """Returns accurate reminder status derived from database records."""
        if not self.is_confirmed:
            if self.is_rejected:
                return "Cancelled"
            elif self.is_reschedule_requested:
                return "On Hold (Reschedule Requested)"
            return "On Hold (Awaiting Confirmations)"

        scheduled_count = self.scheduled_reminders.filter(status=ScheduledReminder.Status.SCHEDULED).count()
        dispatched_count = self.scheduled_reminders.filter(status=ScheduledReminder.Status.DISPATCHED).count()
        if dispatched_count > 0 and scheduled_count > 0:
            return f"Active ({dispatched_count} sent, {scheduled_count} scheduled)"
        elif dispatched_count > 0:
            return f"Dispatched ({dispatched_count} sent)"
        elif scheduled_count > 0:
            return f"Scheduled ({scheduled_count} triggers)"
        return "Active"

    @property
    def time_until(self):
        now = timezone.now()
        if self.start_time > now:
            diff = self.start_time - now
            days = diff.days
            hours, remainder = divmod(diff.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            if days > 0:
                return f"in {days}d {hours}h"
            elif hours > 0:
                return f"in {hours}h {minutes}m"
            else:
                return f"in {minutes}m"
        else:
            diff = now - self.start_time
            return f"{diff.days}d ago" if diff.days > 0 else "Started"


class ReminderSetting(models.Model):
    """Global configuration for MeetCue reminder triggers (WhatsApp and Gmail only)."""
    whatsapp_enabled = models.BooleanField(default=True, verbose_name="WhatsApp Notifications")
    email_enabled = models.BooleanField(default=True, verbose_name="Gmail / Email Notifications")

    notify_participant1 = models.BooleanField(default=True, verbose_name="Notify Participant 1 (Host)")
    notify_participant2 = models.BooleanField(default=True, verbose_name="Notify Participant 2 (Invitee)")

    intervals_data = models.TextField(
        default='[{"minutes": 15, "label": "15 minutes"}]',
        verbose_name="Reminder Timing Intervals JSON"
    )

    auto_schedule_on_accept = models.BooleanField(
        default=True,
        help_text="Automatically schedule WhatsApp and Gmail reminders when both participants accept"
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Reminder Setting"
        verbose_name_plural = "Reminder Settings"

    def get_intervals(self):
        try:
            return json.loads(self.intervals_data)
        except Exception:
            return [{"minutes": 15, "label": "15 minutes"}]

    def set_intervals(self, intervals_list):
        self.intervals_data = json.dumps(intervals_list)

    @classmethod
    def get_settings(cls):
        obj, _ = cls.objects.get_or_create(id=1)
        return obj


class ScheduledReminder(models.Model):
    class Channel(models.TextChoices):
        WHATSAPP = 'WHATSAPP', 'WhatsApp'
        EMAIL = 'EMAIL', 'Gmail (Email)'

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending (Held)'
        SCHEDULED = 'SCHEDULED', 'Scheduled (Active)'
        DISPATCHED = 'DISPATCHED', 'Dispatched'
        CANCELLED = 'CANCELLED', 'Cancelled'

    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name='scheduled_reminders')
    channel = models.CharField(max_length=20, choices=Channel.choices)
    offset_minutes = models.PositiveIntegerField(help_text="Minutes before meeting start time")
    offset_label = models.CharField(max_length=100)
    scheduled_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    dispatched_at = models.DateTimeField(null=True, blank=True)
    dispatch_log = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['scheduled_time']
        verbose_name = "Scheduled Reminder"
        verbose_name_plural = "Scheduled Reminders"

    def __str__(self):
        return f"{self.channel} ({self.offset_label}) for {self.meeting.booking_id} [{self.status}]"


class NotificationLog(models.Model):
    class ActionType(models.TextChoices):
        AUTH_REQUEST = 'AUTH_REQUEST', 'Authorization Request'
        AUTH_RESPONSE = 'AUTH_RESPONSE', 'Participant Decision'
        RESCHEDULE = 'RESCHEDULE', 'Reschedule Notice'
        REMINDER = 'REMINDER', 'Meeting Reminder'
        SYSTEM = 'SYSTEM', 'System Audit'

    meeting = models.ForeignKey(Meeting, on_delete=models.SET_NULL, null=True, related_name='notification_logs')
    reminder = models.ForeignKey(ScheduledReminder, on_delete=models.SET_NULL, null=True, related_name='logs')
    channel = models.CharField(max_length=20)  # WHATSAPP, EMAIL, SYSTEM
    action_type = models.CharField(max_length=30, default='REMINDER')
    recipient_name = models.CharField(max_length=150)
    recipient_role = models.CharField(max_length=100)
    recipient_contact = models.CharField(max_length=120)
    subject_or_headline = models.CharField(max_length=255)
    content_preview = models.TextField()
    status = models.CharField(max_length=30, default='DELIVERED')  # DELIVERED, NOT_CONFIGURED, CANCELLED, FAILED
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Notification Log"
        verbose_name_plural = "Notification Logs"

    def __str__(self):
        return f"[{self.action_type}] {self.channel} -> {self.recipient_name} ({self.status}) at {self.created_at.strftime('%Y-%m-%d %H:%M')}"
