from django.urls import path
from . import views
from .views import *
# urlpatterns = [
#     path("sync-ledgers/", sync_ledgers, name="sync_ledgers"),
# ]
urlpatterns = [
    path('users/ledgers/', views.sync_ledgers, name='sync_ledgers'),  # Sync ledgers from Tally
    path('users/to-zoho/', views.sync_to_zoho, name='sync_to_zoho'),  # Sync ledgers to Zoho Books
    path('generate_token/', CustomAuthToken.as_view(), name='generate_token'), 
    path('users/vendors/', views.sync_vendors, name='sync_vendors'),
    path('users/accounts/', AccountSyncView.as_view(), name='account-sync'),
]