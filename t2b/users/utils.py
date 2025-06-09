# utils.py
from datetime import timedelta
from django.utils.timezone import now
import requests
from .models import ZohoBooksCredential

def get_valid_zoho_access_token(user):
    creds = ZohoBooksCredential.objects.get(user=user)
    
    if creds.token_expires_at <= now():
        # Refresh token
        token_url = "https://accounts.zoho.com/oauth/v2/token"
        params = {
            "refresh_token": creds.refresh_token,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "grant_type": "refresh_token"
        }
        response = requests.post(token_url, params=params)
        if response.status_code != 200:
            raise Exception("Failed to refresh Zoho access token")
        
        token_data = response.json()
        creds.access_token = token_data['access_token']
        creds.token_expires_at = now() + timedelta(seconds=int(token_data['expires_in']))
        creds.save()
    
    return creds.access_token, creds.organization_id
