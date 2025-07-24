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

    for item in items_data:
        account_obj = None
        account_code = item.get("account_code")
        if account_code:
            account_obj = Account.objects.filter(account_code=account_code).first()

        item_obj, _ = Item.objects.update_or_create(
            user=request.user,
            name=item.get("name"),
            defaults={
                "rate": item.get("rate", 0.0),
                "description": item.get("description", ""),
                "sku": item.get("sku", ""),
                "product_type": item.get("product_type", ""),
                "account": account_obj,
                "gst_applicable": item.get("gst_applicable", "Not Applicable"),
                "gst_rate": item.get("gst_rate", 0.0),
                "hsn_code": item.get("hsn_code", "")
            }
        )
        created.append(item_obj.name)

    return Response({
        "message": f"{len(created)} items synced successfully.",
        "items": created
    }, status=status.HTTP_200_OK)


# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def sync_invoices(request):
#     """
#     Accepts and stores invoice data from Tally.
#     """
    
#     invoice_data = request.data
#     if not invoice_data:
#         return Response({
#             "error": "No invoice data provided.",
#             "received_data": request.data  # helps debug what was received
#         }, status=400)

#     # Example debug print
#     print("Invoices received:", invoice_data)

#     serializer = InvoiceSerializer(data=invoice_data)
#     if serializer.is_valid():
#         # Create the invoice
#         invoice = Invoice.objects.create(
#             user=request.user,
#             customer_name=serializer.validated_data['customer_name'],
#             invoice_number=serializer.validated_data['invoice_number'],
#             invoice_date=serializer.validated_data['invoice_date'],
#             cgst=serializer.validated_data['cgst'],
#             sgst=serializer.validated_data['sgst'],
#             total_amount=serializer.validated_data['total_amount']
#         )

#         # Create the invoice items
#         for item in serializer.validated_data['items']:
#             InvoiceItem.objects.create(
#                 invoice=invoice,
#                 item_name=item['item_name'],
#                 quantity=item['quantity'],
#                 amount=item['amount']
#             )

#         return Response({"message": "Invoice saved successfully."}, status=201)

#     return Response(serializer.errors, status=400)

# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def sync_invoices(request):
#     """
#     Accepts and stores invoice data from Tally.
#     Supports multiple invoices in a single POST.
#     """
#     invoice_data = request.data.get("invoices", [])

#     if not invoice_data:
#         return Response({
#             "error": "No invoice data provided.",
#             "received_data": request.data
#         }, status=400)

#     for inv in invoice_data:
#         serializer = InvoiceSerializer(data=inv)
#         if serializer.is_valid():
#             invoice, created = Invoice.objects.update_or_create(
#                 user=request.user,
#                 customer_name=serializer.validated_data['customer_name'],
#                 invoice_number=serializer.validated_data['invoice_number'],
#                 invoice_date=serializer.validated_data['invoice_date'],
#                 total_amount=serializer.validated_data['total_amount']
#             )

#             # Delete existing items before creating new ones
#             invoice.items.all().delete()

#             for item in serializer.validated_data['items']:
#                 InvoiceItem.objects.create(
#                     invoice=invoice,
#                     item_name=item['item_name'],
#                     quantity=item['quantity'],
#                     amount=item['amount'],
#                     cgst=item.get('cgst', 0.0),
#                     sgst=item.get('sgst', 0.0),
#                     tax_type=item.get('tax_type', 'unknown')
#                 )
#         else:
#             return Response({
#                 "error": "Invalid invoice",
#                 "details": serializer.errors,
#                 "invoice": inv
#             }, status=400)

#     return Response({"message": "All invoices saved successfully."}, status=201)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sync_invoices(request):
    """
    Accepts and stores invoice data from Tally.
    Supports multiple invoices in a single POST.
    """
    invoice_data = request.data.get("invoices", [])

    if not invoice_data:
        return Response({
            "error": "No invoice data provided.",
            "received_data": request.data
        }, status=400)

    for inv in invoice_data:
        serializer = InvoiceSerializer(data=inv)
        if serializer.is_valid():
            # Unpack result here
            invoice, created = Invoice.objects.update_or_create(
                user=request.user,
                customer_name=serializer.validated_data['customer_name'],
                invoice_number=serializer.validated_data['invoice_number'],
                invoice_date=serializer.validated_data['invoice_date'],
                defaults={  # use 'defaults' for fields to update
                    'cgst': serializer.validated_data['cgst'],
                    'sgst': serializer.validated_data['sgst'],
                    'total_amount': serializer.validated_data['total_amount']
                }
            )

            for item in serializer.validated_data['items']:
                InvoiceItem.objects.get_or_create(
                    invoice=invoice,  # Now this is a proper Invoice instance
                    item_name=item['item_name'],
                    quantity=item['quantity'],
                    amount=item['amount']
                )
        else:
            return Response({
                "error": "Invalid invoice",
                "details": serializer.errors,
                "invoice": inv
            }, status=400)

    return Response({"message": "All invoices saved successfully."}, status=201)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sync_receipts(request):
    receipts_data = request.data.get("receipts", [])

    if not receipts_data:
        return Response({"error": "No receipt data provided."}, status=400)

    for entry in receipts_data:
        receipt_number = entry.get("receipt_number")
        customer_name = (entry.get("customer_name") or "").strip()
        receipt_date = entry.get("receipt_date")
        amount = entry.get("amount")
        payment_mode = entry.get("payment_mode", "").strip()
        agst_ref_name = entry.get("agst_ref_name", "").strip()

        if not all([receipt_number, customer_name, receipt_date, amount]):
            return Response({"error": f"Missing required fields in entry: {entry}"}, status=400)

        customer = Ledger.objects.filter(
            user=request.user,
            name__iexact=customer_name
        ).first()

        if not customer:
            return Response({
                "error": f"Customer '{customer_name}' not found in Ledger."
            }, status=404)

        invoice = None
        invoice_zoho_id = None
        invoice_total_amount = None

        if agst_ref_name:
            invoice = Invoice.objects.filter(
                user=request.user,
                invoice_number=agst_ref_name
            ).first()

            if invoice:
                invoice_zoho_id = invoice.zoho_invoice_id
                invoice_total_amount = invoice.total_amount

        receipt, created = Receipt.objects.update_or_create(
            user=request.user,
            receipt_number=receipt_number,
            defaults={
                "receipt_date": receipt_date,
                "amount": amount,
                "payment_mode": payment_mode,
                "customer": customer,
                "customer_zoho_id": customer.zoho_contact_id,
                "agst_invoice": invoice,
                "invoice_zoho_id": invoice_zoho_id,
                "invoice_total_amount": invoice_total_amount
            }
        )

    return Response({"message": "Receipts synced successfully."}, status=201)


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


#for agent
class CustomAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        if serializer.is_valid():
            user = serializer.validated_data['user']
            token, created = Token.objects.get_or_create(user=user)
            return Response({'token': token.key})
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)

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
from .models import ZohoTax

def push_taxes_to_zoho(user):
    access_token, org_id = get_valid_zoho_access_token(user)

    print("Access Token:", access_token)
    print("Org ID:", org_id)

    base_url = "https://www.zohoapis.com/books/v3"
    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "Content-Type": "application/json"
    }

    tax_definitions = [
        {"name": "GST18", "rate": 18.0},
        {"name": "GST0", "rate": 0.0},
        {"name": "GST12", "rate": 12.0},
        {"name": "GST28", "rate": 28.0},
        {"name": "GST5", "rate": 5.0},
    ]

    for tax in tax_definitions:
        tax_name = tax["name"]
        tax_rate = tax["rate"]

        # Check if the tax already exists in Zoho
        search_url = f"{base_url}/settings/taxes?organization_id={org_id}"
        search_response = requests.get(search_url, headers=headers)
        try:
            taxes_data = search_response.json()
        except ValueError:
            print(f"[Search Failed] Invalid JSON for tax: {tax_name}")
            continue

        # Skip if tax already exists
        if search_response.status_code == 200:
            existing_tax = next((t for t in taxes_data.get("taxes", []) if t["tax_name"] == tax_name), None)
            if existing_tax:
                print(f"[Skipped] Tax '{tax_name}' already exists in Zoho.")
                # Save tax_id to DB if not saved
                ZohoTax.objects.update_or_create(
                   
                    tax_name=tax_name,
                    defaults={"tax_percentage": tax_rate, "zoho_tax_id": existing_tax["tax_id"]}
                )
                continue

        # Create new tax
        payload = {
            "tax_name": tax_name,
            "tax_percentage": tax_rate,
            "tax_type": "tax"  # or "compound_tax" if applicable
        }

        response = requests.post(
            f"{base_url}/settings/taxes?organization_id={org_id}",
            headers=headers,
            json=payload
        )

        try:
            data = response.json()
        except ValueError:
            print(f"[Error] Invalid response when creating tax '{tax_name}'")
            continue

        if response.status_code == 201:
            zoho_tax_id = data["tax"]["tax_id"]
            print(f"[Success] Tax '{tax_name}' created in Zoho with ID: {zoho_tax_id}")
            # Save in local DB
            ZohoTax.objects.update_or_create(
                tax_name=tax_name,
                defaults={"tax_percentage": tax_rate, "zoho_tax_id": zoho_tax_id}
            )
        else:
            print(f"[Failed] Could not create tax '{tax_name}'. Status: {response.status_code}, Response: {data}")



import requests
from .models import Ledger

def push_customers_to_zoho(user):
    access_token, org_id = get_valid_zoho_access_token(user)

    print("Access Token:", access_token)
    print("Org ID:", org_id)

    ledgers = Ledger.objects.filter(user=user,zoho_contact_id__isnull=True)
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

            contact_id = response_data['contact']['contact_id']

            # ✅ Save Zoho contact ID locally
            ledger.zoho_contact_id = contact_id
            ledger.save(update_fields=["zoho_contact_id"])

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
            contact_id = response_data['contact']['contact_id']
            vendor.zoho_contact_id = contact_id
            vendor.save(update_fields=["zoho_contact_id"])
            print(f"[Success] Vendor {contact_name} pushed successfully.")
        else:
            print(f"[Failed] Vendor {contact_name} → Status: {response.status_code} | Response: {response_data}")


def get_or_create_zoho_tax(rate, access_token, org_id):
    headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}
    tax_url = f"https://www.zohoapis.com/books/v3/settings/taxes?organization_id={org_id}"

    # Check existing taxes
    resp = requests.get(tax_url, headers=headers)
    taxes = resp.json().get("taxes", [])
    for tax in taxes:
        if float(tax["tax_percentage"]) == float(rate):
            return tax["tax_id"]

    # Create new tax
    data = {"tax_name": f"GST {rate}%", "tax_percentage": rate}
    resp = requests.post(tax_url, headers=headers, json=data)
    if resp.status_code == 201:
        return resp.json()["tax"]["tax_id"]

    return None

# def push_items_to_zoho(user):
#     from .models import Item
#     access_token, org_id = get_valid_zoho_access_token(user)

#     items = Item.objects.filter(user=user)
#     url = f"https://www.zohoapis.com/books/v3/items?organization_id={org_id}"
#     headers = {
#         "Authorization": f"Zoho-oauthtoken {access_token}",
#         "Content-Type": "application/json"
#     }

#     for item in items:
#         data = {
#             "name": item.name,
#             "rate": float(item.rate),
#             "description": item.description or "",
#             "sku": item.sku or "",
#             "hsn_or_sac": item.hsn_code or "",
#             "product_type": "goods" if item.product_type.lower() != "service" else "service"
#         }

#         if item.gst_applicable.lower() == "applicable" and item.gst_rate > 0:
#             tax_id = get_or_create_zoho_tax(item.gst_rate, access_token, org_id)
#             if tax_id:
#                 data["tax_id"] = tax_id
#         else:
#             data["taxability"] = "non-taxable"

#         response = requests.post(url, headers=headers, json=data)
#         try:
#             response_data = response.json()
#         except Exception as e:
#             print(f"[Item Push Error] Invalid response for {item.name}: {e}")
#             continue

#         if response.status_code == 201:
#             print(f"[Success] {item.name} pushed successfully.")
#         else:
#             print(f"[Failed] {item.name} → {response_data}")
def push_items_to_zoho(user):
    from .models import Item, ZohoTax
    access_token, org_id = get_valid_zoho_access_token(user)

    items = Item.objects.filter(user=user)
    url = f"https://www.zohoapis.com/books/v3/items?organization_id={org_id}"
    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "Content-Type": "application/json"
    }

    for item in items:
        zoho_tax = ZohoTax.objects.filter(tax_percentage=item.gst_rate).first()
        data = {
            "name": item.name,
            "rate": float(item.rate),
            "description": item.description or "",
            "sku": item.sku or "",
            "hsn_or_sac": item.hsn_code or "",
            "product_type": "goods" if item.product_type.lower() != "service" else "service",
            "tax_id": zoho_tax.zoho_tax_id
            
        }
        
        response = requests.post(url, headers=headers, json=data)
        try:
            response_data = response.json()
        except Exception as e:
            print(f"[Item Push Error] Invalid response for {item.name}: {e}")
            continue

        if response.status_code == 201:
            print(f"[Success] {item.name} pushed successfully.")
        else:
            print(f"[Failed] {item.name} → {response_data}")

        


from .models import Invoice, InvoiceItem, ZohoBooksCredential
from .utils import get_valid_zoho_access_token
import requests
from django.utils.dateparse import parse_date


def push_invoices_to_zoho(user):
    access_token, org_id = get_valid_zoho_access_token(user)

    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "Content-Type": "application/json"
    }

    base_url = f"https://www.zohoapis.com/books/v3"
    invoices = Invoice.objects.filter(user=user, zoho_invoice_id__isnull=True)

    for invoice in invoices:
        # Step 1: Fetch contact_id from customer name
        contact_search_url = f"{base_url}/contacts"
        params = {
            "organization_id": org_id,
            "contact_name": invoice.customer_name
        }
        contact_res = requests.get(contact_search_url, headers=headers, params=params)
        contact_data = contact_res.json()

        if contact_res.status_code != 200 or not contact_data.get("contacts"):
            print(f"[ERROR] Customer '{invoice.customer_name}' not found in Zoho.")
            continue

        contact_id = contact_data['contacts'][0]['contact_id']

        # Step 2: Prepare line_items
        line_items = []
        for item in invoice.items.all():
            line_items.append({
                "name": item.item_name,
                "rate": float(item.amount),
                "quantity": 1,  # Optional: parse item.quantity if needed
                # "tax_id":6368368000000243025,
                # "tax_name": "CGST",
            })

        # Step 3: Prepare invoice payload
        payload = {
            "customer_id": contact_id,
            "invoice_number": invoice.invoice_number,
            "date": invoice.invoice_date.strftime('%Y-%m-%d'),
            "due_date": invoice.invoice_date.strftime('%Y-%m-%d'),
            "line_items": line_items,
            "cgst": float(invoice.cgst),
            "sgst": float(invoice.sgst),
            
            # Do NOT include "status": "sent" here — it is ignored
        }

        # Step 4: POST to Zoho Books
        invoice_url = f"{base_url}/invoices?organization_id={org_id}"
        response = requests.post(invoice_url, headers=headers, json=payload)

        try:
            data = response.json()
        except Exception as e:
            print(f"[ERROR] Invalid JSON for invoice {invoice.invoice_number}: {e}")
            continue

        if response.status_code == 201:
            print(f"[SUCCESS] Invoice {invoice.invoice_number} pushed to Zoho.")

            # Step 5: Mark invoice as sent to change status from "Draft" → "Sent"
            invoice_id = data['invoice']['invoice_id']

            # ✅ Save Zoho invoice ID in local DB
            invoice.zoho_invoice_id = invoice_id
            invoice.save(update_fields=["zoho_invoice_id"])

            mark_sent_url = f"{base_url}/invoices/{invoice_id}/status/sent?organization_id={org_id}"
            sent_response = requests.post(mark_sent_url, headers=headers)

            if sent_response.status_code == 200:
                print(f"[SUCCESS] Invoice {invoice.invoice_number} marked as sent.")
            else:
                print(f"[WARNING] Could not mark invoice {invoice.invoice_number} as sent → {sent_response.status_code}: {sent_response.text}")
        else:
            print(f"[FAILED] Invoice {invoice.invoice_number} → {response.status_code}: {data}")

import requests
from decimal import Decimal
import json


def push_receipts_to_zoho(user):
    access_token, org_id = get_valid_zoho_access_token(user)
    base_url = "https://www.zohoapis.com/books/v3"
    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "Content-Type": "application/json"
    }

    receipts = Receipt.objects.filter(user=user, zoho_receipt_id__isnull=True)

    for receipt in receipts:
        if not receipt.customer_zoho_id:
            print(f"[Skipped] Zoho ID missing for customer in receipt {receipt.receipt_number}")
            continue

        payload = {
            "customer_id": receipt.customer_zoho_id,
            "payment_mode": receipt.payment_mode.lower(),
            "amount": float(receipt.invoice_total_amount),
            "date": str(receipt.receipt_date)
        }

        if receipt.invoice_zoho_id:
            payload["invoices"] = [{
                "invoice_id": receipt.invoice_zoho_id,
                "amount_applied": float(receipt.amount)
            }]
        # 🔍 Print the payload
        print(f"\n📤 Payload for receipt {receipt.receipt_number}:")
        print(json.dumps(payload, indent=2))  # pretty print as JSON

        try:
            response = requests.post(
                f"{base_url}/customerpayments?organization_id={org_id}",
                headers=headers,
                json=payload
            )
            response_data = response.json()
        except Exception as e:
            print(f"[Error] Request failed for receipt {receipt.receipt_number}: {e}")
            continue

        if response.status_code == 201:
            response_data = response.json()
            print("🔍 Zoho HTTP Status:", response.status_code)
            print("🔍 Zoho Response JSON:")
            print(json.dumps(response_data, indent=2))
            zoho_payment_id = response_data["payment"]["payment_id"]
            receipt.zoho_receipt_id = zoho_payment_id
            receipt.save(update_fields=["zoho_receipt_id"])
            print(f"[✅ Success] Receipt {receipt.receipt_number} pushed to Zoho. ID: {zoho_payment_id}")
        else:
            print(f"[❌ Failed] Receipt {receipt.receipt_number} → {response.status_code} → {response_data}")
            

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def push_all_to_zoho(request):
    user = request.user
    try:
        # push_taxes_to_zoho(user)
        # push_customers_to_zoho(user)
        # push_vendors_to_zoho(user)
        # push_accounts_to_zoho(user)
        # push_items_to_zoho(user)
        # push_invoices_to_zoho(user)
        push_receipts_to_zoho(user)
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
