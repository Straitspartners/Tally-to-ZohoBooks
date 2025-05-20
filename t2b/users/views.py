from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from .models import Ledger
from .serializers import LedgerSerializer
import requests

# Sync ledgers from Tally to Django
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sync_ledgers(request):
    """
    Sync ledgers from Tally agent. Supports: customers, vendors, coa, items.
    """
    total_synced = 0
    user = request.user
    data = request.data

    for key in ['customers', 'vendors', 'coa', 'items']:  # ✅ Added 'items'
        entries = data.get(key, [])
        if isinstance(entries, list):
            for entry in entries:
                if not entry.get('name'):
                    continue  # Skip invalid entries

                Ledger.objects.update_or_create(
                    user=user,
                    name=entry.get("name"),
                    defaults={
                        "parent": entry.get("parent", ""),
                        "phone": entry.get("phone", None),
                        "email": entry.get("email", None),
                        "ledger_type": key[:-1] if key != "coa" else "coa"  # e.g., 'customers' -> 'customer'
                    }
                )
                total_synced += 1

    if total_synced == 0:
        return Response({"error": "No valid ledgers provided."}, status=status.HTTP_400_BAD_REQUEST)

    return Response({"message": f"{total_synced} ledgers synced successfully."}, status=status.HTTP_200_OK)


# Optional: Send ledger data to Zoho Books
def send_to_zoho(ledger_data, access_token):
    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}"
    }
    url = "https://books.zoho.com/api/v3/chartofaccounts"
    payload = {
        "name": ledger_data.get("name"),
        "parent": ledger_data.get("parent", ""),
        "phone": ledger_data.get("phone", "0.00")
    }

    try:
        response = requests.post(url, headers=headers, data=payload)
        return response.status_code == 201
    except requests.exceptions.RequestException as e:
        print(f"Error sending data to Zoho Books: {e}")
        return False


# Sync data from Django to Zoho Books
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sync_to_zoho(request):
    ledgers = Ledger.objects.filter(user=request.user)
    zoho_access_token = 'YOUR_ZOHO_OAUTH_ACCESS_TOKEN'  # TODO: Replace this with real token

    success_count = 0
    failed_count = 0

    for ledger in ledgers:
        ledger_data = {
            "name": ledger.name,
            "parent": ledger.parent,
            "phone": ledger.phone
        }

        if send_to_zoho(ledger_data, zoho_access_token):
            success_count += 1
        else:
            failed_count += 1

    return Response({
        "message": f"Successfully synced {success_count} ledgers to Zoho Books. Failed: {failed_count}"
    }, status=status.HTTP_200_OK)


# Custom Auth Token
class CustomAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = serializer.validated_data['user']
            token, created = Token.objects.get_or_create(user=user)
            return Response({'token': token.key})
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)


# Installers :

# pip install requests

#for production 

# pip install pycopg2
# pip install psycopg2-binary
# pip install whitenoise