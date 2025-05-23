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

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
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


# Endpoint for syncing ledger data to Zoho Books (Optional)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sync_to_zoho(request):
    """
    Syncs the ledgers from the Django database to Zoho Books.
    """
    # Fetch all ledgers associated with the authenticated user
    ledgers = Ledger.objects.filter(user=request.user)

    # Assuming the Zoho Books API access token is stored in the environment
    zoho_access_token = 'YOUR_ZOHO_OAUTH_ACCESS_TOKEN'  # Replace with dynamic token management

    success_count = 0
    failed_count = 0

    # Iterate over each ledger and push it to Zoho Books
    for ledger in ledgers:
        ledger_data = {
            "name": ledger.name,
            "parent": ledger.parent,
            "phone": ledger.phone
        }

        # Send to Zoho
        if send_to_zoho(ledger_data, zoho_access_token):
            success_count += 1
        else:
            failed_count += 1

    # Return a summary response
    return Response({
        "message": f"Successfully synced {success_count} ledgers to Zoho Books. Failed to sync {failed_count} ledgers."
    }, status=status.HTTP_200_OK)



from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework import status

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