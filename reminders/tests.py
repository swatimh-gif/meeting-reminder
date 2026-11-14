from django.test import TestCase, Client
from django.utils import timezone
from datetime import timedelta
import datetime
from reminders.models import Meeting, ReminderSetting, ScheduledReminder, NotificationLog
from reminders.services.scheduler import (
    process_participant_decision,
    sync_reminders_for_meeting,
    dispatch_reminder_to_both_participants,
    cancel_reminders_for_meeting,
    hold_reminders_for_meeting,
)
from reminders.services.notification_service import (
    send_whatsapp_message,
    send_gmail_message,
    format_authorization_message,
    is_whatsapp_configured,
    is_gmail_configured,
)


class MeetFlowWorkflowTests(TestCase):
    """
    Comprehensive tests for MeetFlow Meeting Reminder and Authorization System.
    Tests all 7 critical scenarios and user requirements:
    1. Both participants accept -> Meeting confirmed -> WhatsApp & Gmail reminders activated.
    2. One participant accepts and the other is pending -> No reminders.
    3. One participant rejects -> Overall status rejected -> No reminders / cancelled.
    4. One participant requests rescheduling -> New timing proposed -> No reminders until both accept.
    5. Both participants accept revised timing -> Meeting confirmed -> Reminders activated.
    6. Duplicate clicks on authorization links -> Idempotent handling; no duplicate reminders.
    7. WhatsApp or Gmail integration unavailable -> Status recorded as NOT_CONFIGURED.
    """

    def setUp(self):
        self.client = Client()
        self.now = timezone.now()

        # Initialize global settings for WhatsApp & Gmail only
        self.settings = ReminderSetting.get_settings()
        self.settings.whatsapp_enabled = True
        self.settings.email_enabled = True
        self.settings.notify_participant1 = True
        self.settings.notify_participant2 = True
        self.settings.set_intervals([
            {"minutes": 15, "label": "15 minutes (Default)"},
            {"minutes": 60, "label": "1 hour"}
        ])
        self.settings.save()

        # Sample meeting fetched from external booking module
        self.meeting = Meeting.objects.create(
            booking_id="TEST-BK-501",
            p1_name="Dr. Jane Foster",
            p1_email="jane.foster@astrolab.org",
            p1_phone="+15551002000",
            p1_role="Host / Principal Investigator",
            p2_name="Thor Odinson",
            p2_email="thor.odinson@asgardcorp.com",
            p2_phone="+15553004000",
            p2_role="Client / Strategic Partner",
            purpose="Cosmic Waveform Synthesis Deep Dive",
            start_time=self.now + timedelta(days=2),
            duration_minutes=60,
            location="Google Meet (meet.google.com/test-sync)",
            p1_auth_status=Meeting.ParticipantAuth.PENDING,
            p2_auth_status=Meeting.ParticipantAuth.PENDING,
            overall_status=Meeting.OverallStatus.PENDING,
        )

    def test_scenario_1_both_participants_accept_confirms_meeting_and_activates_reminders(self):
        """
        Scenario 1: Both participants accept the meeting.
        - Overall status transitions to CONFIRMED.
        - WhatsApp and Gmail reminders are automatically activated.
        - Only WhatsApp and Email channels are scheduled (no GCAL, no SMS).
        """
        # Initially pending, no reminders
        self.assertEqual(self.meeting.overall_status, Meeting.OverallStatus.PENDING)
        self.assertFalse(self.meeting.can_trigger_reminders)
        self.assertEqual(ScheduledReminder.objects.filter(meeting=self.meeting).count(), 0)

        # Host accepts
        success1, msg1, self.meeting, role1 = process_participant_decision(
            meeting=self.meeting,
            token=self.meeting.p1_token,
            action="ACCEPT"
        )
        self.assertTrue(success1)
        self.meeting.refresh_from_db()
        self.assertEqual(self.meeting.p1_auth_status, Meeting.ParticipantAuth.ACCEPTED)
        self.assertEqual(self.meeting.p2_auth_status, Meeting.ParticipantAuth.PENDING)
        self.assertEqual(self.meeting.overall_status, Meeting.OverallStatus.PENDING)
        self.assertFalse(self.meeting.can_trigger_reminders)
        self.assertEqual(ScheduledReminder.objects.filter(meeting=self.meeting).count(), 0)

        # Client accepts
        success2, msg2, self.meeting, role2 = process_participant_decision(
            meeting=self.meeting,
            token=self.meeting.p2_token,
            action="ACCEPT"
        )
        self.assertTrue(success2)
        self.meeting.refresh_from_db()

        # Meeting is now fully CONFIRMED
        self.assertEqual(self.meeting.p1_auth_status, Meeting.ParticipantAuth.ACCEPTED)
        self.assertEqual(self.meeting.p2_auth_status, Meeting.ParticipantAuth.ACCEPTED)
        self.assertEqual(self.meeting.overall_status, Meeting.OverallStatus.CONFIRMED)
        self.assertTrue(self.meeting.can_trigger_reminders)

        # Reminders activated: 2 intervals * 2 channels (WHATSAPP, EMAIL) = 4 reminders
        scheduled = ScheduledReminder.objects.filter(
            meeting=self.meeting,
            status=ScheduledReminder.Status.SCHEDULED
        )
        self.assertEqual(scheduled.count(), 4)

        # Verify only WhatsApp and Email channels exist
        channels = set(scheduled.values_list('channel', flat=True))
        self.assertEqual(channels, {ScheduledReminder.Channel.WHATSAPP, ScheduledReminder.Channel.EMAIL})

    def test_scenario_2_one_accepts_one_pending_no_reminders(self):
        """
        Scenario 2: One participant accepts and the other is pending.
        - Overall status remains PENDING.
        - Reminders must NOT be triggered.
        """
        process_participant_decision(self.meeting, self.meeting.p1_token, "ACCEPT")
        self.meeting.refresh_from_db()

        self.assertEqual(self.meeting.p1_auth_status, Meeting.ParticipantAuth.ACCEPTED)
        self.assertEqual(self.meeting.p2_auth_status, Meeting.ParticipantAuth.PENDING)
        self.assertEqual(self.meeting.overall_status, Meeting.OverallStatus.PENDING)
        self.assertFalse(self.meeting.can_trigger_reminders)
        self.assertIn("On Hold", self.meeting.reminder_status)

        active_reminders = ScheduledReminder.objects.filter(
            meeting=self.meeting,
            status=ScheduledReminder.Status.SCHEDULED
        ).count()
        self.assertEqual(active_reminders, 0)

    def test_scenario_3_one_participant_rejects_marks_rejected_and_cancels_reminders(self):
        """
        Scenario 3: One participant rejects the meeting.
        - Overall status becomes REJECTED.
        - Reminders must not proceed, and any scheduled reminders must be cancelled.
        - Other participant is notified.
        """
        # First let both accept so reminders are created
        process_participant_decision(self.meeting, self.meeting.p1_token, "ACCEPT")
        process_participant_decision(self.meeting, self.meeting.p2_token, "ACCEPT")
        self.meeting.refresh_from_db()
        self.assertEqual(
            ScheduledReminder.objects.filter(meeting=self.meeting, status=ScheduledReminder.Status.SCHEDULED).count(),
            4
        )

        # Client rejects due to conflict
        success, msg, self.meeting, role = process_participant_decision(
            meeting=self.meeting,
            token=self.meeting.p2_token,
            action="REJECT",
            reason="Unresolvable calendar conflict with board meeting."
        )
        self.assertTrue(success)
        self.meeting.refresh_from_db()

        self.assertEqual(self.meeting.p2_auth_status, Meeting.ParticipantAuth.REJECTED)
        self.assertEqual(self.meeting.overall_status, Meeting.OverallStatus.REJECTED)
        self.assertFalse(self.meeting.can_trigger_reminders)
        self.assertEqual(self.meeting.reminder_status, "Cancelled")

        # Verify all active reminders were cancelled
        active_count = ScheduledReminder.objects.filter(
            meeting=self.meeting,
            status=ScheduledReminder.Status.SCHEDULED
        ).count()
        self.assertEqual(active_count, 0)

        cancelled_count = ScheduledReminder.objects.filter(
            meeting=self.meeting,
            status=ScheduledReminder.Status.CANCELLED
        ).count()
        self.assertEqual(cancelled_count, 4)

    def test_scenario_4_reschedule_requested_holds_reminders_until_both_confirm(self):
        """
        Scenario 4: One participant requests rescheduling.
        - Revised date/time is saved in database.
        - Overall status becomes RESCHEDULE_REQUESTED.
        - Reminders are held/cancelled until revised timing is confirmed by both.
        """
        # Both initially accepted
        process_participant_decision(self.meeting, self.meeting.p1_token, "ACCEPT")
        process_participant_decision(self.meeting, self.meeting.p2_token, "ACCEPT")
        self.meeting.refresh_from_db()

        # Host requests reschedule to a new date
        revised_time = self.now + timedelta(days=5, hours=3)
        success, msg, self.meeting, role = process_participant_decision(
            meeting=self.meeting,
            token=self.meeting.p1_token,
            action="RESCHEDULE",
            reason="Host has urgent symposium clash",
            new_datetime=revised_time
        )
        self.assertTrue(success)
        self.meeting.refresh_from_db()

        self.assertEqual(self.meeting.overall_status, Meeting.OverallStatus.RESCHEDULE_REQUESTED)
        self.assertEqual(self.meeting.rescheduled_date_time, revised_time)
        self.assertIn("symposium", self.meeting.reschedule_reason)
        self.assertFalse(self.meeting.can_trigger_reminders)

        # Host accepted the revised proposal, Client is reset to PENDING
        self.assertEqual(self.meeting.p1_auth_status, Meeting.ParticipantAuth.ACCEPTED)
        self.assertEqual(self.meeting.p2_auth_status, Meeting.ParticipantAuth.PENDING)

        # No active reminders running
        active_count = ScheduledReminder.objects.filter(
            meeting=self.meeting,
            status=ScheduledReminder.Status.SCHEDULED
        ).count()
        self.assertEqual(active_count, 0)

    def test_scenario_5_both_accept_revised_timing_confirms_meeting(self):
        """
        Scenario 5: Both participants confirm the revised rescheduled timing.
        - Meeting transitions back to CONFIRMED.
        - Reminders are reactivated.
        """
        revised_time = self.now + timedelta(days=4)
        process_participant_decision(
            self.meeting,
            self.meeting.p2_token,
            "RESCHEDULE",
            reason="Prefer Thursday",
            new_datetime=revised_time
        )
        self.meeting.refresh_from_db()
        self.assertEqual(self.meeting.overall_status, Meeting.OverallStatus.RESCHEDULE_REQUESTED)

        # Now Host accepts the revised schedule
        success, msg, self.meeting, role = process_participant_decision(
            meeting=self.meeting,
            token=self.meeting.p1_token,
            action="ACCEPT"
        )
        self.assertTrue(success)
        self.meeting.refresh_from_db()

        self.assertEqual(self.meeting.p1_auth_status, Meeting.ParticipantAuth.ACCEPTED)
        self.assertEqual(self.meeting.p2_auth_status, Meeting.ParticipantAuth.ACCEPTED)
        self.assertEqual(self.meeting.overall_status, Meeting.OverallStatus.CONFIRMED)
        self.assertTrue(self.meeting.can_trigger_reminders)

        # Reminders reactivated
        active_reminders = ScheduledReminder.objects.filter(
            meeting=self.meeting,
            status=ScheduledReminder.Status.SCHEDULED
        )
        self.assertEqual(active_reminders.count(), 4)

    def test_scenario_6_duplicate_clicks_prevent_duplicate_responses_and_reminders(self):
        """
        Scenario 6: Participant clicks Accept or Reject multiple times.
        - Handled idempotently with user-friendly feedback.
        - Does not create duplicate reminders or corrupt database state.
        """
        # Host accepts first time
        ok1, msg1, self.meeting, _ = process_participant_decision(self.meeting, self.meeting.p1_token, "ACCEPT")
        self.assertTrue(ok1)
        self.assertIn("recorded", msg1)

        # Host clicks accept a second time
        ok2, msg2, self.meeting, _ = process_participant_decision(self.meeting, self.meeting.p1_token, "ACCEPT")
        self.assertTrue(ok2)
        self.assertIn("already accepted", msg2)

        # Client accepts twice
        ok3, msg3, self.meeting, _ = process_participant_decision(self.meeting, self.meeting.p2_token, "ACCEPT")
        self.assertTrue(ok3)
        ok4, msg4, self.meeting, _ = process_participant_decision(self.meeting, self.meeting.p2_token, "ACCEPT")
        self.assertTrue(ok4)
        self.assertIn("already accepted", msg4)

        # Ensure reminder count is exactly 4 (not duplicated)
        reminders = ScheduledReminder.objects.filter(
            meeting=self.meeting,
            status=ScheduledReminder.Status.SCHEDULED
        )
        self.assertEqual(reminders.count(), 4)

    def test_scenario_7_unconfigured_credentials_recorded_as_not_configured(self):
        """
        Scenario 7: WhatsApp or Gmail integration credentials missing.
        - System records NOT_CONFIGURED instead of falsely claiming messages were sent.
        - Does not throw uncaught errors.
        """
        from reminders.services.notification_service import send_authorization_requests_to_both

        # Test WhatsApp helper with unconfigured environment
        if not is_whatsapp_configured():
            wa_ok, wa_msg = send_whatsapp_message("+15551234567", "Test reminder message")
            self.assertFalse(wa_ok)
            self.assertIn("NOT_CONFIGURED", wa_msg)

        # Test Gmail helper with unconfigured environment
        if not is_gmail_configured():
            gm_ok, gm_msg = send_gmail_message("test@example.com", "Test Subject", "Test Body")
            self.assertFalse(gm_ok)
            self.assertIn("NOT_CONFIGURED", gm_msg)

        # Test authorization requests dispatch to both participants records NOT_CONFIGURED in logs
        results = send_authorization_requests_to_both(self.meeting)
        self.assertEqual(len(results), 4)  # 2 participants * 2 channels

        unconfigured_logs = NotificationLog.objects.filter(
            meeting=self.meeting,
            status="NOT_CONFIGURED"
        )
        self.assertGreaterEqual(unconfigured_logs.count(), 2)

        # Ensure no fake DELIVERED statuses exist when credentials are missing
        if not is_whatsapp_configured() and not is_gmail_configured():
            fake_logs = NotificationLog.objects.filter(meeting=self.meeting, status="DELIVERED")
            self.assertEqual(fake_logs.count(), 0)

    def test_ui_and_endpoints_compliance(self):
        """
        Verify:
        - Dashboard (/) renders 200 with Total, Confirmed, Pending, Rejected.
        - All Meetings (/meetings/) renders 200 with participant columns.
        - Settings (/settings/) renders 200 with WhatsApp and Gmail only.
        - Obsolete /authorization/ and /accepted/ return 404.
        - Public token links work for Accept, Reject, Reschedule.
        """
        # 1. Overview Dashboard
        resp_overview = self.client.get('/')
        self.assertEqual(resp_overview.status_code, 200)
        self.assertContains(resp_overview, "Total Meetings")
        self.assertContains(resp_overview, "Confirmed Meetings")
        self.assertContains(resp_overview, "Pending Confirmations")
        self.assertContains(resp_overview, "Rejected Meetings")
        self.assertNotContains(resp_overview, "Meeting Authorization")
        self.assertNotContains(resp_overview, "Accepted Meetings")
        self.assertNotContains(resp_overview, "Google Calendar")

        # 2. All Meetings
        resp_meetings = self.client.get('/meetings/')
        self.assertEqual(resp_meetings.status_code, 200)
        self.assertContains(resp_meetings, "All Meetings")
        self.assertContains(resp_meetings, self.meeting.booking_id)
        self.assertContains(resp_meetings, "Host Status")
        self.assertContains(resp_meetings, "Client Status")
        self.assertContains(resp_meetings, "Overall Status")

        # 3. Reminder Settings
        resp_settings = self.client.get('/settings/')
        self.assertEqual(resp_settings.status_code, 200)
        self.assertContains(resp_settings, "Reminder Settings")
        self.assertContains(resp_settings, "WhatsApp")
        self.assertContains(resp_settings, "Gmail")
        self.assertNotContains(resp_settings, "Google Calendar")
        self.assertNotContains(resp_settings, "SMS Notifications")

        # 4. Old routes return 404
        resp_old_auth = self.client.get('/authorization/')
        self.assertEqual(resp_old_auth.status_code, 404)
        resp_old_acc = self.client.get('/accepted/')
        self.assertEqual(resp_old_acc.status_code, 404)

        # 5. Public Token Action Links
        token = self.meeting.p1_token
        # GET Accept
        resp_accept = self.client.get(f'/auth-action/{token}/accept/')
        self.assertEqual(resp_accept.status_code, 200)
        self.assertContains(resp_accept, "Meeting Accepted")

        # GET Reschedule form
        resp_reschedule_form = self.client.get(f'/auth-action/{token}/reschedule/')
        self.assertEqual(resp_reschedule_form.status_code, 200)
        self.assertContains(resp_reschedule_form, "Suggest New Meeting Timing")

        # POST Reschedule
        resp_reschedule_post = self.client.post(f'/auth-action/{token}/reschedule/', {
            'new_date': (timezone.now() + timedelta(days=3)).strftime('%Y-%m-%d'),
            'new_time': '14:30',
            'reason': 'Preferred afternoon timing slot',
        })
        self.assertEqual(resp_reschedule_post.status_code, 200)
        self.meeting.refresh_from_db()
        self.assertEqual(self.meeting.overall_status, Meeting.OverallStatus.RESCHEDULE_REQUESTED)

    def test_save_reminder_preferences_three_columns(self):
        """
        Verify the redesigned 3-column reminder settings saving:
        - Saves minutes, hours, days intervals
        - Updates active ScheduledReminder records for confirmed meetings
        """
        # Ensure meeting is confirmed so it receives reminders
        self.meeting.overall_status = Meeting.OverallStatus.CONFIRMED
        self.meeting.save()

        # Submit preferences with 15 min (col 1), 60 min (col 2), 1440 min (col 3)
        resp = self.client.post('/settings/save-preferences/', {
            'whatsapp_enabled': 'on',
            'email_enabled': 'on',
            'intervals': ['15', '60', '1440'],
            'custom_value': '30',
            'custom_unit': 'minutes'
        })
        self.assertEqual(resp.status_code, 302)
        
        settings = ReminderSetting.get_settings()
        self.assertTrue(settings.whatsapp_enabled)
        self.assertTrue(settings.email_enabled)

        saved_minutes = [item['minutes'] for item in settings.get_intervals()]
        self.assertIn(15, saved_minutes)
        self.assertIn(30, saved_minutes)
        self.assertIn(60, saved_minutes)
        self.assertIn(1440, saved_minutes)

        # Verify reminders synced for confirmed meeting: 4 intervals * 2 channels = 8 reminders
        reminders = ScheduledReminder.objects.filter(
            meeting=self.meeting,
            status=ScheduledReminder.Status.SCHEDULED
        )
        self.assertEqual(reminders.count(), 8)

    def test_dashboard_calendar_and_time_filters_context(self):
        """
        Verify dashboard provides interactive calendar JSON and time-based filtered subsets.
        """
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('meetings_json', resp.context)
        self.assertIn('confirmed_today', resp.context)
        self.assertIn('confirmed_tomorrow', resp.context)
        self.assertIn('confirmed_this_week', resp.context)
        self.assertIn('confirmed_this_month', resp.context)
        self.assertContains(resp, "Interactive Calendar")
        self.assertContains(resp, "Confirmed Meetings Schedule")
        self.assertContains(resp, "Pending Meeting Confirmations")
