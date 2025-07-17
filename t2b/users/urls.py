from django.urls import path
from . import views
from .views import *
# urlpatterns = [
#     path("sync-ledgers/", sync_ledgers, name="sync_ledgers"),
# ]
urlpatterns = [
    
    path('users/ledgers/', views.sync_ledgers, name='sync_ledgers'),  # Sync ledgers from Tally
    path('generate_token_agent/', CustomAuthToken.as_view(), name='generate_token_agent'), 
    path('generate_token/', EmailOrUsernameAuthToken.as_view(), name='generate_token'), 
    path('users/vendors/', views.sync_vendors, name='sync_vendors'),
    path('users/items/', views.sync_items, name='sync_items'),
    path('users/accounts/', AccountSyncView.as_view(), name='account-sync'),
    path('users/invoices/push-to-zoho/', views.push_invoices_to_zoho, name='push_invoice_to_zoho'),
    path('users/invoices/', views.sync_invoices, name='sync_invoices'),
    path('users/connect-zoho/', views.connect_zoho_books, name='connect_zoho_books'),
    path('users/push-to-zoho/', views.push_all_to_zoho, name='push_all_to_zoho'),
    path('register/', RegisterView.as_view()),
    path('login/', LoginView.as_view()),
    path('request-reset-email/', RequestPasswordResetEmail.as_view()),
    path('password-reset/<uidb64>/<token>/', PasswordTokenCheckAPI.as_view()),
    path('password-reset-complete/', SetNewPasswordAPIView.as_view()),

]

