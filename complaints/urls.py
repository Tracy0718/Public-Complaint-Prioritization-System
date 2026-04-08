from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('submit/', views.submit_complaint, name='submit_complaint'),
    path('track/<uuid:pk>/', views.track_complaint, name='track_complaint'),
    path('edit/<uuid:pk>/', views.edit_complaint, name='edit_complaint'),
    path('history/', views.history, name='history'),
    path('dashboard/', views.user_dashboard, name='user_dashboard'),
    path('dashboard/', views.user_dashboard, name='dashboard'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    # Used a custom prefix instead of 'admin/' to avoid clashing with Django admin URLs
    path('admin-dashboard/complaint-action/', views.admin_complaint_action, name='admin_complaint_action'),
    path('complaint/delete/<uuid:pk>/', views.delete_complaint, name='delete_complaint'),
    path('api/complaints-data/', views.complaints_data_api, name='complaints_data_api'),
    path('api/user-complaints/', views.user_complaints_api, name='user_complaints_api'),
]
