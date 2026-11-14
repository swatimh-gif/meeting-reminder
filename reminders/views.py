import json
import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q

from reminders.models import Meeting, ReminderSetting, ScheduledReminder, NotificationLog
from reminders.services.booking_service import ExternalBookingClient
from reminders.services.scheduler import (
    process_participant_decision,
    sync_reminders_for_meeting,
    run_scheduler_cycle,
)
from reminders.services.notification_service import (
    send_authorization_requests_to_both,
    build_auth_links,
    is_whatsapp_configured,
    is_gmail_configured,
)


def get_dashboard_context(initial_tab='overview', search_query=''):
    """Assembles context for MeetCue dashboard."""
    now = timezone.now()
    today = now.date()
    tomorrow = today + datetime.timedelta(days=1)
    week_start = today - datetime.timedelta(days=today.weekday())
    week_end = week_start + datetime.timedelta(days=6)

    all_meetings = Meeting.objects.all().order_by('start_time')

    if search_query:
        all_meetings = all_meetings.filter(
            Q(purpose__icontains=search_query) |
            Q(booking_id__icontains=search_query) |
            Q(p1_name__icontains=search_query) |
            Q(p2_name__icontains=search_query) |
            Q(p1_email__icontains=search_query) |
            Q(p2_email__icontains=search_query)
        )

    confirmed_meetings = all_meetings.filter(overall_status=Meeting.OverallStatus.CONFIRMED)
    pending_meetings = all_meetings.filter(overall_status__in=[Meeting.OverallStatus.PENDING, Meeting.OverallStatus.RESCHEDULE_REQUESTED])
    rejected_meetings = all_meetings.filter(overall_status=Meeting.OverallStatus.REJECTED)

    # Time-based subsets for confirmed meetings
    confirmed_today = confirmed_meetings.filter(start_time__date=today)
    confirmed_tomorrow = confirmed_meetings.filter(start_time__date=tomorrow)
    confirmed_this_week = confirmed_meetings.filter(start_time__date__gte=week_start, start_time__date__lte=week_end)
    confirmed_this_month = confirmed_meetings.filter(start_time__year=today.year, start_time__month=today.month)

    # Upcoming preview: next 5 meetings
    upcoming_meetings = all_meetings.filter(start_time__gte=now)[:5]
    if not upcoming_meetings.exists():
        upcoming_meetings = all_meetings[:5]

    # Recent activity logs (latest 8)
    recent_activity = NotificationLog.objects.all().order_by('-created_at')[:8]

    settings = ReminderSetting.get_settings()
    intervals = settings.get_intervals()
    active_interval_minutes = [item.get('minutes') for item in intervals]

    wa_cfg = is_whatsapp_configured()
    gm_cfg = is_gmail_configured()

    # JSON representation for the interactive calendar and instant client-side date selection
    meetings_data_list = []
    for m in all_meetings:
        meetings_data_list.append({
            'id': m.id,
            'booking_id': m.booking_id,
            'purpose': m.purpose,
            'start_time': m.start_time.isoformat(),
            'date_str': m.start_time.strftime('%Y-%m-%d'),
            'formatted_date': m.start_time.strftime('%a, %b %d, %Y'),
            'formatted_time': m.start_time.strftime('%I:%M %p UTC'),
            'duration': f"{m.duration_minutes} mins",
            'location': m.location or 'Online',
            'client_name': m.client_name,
            'client_email': m.client_email,
            'client_phone': m.client_phone,
            'client_role': m.client_role,
            'host_name': m.host_name,
            'host_email': m.host_email,
            'host_phone': m.host_phone,
            'host_role': m.host_role,
            'overall_status': m.overall_status,
            'p1_auth_status': m.p1_auth_status,
            'p2_auth_status': m.p2_auth_status,
            'whatsapp_configured': wa_cfg,
            'gmail_configured': gm_cfg,
        })

    return {
        'total_meetings': Meeting.objects.count(),
        'confirmed_count': confirmed_meetings.count(),
        'pending_count': pending_meetings.count(),
        'rejected_count': rejected_meetings.count(),
        'confirmed_today': confirmed_today,
        'confirmed_tomorrow': confirmed_tomorrow,
        'confirmed_this_week': confirmed_this_week,
        'confirmed_this_month': confirmed_this_month,
        'confirmed_meetings': confirmed_meetings,
        'pending_meetings': pending_meetings,
        'upcoming_meetings': upcoming_meetings,
        'recent_activity': recent_activity,
        'all_meetings': all_meetings,
        'settings': settings,
        'intervals': intervals,
        'active_interval_minutes': active_interval_minutes,
        'active_tab': initial_tab,
        'search_query': search_query,
        'whatsapp_configured': wa_cfg,
        'gmail_configured': gm_cfg,
        'meetings_json': json.dumps(meetings_data_list),
        'today_str': today.strftime('%Y-%m-%d'),
    }


def overview(request):
    """Main SaaS Dashboard with zero-reload internal tabs (Overview, All Meetings, Settings)."""
    initial_tab = request.GET.get('tab', 'overview')
    context = get_dashboard_context(initial_tab=initial_tab)
    return render(request, 'reminders/dashboard.html', context)


def meetings_list(request):
    """Direct route for All Meetings tab."""
    search_query = request.GET.get('q', '').strip()
    context = get_dashboard_context(initial_tab='meetings', search_query=search_query)
    return render(request, 'reminders/dashboard.html', context)


def settings_view(request):
    """Direct route for Reminder Settings tab."""
    context = get_dashboard_context(initial_tab='settings')
    return render(request, 'reminders/dashboard.html', context)


def meeting_detail(request, pk):
    """
    Returns meeting details for inspection modal.
    Includes participant authorization statuses and preview links.
    """
    meeting = get_object_or_404(Meeting, pk=pk)
    base_url = request.build_absolute_uri('/')

    p1_links = build_auth_links(meeting, meeting.p1_token, base_url)
    p2_links = build_auth_links(meeting, meeting.p2_token, base_url)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
        return JsonResponse({
            'id': meeting.pk,
            'booking_id': meeting.booking_id,
            'purpose': meeting.purpose,
            'client_name': meeting.client_name,
            'client_email': meeting.client_email,
            'client_phone': meeting.client_phone,
            'client_role': meeting.client_role,
            'host_name': meeting.host_name,
            'host_email': meeting.host_email,
            'host_phone': meeting.host_phone,
            'host_role': meeting.host_role,
            'date': meeting.meeting_date_formatted,
            'time': meeting.meeting_time_formatted,
            'duration': f"{meeting.duration_minutes} mins",
            'location': meeting.location,
            'notes': meeting.notes or 'No agenda notes provided.',
            'overall_status': meeting.overall_status,
            'p1_auth_status': meeting.p1_auth_status,
            'p2_auth_status': meeting.p2_auth_status,
            'reminder_status': meeting.reminder_status,
            'rescheduled_date': meeting.rescheduled_date_formatted,
            'rescheduled_time': meeting.rescheduled_time_formatted,
            'reschedule_reason': meeting.reschedule_reason,
            'rescheduled_by': meeting.rescheduled_by,
            'p1_links': p1_links,
            'p2_links': p2_links,
        })

    reminders = meeting.scheduled_reminders.all().order_by('scheduled_time')
    return render(request, 'reminders/meeting_detail.html', {
        'meeting': meeting,
        'reminders': reminders,
        'p1_links': p1_links,
        'p2_links': p2_links,
        'active_tab': 'meetings'
    })


def auth_action_view(request, token, action):
    """
    Public Endpoint for WhatsApp and Gmail Authorization Links:
    Accepts action: 'accept' or 'reject'
    """
    # Look up meeting by participant token
    meeting = Meeting.objects.filter(Q(p1_token=token) | Q(p2_token=token)).first()
    if not meeting:
        return render(request, 'reminders/auth_response.html', {
            'success': False,
            'title': 'Invalid Link',
            'message': 'This meeting authorization link is invalid or has expired.'
        }, status=404)

    base_url = request.build_absolute_uri('/')
    success, user_msg, meeting, actor_role = process_participant_decision(
        meeting=meeting,
        token=token,
        action=action,
        base_url=base_url
    )

    actor_name = meeting.p1_name if actor_role == 'Host' else meeting.p2_name

    return render(request, 'reminders/auth_response.html', {
        'success': success,
        'meeting': meeting,
        'actor_role': actor_role,
        'actor_name': actor_name,
        'action': action.upper(),
        'title': 'Meeting Accepted' if action.lower() == 'accept' else 'Meeting Rejected',
        'message': user_msg,
    })


def reschedule_view(request, token):
    """
    Public Endpoint for Reschedule Link:
    GET: Displays clean form to suggest new date, time, and reason.
    POST: Processes proposed timing and dispatches revised authorization to both participants.
    """
    meeting = Meeting.objects.filter(Q(p1_token=token) | Q(p2_token=token)).first()
    if not meeting:
        return render(request, 'reminders/auth_response.html', {
            'success': False,
            'title': 'Invalid Link',
            'message': 'This reschedule link is invalid or has expired.'
        }, status=404)

    actor_role = "Host" if token == meeting.p1_token else "Client"
    actor_name = meeting.p1_name if actor_role == "Host" else meeting.p2_name

    if request.method == 'POST':
        new_date_str = request.POST.get('new_date')
        new_time_str = request.POST.get('new_time')
        reason = request.POST.get('reason', '').strip()

        if not new_date_str or not new_time_str:
            messages.error(request, "Please specify both a proposed date and time.")
            return render(request, 'reminders/reschedule_form.html', {
                'meeting': meeting,
                'actor_role': actor_role,
                'actor_name': actor_name,
                'token': token,
            })

        try:
            naive_dt = datetime.datetime.strptime(f"{new_date_str} {new_time_str}", "%Y-%m-%d %H:%M")
            new_datetime = timezone.make_aware(naive_dt, timezone.get_current_timezone())
        except Exception:
            messages.error(request, "Invalid date/time format submitted.")
            return render(request, 'reminders/reschedule_form.html', {
                'meeting': meeting,
                'actor_role': actor_role,
                'actor_name': actor_name,
                'token': token,
            })

        base_url = request.build_absolute_uri('/')
        success, user_msg, meeting, _ = process_participant_decision(
            meeting=meeting,
            token=token,
            action='RESCHEDULE',
            reason=reason,
            new_datetime=new_datetime,
            base_url=base_url
        )

        return render(request, 'reminders/auth_response.html', {
            'success': success,
            'meeting': meeting,
            'actor_role': actor_role,
            'actor_name': actor_name,
            'action': 'RESCHEDULE',
            'title': 'Reschedule Request Submitted',
            'message': user_msg,
        })

    # Render clean reschedule request form
    return render(request, 'reminders/reschedule_form.html', {
        'meeting': meeting,
        'actor_role': actor_role,
        'actor_name': actor_name,
        'token': token,
    })


def send_auth_requests_view(request, pk):
    """
    Sends or resends WhatsApp and Gmail authorization messages to BOTH participants.
    """
    if request.method != 'POST':
        return redirect('overview')

    meeting = get_object_or_404(Meeting, pk=pk)
    base_url = request.build_absolute_uri('/')

    results = send_authorization_requests_to_both(meeting, base_url=base_url)

    delivered_count = sum(1 for r in results if r['status'] == 'DELIVERED')
    not_config_count = sum(1 for r in results if r['status'] == 'NOT_CONFIGURED')

    if not_config_count > 0:
        messages.warning(
            request,
            f"Authorization links generated for '{meeting.booking_id}'. Note: Notification channels marked as NOT_CONFIGURED (configure Twilio/Gmail in .env to enable live delivery)."
        )
    else:
        messages.success(request, f"Authorization messages dispatched via WhatsApp & Gmail to {meeting.p1_name} and {meeting.p2_name}.")

    next_url = request.POST.get('next') or '/#meetings'
    return redirect(next_url)


def save_reminder_preferences(request):
    """
    Saves WhatsApp & Gmail preferences and 3-column reminder lead times.
    Supports pill button selection:
    - Minutes (5, 10, 15, 30, 45)
    - Hours (1, 2, 3, 6, 12)
    - Days (1, 2, 3, 5, 7)
    - Plus optional custom timing input.
    """
    if request.method != 'POST':
        return redirect('/#settings')

    settings = ReminderSetting.get_settings()
    settings.whatsapp_enabled = (request.POST.get('whatsapp_enabled') == 'on')
    settings.email_enabled = (request.POST.get('email_enabled') == 'on')

    # Selected interval minutes from checkboxes / pill inputs (named 'intervals')
    selected_minutes_raw = request.POST.getlist('intervals')

    # Optional custom timing input
    custom_val = request.POST.get('custom_value', '').strip()
    custom_unit = request.POST.get('custom_unit', 'minutes')
    if custom_val and custom_val.isdigit():
        val = int(custom_val)
        if val > 0:
            if custom_unit == 'hours':
                selected_minutes_raw.append(str(val * 60))
            elif custom_unit == 'days':
                selected_minutes_raw.append(str(val * 1440))
            else:
                selected_minutes_raw.append(str(val))

    def label_for_minutes(mins):
        if mins < 60:
            return f"{mins} min" if mins != 15 else "15 min (Default)"
        elif mins < 1440:
            hrs = mins // 60
            return f"{hrs} hour" if hrs == 1 else f"{hrs} hours"
        else:
            days = mins // 1440
            return f"{days} day" if days == 1 else f"{days} days"

    new_intervals = []
    seen = set()
    for m_str in selected_minutes_raw:
        try:
            m_int = int(m_str)
            if m_int > 0 and m_int not in seen:
                seen.add(m_int)
                new_intervals.append({
                    "minutes": m_int,
                    "label": label_for_minutes(m_int)
                })
        except ValueError:
            continue

    if not new_intervals:
        new_intervals = [{"minutes": 15, "label": "15 min (Default)"}]

    new_intervals.sort(key=lambda x: x.get('minutes', 0))
    settings.set_intervals(new_intervals)
    settings.save()

    # Re-sync reminders for all confirmed meetings
    for m in Meeting.objects.filter(overall_status=Meeting.OverallStatus.CONFIRMED):
        sync_reminders_for_meeting(m)

    messages.success(request, f"Reminder settings saved: {len(new_intervals)} active reminder timing(s) configured for WhatsApp & Gmail.")
    return redirect('/#settings')


def save_channel_settings(request):
    """Toggles WhatsApp and Gmail notification channels in settings."""
    if request.method != 'POST':
        return redirect('/#settings')

    settings = ReminderSetting.get_settings()
    settings.whatsapp_enabled = (request.POST.get('whatsapp_enabled') == 'on')
    settings.email_enabled = (request.POST.get('email_enabled') == 'on')
    settings.save()

    messages.success(request, "Notification channels updated: WhatsApp and Gmail.")
    return redirect('/#settings')


def add_timing_interval(request):
    """Configures default reminder timing (15m, 30m, 1h, or custom)."""
    if request.method != 'POST':
        return redirect('/#settings')

    settings = ReminderSetting.get_settings()
    intervals = settings.get_intervals()

    timing_type = request.POST.get('timing_type')
    custom_value = request.POST.get('custom_value')
    custom_unit = request.POST.get('custom_unit', 'minutes')

    if timing_type == 'preset':
        preset_mins = int(request.POST.get('preset_minutes', 15))
        label_map = {
            15: "15 minutes",
            30: "30 minutes",
            60: "1 hour",
            1440: "1 day"
        }
        label = label_map.get(preset_mins, f"{preset_mins} minutes")
        minutes = preset_mins
    else:
        try:
            val = int(custom_value)
            if val <= 0:
                messages.error(request, "Please enter a positive timing number.")
                return redirect('/#settings')
        except (ValueError, TypeError):
            messages.error(request, "Invalid custom timing value.")
            return redirect('/#settings')

        if custom_unit == 'hours':
            minutes = val * 60
            label = f"{val} hour" if val == 1 else f"{val} hours"
        elif custom_unit == 'days':
            minutes = val * 1440
            label = f"{val} day" if val == 1 else f"{val} days"
        else:
            minutes = val
            label = f"{val} minutes"

    if any(item.get('minutes') == minutes for item in intervals):
        messages.warning(request, f"Reminder timing for {label} is already configured.")
        return redirect('/#settings')

    intervals.append({"minutes": minutes, "label": label})
    intervals.sort(key=lambda x: x.get('minutes', 0), reverse=True)
    settings.set_intervals(intervals)
    settings.save()

    # Refresh reminders for all confirmed meetings
    for m in Meeting.objects.filter(overall_status=Meeting.OverallStatus.CONFIRMED):
        sync_reminders_for_meeting(m)

    messages.success(request, f"Added reminder timing: {label} before meeting.")
    return redirect('/#settings')


def remove_timing_interval(request):
    """Removes a timing interval from global configuration."""
    if request.method != 'POST':
        return redirect('/#settings')

    minutes_to_remove = int(request.POST.get('minutes', -1))
    settings = ReminderSetting.get_settings()
    intervals = settings.get_intervals()

    new_intervals = [item for item in intervals if item.get('minutes') != minutes_to_remove]
    settings.set_intervals(new_intervals)
    settings.save()

    for m in Meeting.objects.filter(overall_status=Meeting.OverallStatus.CONFIRMED):
        sync_reminders_for_meeting(m)

    messages.success(request, f"Removed timing interval ({minutes_to_remove} minutes).")
    return redirect('/#settings')


def sync_booking_module_view(request):
    """Fetches scheduled meetings from the external booking module."""
    if request.method != 'POST':
        return redirect('/')

    stats = ExternalBookingClient.sync_to_database()
    messages.success(
        request, 
        f"External Booking Module: Synced {stats['total']} scheduled meetings "
        f"({stats['created']} new imported, {stats['updated']} refreshed)."
    )
    return redirect(request.POST.get('next') or '/')


def run_scheduler_view(request):
    """Processes due reminders."""
    if request.method != 'POST':
        return redirect('/')
    count = run_scheduler_cycle()
    messages.success(request, f"Processed {count} scheduled reminders via WhatsApp & Gmail.")
    return redirect(request.POST.get('next') or '/')
