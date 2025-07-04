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
    

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sync_items(request):
    items_data = request.data.get("items", [])
    if not items_data:
        return Response({"error": "No items provided."}, status=status.HTTP_400_BAD_REQUEST)

    created = []
    errors = []

    for item in items_data:
        # Optional: resolve account by account_code if provided
        account_obj = None
        account_code = item.get("account_code")
        if account_code:
            account_obj = Account.objects.filter(account_code=account_code).first()

        item_obj, created_flag = Item.objects.update_or_create(
            user=request.user,
            name=item.get("name"),
            defaults={
                "rate": item.get("rate", 0.0),
                "description": item.get("description", ""),
                "sku": item.get("sku", ""),
                "product_type": item.get("product_type", ""),
                "account": account_obj
            }
        )
        created.append(item_obj.name)

    return Response({
        "message": f"{len(created)} items synced successfully.",
        "items": created
    }, status=status.HTTP_200_OK)


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



# class CustomAuthToken(ObtainAuthToken):
#     def post(self, request, *args, **kwargs):
#         serializer = self.serializer_class(data=request.data,
#                                            context={'request': request})
#         if serializer.is_valid():
#             user = serializer.validated_data['user']
#             token, created = Token.objects.get_or_create(user=user)
#             return Response({'token': token.key})
#         return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)

from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from django.contrib.auth import authenticate

class EmailOrUsernameAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        identifier = request.data.get('identifier')
        password = request.data.get('password')

        # Try email or username
        try:
            user_obj = User.objects.get(email=identifier)
            username = user_obj.username
        except User.DoesNotExist:
            username = identifier

        user = authenticate(username=username, password=password)
        if user is not None:
            token, created = Token.objects.get_or_create(user=user)
            return Response({'token': token.key, 'user': {'username': user.username, 'email': user.email}})
        return Response({'error': 'Invalid credentials'}, status=400)

# Installers :

# pip install requests

#for production 

# pip install pycopg2
# pip install psycopg2-binary
# pip install whitenoise

from .utils import get_valid_zoho_access_token


# def push_customers_to_zoho(user):
#     from .models import Ledger
#     access_token, org_id = get_valid_zoho_access_token(user)

#     # Debug print
#     print("Access Token:", access_token)
#     print("Org ID:", org_id)


#     ledgers = Ledger.objects.filter(user=user)
#     url = f"https://www.zohoapis.com/books/v3/contacts?organization_id={org_id}"
#     headers = {
#         "Authorization": f"Zoho-oauthtoken {access_token}",
#         "Content-Type": "application/json"
#     }

#     for ledger in ledgers:
#         data = {
#             "contact_name": ledger.name,
#             "company_name": ledger.name,
#             "email": ledger.email or f"{ledger.name.replace(' ', '').lower()}@exasdmple.com",
#             "billing_address": {
#                 "address": ledger.address or "",
#                 "zip": ledger.pincode or "",
#                 "state": ledger.state_name or "",
#                 "country": ledger.country_name or ""
#             },
#             "contact_persons": [
#                 {
#                     "first_name": ledger.name,
#                     "email": ledger.email or f"{ledger.name.replace(' ', '').lower()}@exdsample.com",
#                     # "email": ledger.email,
#                     "phone": ledger.ledger_mobile or "",
#                 }
#             ]
#         }

#         r = requests.post(url, headers=headers, json=data)
#         print(f"[Customer] {ledger.name} → {r.status_code}", r.json())

import requests
from .models import Ledger

def push_customers_to_zoho(user):
    access_token, org_id = get_valid_zoho_access_token(user)

    print("Access Token:", access_token)
    print("Org ID:", org_id)

    ledgers = Ledger.objects.filter(user=user)
    base_url = "https://www.zohoapis.com/books/v3"
    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "Content-Type": "application/json"
    }

    for ledger in ledgers:
        email = ledger.email or f"{ledger.name.replace(' ', '').lower()}@example.com"
        contact_name = ledger.name

        # Check if contact already exists
        search_url = f"{base_url}/contacts?organization_id={org_id}&email={email}"
        search_response = requests.get(search_url, headers=headers)
        try:
            search_data = search_response.json()
        except ValueError:
            print(f"[Search Failed] Invalid JSON while searching {contact_name}")
            continue

        if search_response.status_code == 200 and search_data.get("contacts"):
            print(f"[Skipped] {contact_name} already exists in Zoho Books.")
            continue

        data = {
            "contact_name": contact_name,
            "company_name": contact_name,
            "email": email,
            "phone": ledger.ledger_mobile or "",
            "billing_address": {
                "address": ledger.address or "",
                "zip": ledger.pincode or "",
                "state": ledger.state_name or "",
                "country": ledger.country_name or ""
            },
            "contact_persons": [
                {
                    "first_name": contact_name,
                    "email": email,
                    "phone": ledger.ledger_mobile or ""
                }
            ],
            # Optional fields you can add if available:
            # "website": ledger.website or "",
            # "gst_treatment": "business_gst" or "consumer",  # depends on country
            # "place_of_contact": ledger.state_name or ""
        }

        try:
            response = requests.post(
                f"{base_url}/contacts?organization_id={org_id}",
                headers=headers,
                json=data
            )
            response_data = response.json()
        except ValueError:
            print(f"[Error] Invalid response for {contact_name}")
            continue

        if response.status_code == 201:
            print(f"[Success] {contact_name} pushed successfully.")
        else:
            print(f"[Failed] {contact_name} → Status: {response.status_code} | Response: {response_data}")




def push_accounts_to_zoho(user):
    from .models import Account
    access_token, org_id = get_valid_zoho_access_token(user)

    # Debug print
    print("Access Token:", access_token)
    print("Org ID:", org_id)

    accounts = Account.objects.all()
    url = f"https://www.zohoapis.com/books/v3/chartofaccounts?organization_id={org_id}"
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
        response_data = r.json()
        print(f"[Zoho Response] {response_data}")

        if r.status_code == 201:  # Successfully created
            zoho_account_id = response_data['chart_of_account']['account_id']
            account.zoho_account_id = zoho_account_id  # assumes your model has this field
            account.save()
            print(f"[Account] {account.account_name} → Created in Zoho with ID {zoho_account_id}")
        else:
            print(f"[Error] Failed to create {account.account_name} →", response_data)

# def push_vendors_to_zoho(user):
#     from .models import Vendor
#     import requests

#     access_token, org_id = get_valid_zoho_access_token(user)
#     print("Access Token:", access_token)
#     print("Org ID:", org_id)

#     vendors = Vendor.objects.filter(user=user)
#     url = "https://www.zohoapis.com/books/v3/contacts"
#     headers = {
#         "Authorization": f"Zoho-oauthtoken {access_token}",
#         "Content-Type": "application/json"
#     }
#     params = {
#         "organization_id": org_id
#     }

#     for vendor in vendors:
#         data = {
#             "contact_type": "vendor",  # Specify contact type as vendor
#             "contact_name": vendor.name,
#             "vendor_name": vendor.name,
#             "email": vendor.email or f"{vendor.name.replace(' ', '').lower()}@example.com",
#             "billing_address": {
#                 "address": vendor.address or "",
#                 "zip": vendor.pincode or "",
#                 "state": vendor.state_name or "",
#                 "country": vendor.country_name or ""
#             },
#             "phone": vendor.ledger_mobile or ""
#         }

#         r = requests.post(url, headers=headers, params=params, json=data)
#         print(f"[Vendor] {vendor.name} → {r.status_code}", r.json())

def push_vendors_to_zoho(user):
    from .models import Vendor
    import requests

    access_token, org_id = get_valid_zoho_access_token(user)
    print("Access Token:", access_token)
    print("Org ID:", org_id)

    vendors = Vendor.objects.filter(user=user)
    base_url = "https://www.zohoapis.com/books/v3"
    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "Content-Type": "application/json"
    }

    for vendor in vendors:
        email = vendor.email.strip() if vendor.email and vendor.email.strip() else f"{vendor.name.replace(' ', '').lower()}@example.com"
        print(f"Resolved Email for {vendor.name}: {email}")
        contact_name = vendor.name

        # Check if the vendor already exists in Zoho Books
        search_url = f"{base_url}/contacts"
        search_params = {
            "organization_id": org_id,
            "email": email
        }

        try:
            search_response = requests.get(search_url, headers=headers, params=search_params)
            search_data = search_response.json()
        except ValueError:
            print(f"[Search Failed] Invalid JSON while searching vendor {contact_name}")
            continue

        if search_response.status_code == 200 and search_data.get("contacts"):
            print(f"[Skipped] Vendor {contact_name} already exists in Zoho Books.")
            continue

        # Prepare vendor data
        data = {
            "contact_type": "vendor",
            "contact_name": contact_name,
            "vendor_name": contact_name,
            "email": email,
            "phone": vendor.ledger_mobile or "",
            "billing_address": {
                "address": vendor.address or "",
                "zip": vendor.pincode or "",
                "state": vendor.state_name or "",
                "country": vendor.country_name or ""
            }
        }

        # Push to Zoho Books
        try:
            response = requests.post(
                f"{base_url}/contacts",
                headers=headers,
                params={"organization_id": org_id},
                json=data
            )
            response_data = response.json()
        except ValueError:
            print(f"[Error] Invalid response while pushing vendor {contact_name}")
            continue

        if response.status_code == 201:
            print(f"[Success] Vendor {contact_name} pushed successfully.")
        else:
            print(f"[Failed] Vendor {contact_name} → Status: {response.status_code} | Response: {response_data}")

def push_items_to_zoho(user):
    from .models import Item
    access_token, org_id = get_valid_zoho_access_token(user)

    print("Access Token:", access_token)
    print("Org ID:", org_id)

    items = Item.objects.filter(user=user)
    url = f"https://www.zohoapis.com/books/v3/items?organization_id={org_id}"
    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "Content-Type": "application/json"
    }

    for item in items:
        data = {
            "name": item.name,
            "rate": float(item.rate),
            "description": item.description or "",
            "sku": item.sku or "",
            # "product_type": item.product_type or "goods",  # Must be 'goods' or 'service'
        }

        # Optionally map account to Zoho "account_id"
        if item.account:
            # Here you can extend logic to fetch and map Zoho account_id if needed
            data["account_id"] = None  # Optional field if you sync Zoho account IDs

        response = requests.post(url, headers=headers, json=data)
        try:
            response_data = response.json()
        except Exception as e:
            print(f"[Item Push Error] Invalid response for {item.name}: {e}")
            continue

        if response.status_code == 201:
            print(f"[Success] {item.name} pushed successfully.")
        else:
            print(f"[Failed] {item.name} → Status: {response.status_code} | Response: {response_data}")


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def push_all_to_zoho(request):
    user = request.user
    try:
        push_customers_to_zoho(user)
        push_vendors_to_zoho(user)
        push_accounts_to_zoho(user)
        push_items_to_zoho(user)
        return Response({"message": "Data pushed to Zoho Books successfully."})
    except Exception as e:
        return Response({"error": str(e)}, status=500)


## Signup,Sigin,Forgot Password

from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils.encoding import smart_bytes, smart_str, DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.core.mail import send_mail
from .tokens import account_activation_token
from .serializers import *

class RegisterView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"msg": "User created"}, status=201)
        return Response(serializer.errors, status=400)

class LoginView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        identifier = serializer.validated_data['identifier']
        password = serializer.validated_data['password']
        user = User.objects.filter(email=identifier).first() or User.objects.filter(username=identifier).first()
        if user is None or not user.check_password(password):
            return Response({"error": "Invalid credentials"}, status=400)
        token = RefreshToken.for_user(user)
        return Response({
            'refresh': str(token),
            'access': str(token.access_token),
        })

class RequestPasswordResetEmail(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = ResetPasswordEmailRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = User.objects.filter(email=email).first()
            if user:
                uidb64 = urlsafe_base64_encode(smart_bytes(user.id))
                token = account_activation_token.make_token(user)
                reset_link = f"http://localhost:3000/password-reset/{uidb64}/{token}"
                send_mail(
                    "Password Reset",
                    f"Click link to reset password: {reset_link}",
                    "noreply@example.com",
                    [email],
                )
            return Response({"msg": "Check your email if account exists."})
        return Response(serializer.errors, status=400)

class PasswordTokenCheckAPI(APIView):
    permission_classes = [AllowAny]
    def get(self, request, uidb64, token):
        try:
            user_id = smart_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(id=user_id)
            if not account_activation_token.check_token(user, token):
                return Response({"error": "Invalid token"}, status=401)
            return Response({"success": True, "uidb64": uidb64, "token": token})
        except Exception:
            return Response({"error": "Token check failed"}, status=400)

class SetNewPasswordAPIView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = SetNewPasswordSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user_id = smart_str(urlsafe_base64_decode(serializer.validated_data['uidb64']))
                user = User.objects.get(id=user_id)
                if not account_activation_token.check_token(user, serializer.validated_data['token']):
                    return Response({"error": "Invalid token"}, status=401)
                user.set_password(serializer.validated_data['password'])
                user.save()
                return Response({"msg": "Password reset successful"})
            except DjangoUnicodeDecodeError:
                return Response({"error": "Invalid decode"}, status=400)
        return Response(serializer.errors, status=400)
