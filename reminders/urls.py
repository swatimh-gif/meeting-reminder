from django.urls import path
from reminders import views

urlpatterns = [
    # Dashboard & Consolidated List
    path('', views.overview, name='overview'),
    path('meetings/', views.meetings_list, name='meetings_list'),
    path('meetings/<int:pk>/', views.meeting_detail, name='meeting_detail'),
    path('meetings/<int:pk>/send-auth/', views.send_auth_requests_view, name='send_auth_requests'),

    # WhatsApp and Gmail Direct Authorization Action Links
    path('auth-action/<str:token>/reschedule/', views.reschedule_view, name='reschedule_action'),
    path('auth-action/<str:token>/<str:action>/', views.auth_action_view, name='auth_action'),

    # Reminder Settings (WhatsApp & Gmail only)
    path('settings/', views.settings_view, name='settings'),
    path('settings/save-preferences/', views.save_reminder_preferences, name='save_preferences'),
    path('settings/channels/', views.save_channel_settings, name='save_channels'),
    path('settings/add-interval/', views.add_timing_interval, name='add_interval'),
    path('settings/remove-interval/', views.remove_timing_interval, name='remove_interval'),

    # Integration Operations
    path('sync-booking-module/', views.sync_booking_module_view, name='sync_booking_module'),
    path('run-scheduler/', views.run_scheduler_view, name='run_scheduler'),
]
