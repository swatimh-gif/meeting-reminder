from django.contrib import admin
from reminders.models import Meeting, ReminderSetting, ScheduledReminder, NotificationLog

@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ('booking_id', 'purpose', 'p1_name', 'p1_auth_status', 'p2_name', 'p2_auth_status', 'overall_status', 'start_time')
    list_filter = ('overall_status', 'p1_auth_status', 'p2_auth_status', 'start_time')
    search_fields = ('booking_id', 'purpose', 'p1_name', 'p1_email', 'p2_name', 'p2_email')
    readonly_fields = ('p1_token', 'p2_token')

@admin.register(ReminderSetting)
class ReminderSettingAdmin(admin.ModelAdmin):
    list_display = ('id', 'whatsapp_enabled', 'email_enabled', 'updated_at')

@admin.register(ScheduledReminder)
class ScheduledReminderAdmin(admin.ModelAdmin):
    list_display = ('meeting', 'channel', 'offset_label', 'scheduled_time', 'status')
    list_filter = ('channel', 'status')
    search_fields = ('meeting__booking_id', 'meeting__purpose')

@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'action_type', 'channel', 'recipient_name', 'recipient_role', 'recipient_contact', 'status')
    list_filter = ('channel', 'action_type', 'status')
    search_fields = ('recipient_name', 'recipient_contact', 'subject_or_headline')
