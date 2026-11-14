from reminders.models import Meeting, ScheduledReminder, ReminderSetting

def system_stats(request):
    """Provides global counts and states for the navigation bar and layout."""
    confirmed_count = Meeting.objects.filter(overall_status=Meeting.OverallStatus.CONFIRMED).count()
    pending_count = Meeting.objects.filter(overall_status__in=[Meeting.OverallStatus.PENDING, Meeting.OverallStatus.RESCHEDULE_REQUESTED]).count()
    rejected_count = Meeting.objects.filter(overall_status=Meeting.OverallStatus.REJECTED).count()
    total_count = Meeting.objects.count()
    active_reminders_count = ScheduledReminder.objects.filter(status=ScheduledReminder.Status.SCHEDULED).count()
    settings = ReminderSetting.get_settings()

    return {
        'nav_total_count': total_count,
        'nav_confirmed_count': confirmed_count,
        'nav_pending_count': pending_count,
        'nav_rejected_count': rejected_count,
        'nav_active_reminders_count': active_reminders_count,
        'global_settings': settings,
    }
