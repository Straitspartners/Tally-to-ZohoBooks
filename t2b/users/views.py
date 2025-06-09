from django.shortcuts import render

# Create your views here.
# from rest_framework.decorators import api_view, permission_classes
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.response import Response
# from .serializers import LedgerSerializer
# from .models import Ledger

# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def sync_ledgers(request):
#     ledgers = request.data.get("ledgers", [])
#     for entry in ledgers:
#         Ledger.objects.update_or_create(
#             user=request.user,
#             name=entry.get("name"),
#             defaults={
#                 "parent": entry.get("parent"),
#                 "phone": entry.get("phone")
#             }
#         )
#     return Response({"message": f"{len(ledgers)} ledgers synced successfully."})

from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status,permissions
from .models import *
from .serializers import *
import requests

# Sync ledgers from Tally to Django
@api_view(['POST'])
@permission_classes([IsAuthenticated])  # Only authenticated users can access
def sync_ledgers(request):
    """
    This endpoint accepts data from the Tally sync agent and stores the ledger information in the database.
    Expected data: 
    {
        "ledgers": [
            {"name": "Ledger Name", "parent": "Parent Group", "phone": "1000.00"},
            {"name": "Another Ledger", "parent": "Another Group", "phone": "2000.00"}
        ]
    }
    """
    # Data should come in a list under the "ledgers" key
    ledgers = request.data.get("ledgers", [])

    # If no ledgers are sent in the request, return an error
    if not ledgers:
        return Response({"error": "No ledgers provided in the request."}, status=status.HTTP_400_BAD_REQUEST)

    # Process each ledger
    for entry in ledgers:
        # Check if required fields are present
        if not entry.get('name'):
            return Response({"error": "Ledger name is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Update or create the ledger in the database
        Ledger.objects.update_or_create(
            user=request.user,  # Link the ledger to the authenticated user
            name=entry.get("name"),
            # defaults={
            #      "parent": entry.get("parent", ""),
            #      "phone": entry.get("phone", None),
            #      "email": entry.get("email", None),
            #      "address": entry.get("address", None) 
            # }
            defaults = {
    "parent": entry.get("parent", ""),
    "email": entry.get("email", None),
    "address": entry.get("address", None),
    "ledger_mobile": entry.get("ledger_mobile", None),
    "website": entry.get("website", None),
    "state_name": entry.get("state_name", None),
    "country_name": entry.get("country_name", None),
    "pincode": entry.get("pincode", None),
}

        )

    # Return a success message
    return Response({"message": f"{len(ledgers)} ledgers synced successfully."}, status=status.HTTP_200_OK)


# views.py (add below sync_ledgers)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sync_vendors(request):
    """
    Accepts and stores vendor information in the database.
    Endpoint: /api/users/ledgers/vendors/
    """
    vendors = request.data.get("ledgers", [])

    if not vendors:
        return Response({"error": "No vendors provided in the request."}, status=status.HTTP_400_BAD_REQUEST)

    for entry in vendors:
        if not entry.get('name'):
            return Response({"error": "Vendor name is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Update or create vendor
        Vendor.objects.update_or_create(
            user=request.user,
            name=entry.get("name"),
            defaults={
                "parent": entry.get("parent", ""),
                "email": entry.get("email", None),
                "address": entry.get("address", None),
                "ledger_mobile": entry.get("ledger_mobile", None),
                "website": entry.get("website", None),
                "state_name": entry.get("state_name", None),
                "country_name": entry.get("country_name", None),
                "pincode": entry.get("pincode", None),
            }
        )

    return Response({"message": f"{len(vendors)} vendors synced successfully."}, status=status.HTTP_200_OK)

from rest_framework.views import APIView
class AccountSyncView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        accounts_data = request.data.get("accounts", [])
        created = []
        errors = []

        for account_data in accounts_data:
            serializer = AccountSerializer(data=account_data)
            if serializer.is_valid():
                # Avoid duplicates using account_code
                obj, created_flag = Account.objects.update_or_create(
                    account_code=account_data["account_code"],
                    defaults=serializer.validated_data
                )
                created.append(obj.account_code)
            else:
                errors.append(serializer.errors)

        return Response({
            "created": created,
            "errors": errors
        }, status=status.HTTP_201_CREATED if not errors else status.HTTP_207_MULTI_STATUS)

# Send the data to Zoho Books (Optional: Example function)
def send_to_zoho(ledger_data, access_token):
    """
    Sends the ledger data to Zoho Books using Zoho's API.
    """

    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}"  # Zoho API authentication header
    }

    # Zoho Books API endpoint to create chart of accounts
    url = "https://books.zoho.com/api/v3/chartofaccounts"

    payload = {
        "name": ledger_data.get("name"),
        "parent": ledger_data.get("parent", ""),
        "phone": ledger_data.get("phone", "0.00")
    }

    try:
        # Sending the data to Zoho Books API
        response = requests.post(url, headers=headers, data=payload)
        if response.status_code == 201:
            return True
        else:
            return False
    except requests.exceptions.RequestException as e:
        print(f"Error sending data to Zoho Books: {e}")
        return False


from django.utils.timezone import now, timedelta
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import ZohoBooksCredential
import requests

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def connect_zoho_books(request):
    """
    Save Zoho Books credentials, refresh access token and validate connection.
    """
    user = request.user
    data = request.data

    required_fields = ["client_id", "client_secret", "refresh_token", "organization_id"]
    if not all(field in data for field in required_fields):
        return Response({"error": "Missing one or more required fields."}, status=400)

    # Attempt to get a new access token
    token_url = "https://accounts.zoho.com/oauth/v2/token"
    params = {
        "refresh_token": data["refresh_token"],
        "client_id": data["client_id"],
        "client_secret": data["client_secret"],
        "grant_type": "refresh_token"
    }

    token_response = requests.post(token_url, params=params)
    if token_response.status_code != 200:
        return Response({"error": "Failed to connect to Zoho.", "details": token_response.json()}, status=400)

    token_data = token_response.json()
    access_token = token_data["access_token"]
    expires_in = int(token_data.get("expires_in", 3600))

    # Save or update credentials
    ZohoBooksCredential.objects.update_or_create(
        user=user,
        defaults={
            "client_id": data["client_id"],
            "client_secret": data["client_secret"],
            "refresh_token": data["refresh_token"],
            "access_token": access_token,
            "token_expires_at": now() + timedelta(seconds=expires_in),
            "organization_id": data["organization_id"]
        }
    )

    # Optional: Validate connection by calling a basic Zoho Books API
    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}"
    }
    test_url = f"https://books.zoho.com/api/v3/organizations?organization_id={data['organization_id']}"
    test_response = requests.get(test_url, headers=headers)

    if test_response.status_code == 200:
        return Response({"message": "Connected to Zoho Books successfully."})
    else:
        return Response({"error": "Failed to verify Zoho Books connection.", "details": test_response.json()}, status=400)



class CustomAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
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

from .utils import get_valid_zoho_access_token


def push_customers_to_zoho(user):
    from .models import Ledger
    access_token, org_id = get_valid_zoho_access_token(user)

    ledgers = Ledger.objects.filter(user=user)
    url = f"https://books.zoho.com/api/v3/customers?organization_id={org_id}"
    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}"
    }

    for ledger in ledgers:
        data = {
            "contact_name": ledger.name,
            "company_name": ledger.name,
            "email": ledger.email,
            "billing_address": {
                "address": ledger.address or "",
                "zip": ledger.pincode or "",
                "state": ledger.state_name or "",
                "country": ledger.country_name or ""
            },
            "contact_persons": [
                {
                    "first_name": ledger.name,
                    "email": ledger.email,
                    "phone": ledger.ledger_mobile or "",
                }
            ]
        }

        r = requests.post(url, headers=headers, json=data)
        print(f"[Customer] {ledger.name} → {r.status_code}", r.json())

def push_vendors_to_zoho(user):
    from .models import Vendor
    access_token, org_id = get_valid_zoho_access_token(user)

    vendors = Vendor.objects.filter(user=user)
    url = f"https://books.zoho.com/api/v3/vendors?organization_id={org_id}"
    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}"
    }

    for vendor in vendors:
        data = {
            "vendor_name": vendor.name,
            "email": vendor.email,
            "billing_address": {
                "address": vendor.address or "",
                "zip": vendor.pincode or "",
                "state": vendor.state_name or "",
                "country": vendor.country_name or ""
            },
            "phone": vendor.ledger_mobile or ""
        }

        r = requests.post(url, headers=headers, json=data)
        print(f"[Vendor] {vendor.name} → {r.status_code}", r.json())

def push_accounts_to_zoho(user):
    from .models import Account
    access_token, org_id = get_valid_zoho_access_token(user)

    accounts = Account.objects.all()
    url = f"https://books.zoho.com/api/v3/chartofaccounts?organization_id={org_id}"
    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}"
    }

    for account in accounts:
        data = {
            "account_name": account.account_name,
            "account_type": account.account_type,
            "account_code": account.account_code
        }

        r = requests.post(url, headers=headers, json=data)
        print(f"[Account] {account.account_name} → {r.status_code}", r.json())

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def push_all_to_zoho(request):
    user = request.user
    try:
        push_customers_to_zoho(user)
        push_vendors_to_zoho(user)
        push_accounts_to_zoho(user)
        return Response({"message": "Data pushed to Zoho Books successfully."})
    except Exception as e:
        return Response({"error": str(e)}, status=500)

