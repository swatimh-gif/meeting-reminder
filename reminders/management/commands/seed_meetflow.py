from django.core.management.base import BaseCommand
from reminders.models import Meeting, ReminderSetting, ScheduledReminder, NotificationLog
from reminders.services.booking_service import ExternalBookingClient
from reminders.services.scheduler import sync_reminders_for_meeting, dispatch_reminder_to_both_participants
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = "Seeds initial realistic scheduled meetings from mock booking module and initial reminder settings"

    def handle(self, *args, **options):
        self.stdout.write("Initializing MeetFlow Reminder Settings...")
        settings = ReminderSetting.get_settings()
        settings.whatsapp_enabled = True
        settings.email_enabled = True
        settings.notify_participant1 = True
        settings.notify_participant2 = True
        settings.set_intervals([
            {"minutes": 15, "label": "15 minutes"},
            {"minutes": 60, "label": "1 hour"},
            {"minutes": 1440, "label": "1 day"},
        ])
        settings.save()
        self.stdout.write(self.style.SUCCESS("[OK] Reminder Settings initialized (WhatsApp & Gmail active; 15m default)"))

        self.stdout.write("Fetching scheduled meetings from External Booking Module...")
        stats = ExternalBookingClient.sync_to_database()
        self.stdout.write(self.style.SUCCESS(f"[OK] Synced: {stats['created']} created, {stats['updated']} updated (Total: {stats['total']})"))

        # For demo realism: pick one Confirmed meeting and simulate 1 dispatched reminder
        confirmed_meeting = Meeting.objects.filter(overall_status=Meeting.OverallStatus.CONFIRMED).first()
        if confirmed_meeting:
            sync_reminders_for_meeting(confirmed_meeting)
            reminder = ScheduledReminder.objects.filter(meeting=confirmed_meeting, status=ScheduledReminder.Status.SCHEDULED).first()
            if reminder:
                dispatch_reminder_to_both_participants(reminder)
                self.stdout.write(self.style.SUCCESS(f"[OK] Simulated 1 dispatched reminder for meeting {confirmed_meeting.booking_id} to both participants"))

        self.stdout.write(self.style.SUCCESS("MeetFlow database seeding completed successfully!"))
