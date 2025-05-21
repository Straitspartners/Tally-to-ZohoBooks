from django.urls import path
from . import views
from .views import CustomAuthToken

urlpatterns = [
    path('generate_token/', CustomAuthToken.as_view(), name='generate_token'),
    path('users/customers/', views.sync_customers, name='sync_customers'),
    path('users/vendors/', views.sync_vendors, name='sync_vendors'),
]
