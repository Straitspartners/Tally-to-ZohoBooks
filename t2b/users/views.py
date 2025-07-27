from django.shortcuts import render
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

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sync_ledgers(request):
    ledgers = request.data.get("ledgers", [])
    if not ledgers:
        return Response({"error": "No ledgers provided in the request."}, status=status.HTTP_400_BAD_REQUEST)

    synced_count = 0
    for entry in ledgers:
        name = entry.get('name')
        if not name:
            continue  # skip entries without a name

        # Check for existing ledger
        ledger_qs = Ledger.objects.filter(user=request.user, name=name)
        if ledger_qs.exists():
            ledger = ledger_qs.first()
            if not ledger.fetched_from_tally:
                # Update only if not yet fetched
                ledger.parent = entry.get("parent", "")
                ledger.email = entry.get("email", None)
                ledger.address = entry.get("address", None)
                ledger.ledger_mobile = entry.get("ledger_mobile", None)
                ledger.website = entry.get("website", None)
                ledger.state_name = entry.get("state_name", None)
                ledger.country_name = entry.get("country_name", None)
                ledger.pincode = entry.get("pincode", None)
                ledger.fetched_from_tally = True
                ledger.save()
                synced_count += 1
            # else, already fetched, skip
        else:
            # Create new ledger and mark as fetched
            Ledger.objects.create(
                user=request.user,
                name=name,
                parent=entry.get("parent", ""),
                email=entry.get("email", None),
                address=entry.get("address", None),
                ledger_mobile=entry.get("ledger_mobile", None),
                website=entry.get("website", None),
                state_name=entry.get("state_name", None),
                country_name=entry.get("country_name", None),
                pincode=entry.get("pincode", None),
                fetched_from_tally=True
            )
            synced_count += 1

    return Response({"message": f"{synced_count} ledgers synced successfully."}, status=status.HTTP_200_OK)


# views.py (add below sync_ledgers)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sync_vendors(request):
    vendors = request.data.get("ledgers", [])
    if not vendors:
        return Response({"error": "No vendors provided in the request."}, status=status.HTTP_400_BAD_REQUEST)

    synced_count = 0
    for entry in vendors:
        name = entry.get('name')
        if not name:
            continue

        vendor_qs = Vendor.objects.filter(user=request.user, name=name)
        if vendor_qs.exists():
            vendor = vendor_qs.first()
            if not vendor.fetched_from_tally:
                vendor.parent = entry.get("parent", "")
                vendor.email = entry.get("email", None)
                vendor.address = entry.get("address", None)
                vendor.ledger_mobile = entry.get("ledger_mobile", None)
                vendor.website = entry.get("website", None)
                vendor.state_name = entry.get("state_name", None)
                vendor.country_name = entry.get("country_name", None)
                vendor.pincode = entry.get("pincode", None)
                vendor.fetched_from_tally = True
                vendor.save()
                synced_count += 1
        else:
            Vendor.objects.create(
                user=request.user,
                name=name,
                parent=entry.get("parent", ""),
                email=entry.get("email", None),
                address=entry.get("address", None),
                ledger_mobile=entry.get("ledger_mobile", None),
                website=entry.get("website", None),
                state_name=entry.get("state_name", None),
                country_name=entry.get("country_name", None),
                pincode=entry.get("pincode", None),
                fetched_from_tally=True
            )
            synced_count += 1

    return Response({"message": f"{synced_count} vendors synced successfully."}, status=status.HTTP_200_OK)

from rest_framework import permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Account
from .serializers import AccountSerializer

class AccountSyncView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        accounts_data = request.data.get("accounts", [])
        created = []
        errors = []

        for account_data in accounts_data:
            serializer = AccountSerializer(data=account_data)
            if serializer.is_valid():
                account_code = account_data.get("account_code")
                if not account_code:
                    errors.append({"error": "Missing account_code in data", "data": account_data})
                    continue

                # Check for existing account with account_code
                try:
                    account_obj = Account.objects.get(user=request.user, account_code=account_code)
                    # Update only if not yet fetched from tally
                    if not account_obj.fetched_from_tally:
                        # Update fields with validated data
                        for attr, value in serializer.validated_data.items():
                            setattr(account_obj, attr, value)
                        account_obj.fetched_from_tally = True
                        account_obj.save()
                        created.append(account_obj.account_code)
                    else:
                        # Already fetched, skip update
                        pass
                except Account.DoesNotExist:
                    # Create new if not exists
                    account_obj = Account.objects.create(
                        user=request.user,
                        account_name=serializer.validated_data.get("account_name", ""),
                        account_code=serializer.validated_data.get("account_code", ""),
                        account_type=serializer.validated_data.get("account_type", ""),
                        zoho_account_id=serializer.validated_data.get("zoho_account_id", ""),
                        fetched_from_tally=True
                    )
                    created.append(account_obj.account_code)
            else:
                errors.append(serializer.errors)

        return Response({
            "created": created,
            "errors": errors
        }, status=status.HTTP_201_CREATED if not errors else status.HTTP_207_MULTI_STATUS)

    

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sync_items(request):
    items = request.data.get("items", [])
    if not items:
        return Response({"error": "No items provided."}, status=status.HTTP_400_BAD_REQUEST)

    synced_items = []

    for item in items:
        name = item.get("name")
        account_code = item.get("account_code")

        # Find existing Item by name for the user
        item_qs = Item.objects.filter(user=request.user, name=name)
        if item_qs.exists():
            item_obj = item_qs.first()
            if not item_obj.fetched_from_tally:
                # Update only if not yet fetched
                account_obj = None
                if account_code:
                    account_obj = Account.objects.filter(user=request.user, account_code=account_code).first()
                item_obj.rate = item.get("rate", 0.0)
                item_obj.description = item.get("description", "")
                item_obj.sku = item.get("sku", "")
                item_obj.product_type = item.get("product_type", "")
                item_obj.account = account_obj
                item_obj.gst_applicable = item.get("gst_applicable", "Not Applicable")
                item_obj.gst_rate = item.get("gst_rate", 0.0)
                item_obj.hsn_code = item.get("hsn_code", "")
                # Keep fetched_from_tally True after initial fetch
                item_obj.fetched_from_tally = True
                item_obj.save()
                synced_items.append(item_obj.name)
            # else, already fetched, skip
        else:
            # Create new item
            account_obj = None
            if account_code:
                account_obj = Account.objects.filter(user=request.user, account_code=account_code).first()
            item_obj = Item.objects.create(
                user=request.user,
                name=name,
                rate=item.get("rate", 0.0),
                description=item.get("description", ""),
                sku=item.get("sku", ""),
                product_type=item.get("product_type", ""),
                account=account_obj,
                gst_applicable=item.get("gst_applicable", "Not Applicable"),
                gst_rate=item.get("gst_rate", 0.0),
                hsn_code=item.get("hsn_code", ""),
                fetched_from_tally=True
            )
            synced_items.append(item_obj.name)

    return Response({
        "message": f"{len(synced_items)} items synced successfully.",
        "items": synced_items
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sync_invoices(request):
    invoices_data = request.data.get("invoices", [])
    if not invoices_data:
        return Response({"error": "No invoice data provided."}, status=status.HTTP_400_BAD_REQUEST)

    saved_invoices = []

    for inv in invoices_data:
        serializer = InvoiceSerializer(data=inv)
        if serializer.is_valid():
            invoice_qs = Invoice.objects.filter(
                user=request.user,
                invoice_number=serializer.validated_data['invoice_number']
            )
            if invoice_qs.exists():
                invoice = invoice_qs.first()
                if not invoice.fetched_from_tally:
                    # Update existing invoice
                    invoice.customer_name = serializer.validated_data['customer_name']
                    invoice.invoice_date = serializer.validated_data['invoice_date']
                    invoice.cgst = serializer.validated_data['cgst']
                    invoice.sgst = serializer.validated_data['sgst']
                    invoice.total_amount = serializer.validated_data['total_amount']
                    invoice.fetched_from_tally = True
                    invoice.save()
            else:
                # Create new invoice
                invoice = Invoice.objects.create(
                    user=request.user,
                    customer_name=serializer.validated_data['customer_name'],
                    invoice_number=serializer.validated_data['invoice_number'],
                    invoice_date=serializer.validated_data['invoice_date'],
                    cgst=serializer.validated_data['cgst'],
                    sgst=serializer.validated_data['sgst'],
                    total_amount=serializer.validated_data['total_amount'],
                    fetched_from_tally=True
                )
            # Save invoice items
            for item in serializer.validated_data['items']:
                InvoiceItem.objects.get_or_create(
                    invoice=invoice,
                    item_name=item['item_name'],
                    quantity=item['quantity'],
                    amount=item['amount'],
                    defaults={'fetched_from_tally': True}
                )
            if invoice.fetched_from_tally:
                saved_invoices.append(invoice.invoice_number)
        else:
            return Response({
                "error": "Invalid invoice",
                "details": serializer.errors,
                "invoice": inv
            }, status=status.HTTP_400_BAD_REQUEST)

    return Response({"message": f"{len(saved_invoices)} invoices synced successfully."}, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sync_receipts(request):
    receipts_data = request.data.get("receipts", [])
    if not receipts_data:
        return Response({"error": "No receipt data provided."}, status=status.HTTP_400_BAD_REQUEST)

    synced_count = 0
    processed_receipts = []

    for entry in receipts_data:
        receipt_number = entry.get("receipt_number")
        customer_name = (entry.get("customer_name") or "").strip()
        receipt_date = entry.get("receipt_date")
        amount = entry.get("amount")
        payment_mode = entry.get("payment_mode", "").strip()
        agst_ref_name = entry.get("agst_ref_name", "").strip()

        # Validate required fields
        if not all([receipt_number, customer_name, receipt_date, amount]):
            continue  # skip invalid entries

        # Check if customer (Ledger) exists
        customer = Ledger.objects.filter(
            user=request.user,
            name__iexact=customer_name
        ).first()
        if not customer:
            continue  # skip if customer not found

        invoice = None
        invoice_zoho_id = None
        invoice_total_amount = None

        if agst_ref_name:
            # Find related invoice
            invoice = Invoice.objects.filter(
                user=request.user,
                invoice_number=agst_ref_name
            ).first()
            if invoice:
                invoice_zoho_id = invoice.zoho_invoice_id
                invoice_total_amount = invoice.total_amount

        # Check if receipt already exists
        receipt_qs = Receipt.objects.filter(
            user=request.user,
            receipt_number=receipt_number
        )

        if receipt_qs.exists():
            receipt = receipt_qs.first()
            if not receipt.fetched_from_tally:
                # Update existing Receipt
                receipt.receipt_date = receipt_date
                receipt.amount = amount
                receipt.payment_mode = payment_mode
                receipt.customer = customer
                # receipt.customer_zoho_id = customer.zoho_contact_id
                receipt.agst_invoice = invoice
                # receipt.invoice_zoho_id = invoice_zoho_id
                # receipt.invoice_total_amount = invoice_total_amount
                receipt.fetched_from_tally = True
                receipt.save()
                synced_count += 1
        else:
            # Create new receipt
            Receipt.objects.create(
                user=request.user,
                receipt_number=receipt_number,
                receipt_date=receipt_date,
                amount=amount,
                payment_mode=payment_mode,
                customer=customer,
                # customer_zoho_id=customer.zoho_contact_id,
                agst_invoice=invoice,
                # invoice_zoho_id=invoice_zoho_id,
                # invoice_total_amount=invoice_total_amount,
                fetched_from_tally=True
            )
            synced_count += 1
        processed_receipts.append(receipt_number)

    return Response({"message": f"{synced_count} receipts synced successfully."}, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sync_purchases(request):
    purchases_data = request.data.get("purchases", [])
    if not purchases_data:
        return Response({"error": "No purchase data provided."}, status=status.HTTP_400_BAD_REQUEST)

    saved_purchases = []

    for pur in purchases_data:
        serializer = PurchaseSerializer(data=pur)
        if serializer.is_valid():
            purchase_qs = Purchase.objects.filter(
                user=request.user,
                purchase_number=serializer.validated_data['purchase_number']
            )
            if purchase_qs.exists():
                purchase = purchase_qs.first()
                if not purchase.fetched_from_tally:
                    purchase.vendor_name = serializer.validated_data['vendor_name']
                    purchase.purchase_date = serializer.validated_data['purchase_date']
                    purchase.purchase_ledger = serializer.validated_data['purchase_ledger']
                    purchase.cgst = serializer.validated_data['cgst']
                    purchase.sgst = serializer.validated_data['sgst']
                    purchase.total_amount = serializer.validated_data['total_amount']
                    purchase.fetched_from_tally = True
                    purchase.save()
            else:
                purchase = Purchase.objects.create(
                    user=request.user,
                    vendor_name=serializer.validated_data['vendor_name'],
                    purchase_number=serializer.validated_data['purchase_number'],
                    purchase_date=serializer.validated_data['purchase_date'],
                    purchase_ledger=serializer.validated_data['purchase_ledger'],
                    cgst=serializer.validated_data['cgst'],
                    sgst=serializer.validated_data['sgst'],
                    total_amount=serializer.validated_data['total_amount'],
                    fetched_from_tally=True
                )
            # Save items
            for item in serializer.validated_data['items']:
                PurchaseItem.objects.get_or_create(
                    purchase=purchase,
                    item_name=item['item_name'],
                    quantity=item['quantity'],
                    amount=item['amount'],
                    defaults={'fetched_from_tally': True}
                )
            saved_purchases.append(purchase.purchase_number)
        else:
            return Response({
                "error": "Invalid purchase",
                "details": serializer.errors,
                "purchase": pur
            }, status=status.HTTP_400_BAD_REQUEST)

    return Response({"message": f"{len(saved_purchases)} purchases synced successfully."}, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sync_payments(request):
    payments_data = request.data.get("payments", [])
    if not payments_data:
        return Response({"error": "No payment data provided."}, status=status.HTTP_400_BAD_REQUEST)

    synced_count = 0
    processed_payments = []

    for entry in payments_data:
        payment_number = entry.get("payment_number")
        vendor_name = (entry.get("vendor_name") or "").strip()
        payment_date = entry.get("payment_date")
        amount = entry.get("amount")
        payment_mode = entry.get("payment_mode", "").strip()
        agst_ref_name = entry.get("agst_ref_name", "").strip()

        if not all([payment_number, vendor_name, payment_date, amount]):
            continue  # skip invalid entries

        vendor = Vendor.objects.filter(user=request.user, name__iexact=vendor_name).first()
        if not vendor:
            print(f"❌ Vendor not found: '{vendor_name}' for user {request.user}")
            continue  # skip if vendor not found

        invoice = None
        invoice_zoho_id = None
        invoice_total_amount = None

        if agst_ref_name:
            invoice = Invoice.objects.filter(user=request.user, invoice_number=agst_ref_name).first()
            if invoice:
                invoice_zoho_id = invoice.zoho_invoice_id
                invoice_total_amount = invoice.total_amount

        payment_qs = Payment.objects.filter(user=request.user, payment_number=payment_number)
        if payment_qs.exists():
            payment = payment_qs.first()
            if not payment.fetched_from_tally:
                payment.payment_date = payment_date
                payment.amount = amount
                payment.payment_mode = payment_mode
                payment.vendor = vendor
                payment.agst_invoice = invoice
                payment.fetched_from_tally = True
                payment.save()
                synced_count += 1
        else:
            Payment.objects.create(
                user=request.user,
                payment_number=payment_number,
                payment_date=payment_date,
                amount=amount,
                payment_mode=payment_mode,
                vendor=vendor,
                agst_invoice=invoice,
                fetched_from_tally=True
            )
            synced_count += 1

        processed_payments.append(payment_number)

    return Response({"message": f"{synced_count} payments synced successfully."}, status=status.HTTP_201_CREATED)

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
                    defaults={"tax_percentage": tax_rate, "zoho_tax_id": existing_tax["tax_id"],"pushed_to_zoho": True}
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

    ledgers = Ledger.objects.filter(user=user,zoho_contact_id__isnull=True, pushed_to_zoho=False)
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
            ledger.pushed_to_zoho = True
            ledger.save(update_fields=["zoho_contact_id", "pushed_to_zoho"])

        else:
            print(f"[Failed] {contact_name} → Status: {response.status_code} | Response: {response_data}")


def push_accounts_to_zoho(user):
    from .models import Account
    access_token, org_id = get_valid_zoho_access_token(user)

    # Debug print
    print("Access Token:", access_token)
    print("Org ID:", org_id)

    accounts = Account.objects.filter(pushed_to_zoho=False)
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
            account.pushed_to_zoho = True
            account.save(update_fields=["zoho_account_id", "pushed_to_zoho"])
            print(f"[Account] {account.account_name} → Created in Zoho with ID {zoho_account_id}")
        else:
            print(f"[Error] Failed to create {account.account_name} →", response_data)


def push_vendors_to_zoho(user):
    from .models import Vendor
    import requests

    access_token, org_id = get_valid_zoho_access_token(user)
    print("Access Token:", access_token)
    print("Org ID:", org_id)

    vendors = Vendor.objects.filter(user=user,pushed_to_zoho=False)
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
            vendor.pushed_to_zoho = True
            vendor.save(update_fields=["zoho_contact_id", "pushed_to_zoho"])
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

    items = Item.objects.filter(user=user,pushed_to_zoho=False)
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
            item.pushed_to_zoho = True
            item.save(update_fields=["pushed_to_zoho"])
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
    invoices = Invoice.objects.filter(user=user, zoho_invoice_id__isnull=True,pushed_to_zoho=False)

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
            invoice.pushed_to_zoho = True
            invoice.save(update_fields=["zoho_invoice_id", "pushed_to_zoho"])

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


# def push_receipts_to_zoho(user):
#     access_token, org_id = get_valid_zoho_access_token(user)
#     base_url = "https://www.zohoapis.com/books/v3"
#     headers = {
#         "Authorization": f"Zoho-oauthtoken {access_token}",
#         "Content-Type": "application/json"
#     }

#     receipts = Receipt.objects.filter(user=user, zoho_receipt_id__isnull=True,pushed_to_zoho=False)

#     for receipt in receipts:
#         if not receipt.customer_zoho_id:
#             print(f"[Skipped] Zoho ID missing for customer in receipt {receipt.receipt_number}")
#             continue

#         payload = {
#             "customer_id": receipt.customer_zoho_id,
#             "payment_mode": receipt.payment_mode.lower(),
#             "amount": float(receipt.invoice_total_amount),
#             "date": str(receipt.receipt_date)
#         }

#         if receipt.invoice_zoho_id:
#             payload["invoices"] = [{
#                 "invoice_id": receipt.invoice_zoho_id,
#                 "amount_applied": float(receipt.amount)
#             }]
#         # 🔍 Print the payload
#         print(f"\n📤 Payload for receipt {receipt.receipt_number}:")
#         print(json.dumps(payload, indent=2))  # pretty print as JSON

#         try:
#             response = requests.post(
#                 f"{base_url}/customerpayments?organization_id={org_id}",
#                 headers=headers,
#                 json=payload
#             )
#             response_data = response.json()
#         except Exception as e:
#             print(f"[Error] Request failed for receipt {receipt.receipt_number}: {e}")
#             continue

#         if response.status_code == 201:
#             response_data = response.json()
#             print("🔍 Zoho HTTP Status:", response.status_code)
#             print("🔍 Zoho Response JSON:")
#             print(json.dumps(response_data, indent=2))
#             zoho_payment_id = response_data["payment"]["payment_id"]
#             receipt.zoho_receipt_id = zoho_payment_id
#             receipt.pushed_to_zoho = True
#             receipt.save(update_fields=["zoho_receipt_id", "pushed_to_zoho"])
#             print(f"[✅ Success] Receipt {receipt.receipt_number} pushed to Zoho. ID: {zoho_payment_id}")
#         else:
#             print(f"[❌ Failed] Receipt {receipt.receipt_number} → {response.status_code} → {response_data}")

def push_receipts_to_zoho(user):
    access_token, org_id = get_valid_zoho_access_token(user)
    base_url = "https://www.zohoapis.com/books/v3"
    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "Content-Type": "application/json"
    }

    receipts = Receipt.objects.filter(user=user, zoho_receipt_id__isnull=True, pushed_to_zoho=False)

    for receipt in receipts:
        customer = receipt.customer
        invoice = receipt.agst_invoice

        if not customer or not customer.zoho_contact_id:
            print(f"[Skipped] Missing Zoho ID for customer {customer} in receipt {receipt.receipt_number}")
            continue

        customer_zoho_id = customer.zoho_contact_id
        invoice_zoho_id = invoice.zoho_invoice_id if invoice else None
        invoice_total_amount = invoice.total_amount if invoice else None

        # 🔄 Update the receipt record with Zoho IDs before pushing
        receipt.customer_zoho_id = customer_zoho_id
        receipt.invoice_zoho_id = invoice_zoho_id
        receipt.invoice_total_amount = invoice_total_amount
        receipt.save(update_fields=["customer_zoho_id", "invoice_zoho_id", "invoice_total_amount"])

        payload = {
            "customer_id": customer_zoho_id,
            "payment_mode": receipt.payment_mode.lower(),
            "amount": float(invoice_total_amount or receipt.amount),
            "date": str(receipt.receipt_date)
        }

        if invoice_zoho_id:
            payload["invoices"] = [{
                "invoice_id": invoice_zoho_id,
                "amount_applied": float(receipt.amount)
            }]

        print(f"\n📤 Payload for receipt {receipt.receipt_number}:")
        print(json.dumps(payload, indent=2))

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
            zoho_payment_id = response_data["payment"]["payment_id"]
            receipt.zoho_receipt_id = zoho_payment_id
            receipt.pushed_to_zoho = True
            receipt.save(update_fields=["zoho_receipt_id", "pushed_to_zoho"])
            print(f"[✅ Success] Receipt {receipt.receipt_number} pushed to Zoho. ID: {zoho_payment_id}")
        else:
            print(f"[❌ Failed] Receipt {receipt.receipt_number} → {response.status_code} → {response_data}")




# def push_purchases_to_zoho(user):
#     access_token, org_id = get_valid_zoho_access_token(user)

#     headers = {
#         "Authorization": f"Zoho-oauthtoken {access_token}",
#         "Content-Type": "application/json"
#     }

#     base_url = f"https://www.zohoapis.com/books/v3"
#     purchases = Purchase.objects.filter(user=user, zoho_bill_id__isnull=True, pushed_to_zoho=False)

#     for purchase in purchases:
#         # Step 1: Find vendor
#         contact_url = f"{base_url}/contacts"
#         params = {
#             "organization_id": org_id,
#             "contact_name": purchase.vendor_name
#         }
#         res = requests.get(contact_url, headers=headers, params=params)
#         data = res.json()

#         if res.status_code != 200 or not data.get("contacts"):
#             print(f"[ERROR] Vendor '{purchase.vendor_name}' not found in Zoho.")
#             continue

#         contact_id = data['contacts'][0]['contact_id']

#         # Step 2: Prepare line_items
#         line_items = []
#         for item in purchase.items.all():
#             if not item.account or not item.account.zoho_account_id:
#                 print(f"[WARNING] Item '{item.item_name}' has no linked Zoho account. Skipping.")
#                 continue
#             line_items.append({
#                 "name": item.item_name,
#                 "rate": float(item.amount),
#                 "quantity": 1,
#                 "account_id": item.account.zoho_account_id
#             })

#         payload = {
#             "vendor_id": contact_id,
#             "bill_number": purchase.purchase_number,
#             "date": purchase.purchase_date.strftime('%Y-%m-%d'),
#             "line_items": line_items,
#         }

#         # Step 3: Create bill
#         bill_url = f"{base_url}/bills?organization_id={org_id}"
#         response = requests.post(bill_url, headers=headers, json=payload)

#         try:
#             result = response.json()
#         except:
#             print(f"[ERROR] Invalid response for bill {purchase.purchase_number}")
#             continue

#         if response.status_code == 201:
#             zoho_bill_id = result['bill']['bill_id']
#             purchase.zoho_bill_id = zoho_bill_id
#             purchase.pushed_to_zoho = True
#             purchase.save(update_fields=["zoho_bill_id", "pushed_to_zoho"])
#             print(f"[SUCCESS] Purchase {purchase.purchase_number} pushed to Zoho.")
#         else:
#             print(f"[FAILED] Purchase {purchase.purchase_number} → {response.status_code}: {result}")
def push_purchases_to_zoho(user):
    access_token, org_id = get_valid_zoho_access_token(user)

    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "Content-Type": "application/json"
    }

    base_url = f"https://www.zohoapis.com/books/v3"
    purchases = Purchase.objects.filter(user=user, zoho_bill_id__isnull=True, pushed_to_zoho=False)

    for purchase in purchases:
        # Step 1: Find vendor
        contact_url = f"{base_url}/contacts"
        params = {
            "organization_id": org_id,
            "contact_name": purchase.vendor_name
        }
        res = requests.get(contact_url, headers=headers, params=params)
        data = res.json()

        if res.status_code != 200 or not data.get("contacts"):
            print(f"[ERROR] Vendor '{purchase.vendor_name}' not found in Zoho.")
            continue

        contact_id = data['contacts'][0]['contact_id']

        # Step 2: Match purchase ledger to Account
        try:
            account = Account.objects.get(user=user, account_name__iexact=purchase.purchase_ledger)
            zoho_account_id = account.zoho_account_id
        except Account.DoesNotExist:
            print(f"[ERROR] No matching Account for ledger '{purchase.purchase_ledger}'")
            continue

        # Step 3: Prepare line_items
        line_items = []
        for item in purchase.items.all():
            line_items.append({
                "name": item.item_name,
                "rate": float(item.amount),
                "quantity": 1,
                "account_id": zoho_account_id
            })

        payload = {
            "vendor_id": contact_id,
            "bill_number": purchase.purchase_number,
            "date": purchase.purchase_date.strftime('%Y-%m-%d'),
            "line_items": line_items,
        }

        # Step 4: Create bill
        bill_url = f"{base_url}/bills?organization_id={org_id}"
        response = requests.post(bill_url, headers=headers, json=payload)

        try:
            result = response.json()
        except:
            print(f"[ERROR] Invalid response for bill {purchase.purchase_number}")
            continue

        if response.status_code == 201:
            zoho_bill_id = result['bill']['bill_id']
            purchase.zoho_bill_id = zoho_bill_id
            purchase.pushed_to_zoho = True
            purchase.save(update_fields=["zoho_bill_id", "pushed_to_zoho"])
            print(f"[SUCCESS] Purchase {purchase.purchase_number} pushed to Zoho.")
        else:
            print(f"[FAILED] Purchase {purchase.purchase_number} → {response.status_code}: {result}")

# def push_payments_to_zoho(user):
#     access_token, org_id = get_valid_zoho_access_token(user)
#     base_url = "https://www.zohoapis.com/books/v3"
#     headers = {
#         "Authorization": f"Zoho-oauthtoken {access_token}",
#         "Content-Type": "application/json"
#     }

#     payments = Payment.objects.filter(user=user, zoho_payment_id__isnull=True, pushed_to_zoho=False)

#     for payment in payments:
#         vendor = payment.vendor
#         invoice = payment.agst_invoice

#         if not vendor or not vendor.zoho_contact_id:
#             print(f"[Skipped] Missing Zoho ID for vendor {vendor} in payment {payment.payment_number}")
#             continue

#         payload = {
#             "vendor_id": vendor.zoho_contact_id,
#             "payment_mode": payment.payment_mode.lower(),
#             "amount": float(payment.amount),
#             "date": str(payment.payment_date)
#         }

#         if invoice:
#             payload["invoices"] = [{
#                 "invoice_id": invoice.zoho_invoice_id,
#                 "amount_applied": float(payment.amount)
#             }]

#         try:
#             response = requests.post(
#                 f"{base_url}/vendorpayments?organization_id={org_id}",
#                 headers=headers,
#                 json=payload
#             )
#             data = response.json()
#             if response.status_code == 201:
#                 zoho_payment_id = data["payment"]["payment_id"]
#                 payment.zoho_payment_id = zoho_payment_id
#                 payment.pushed_to_zoho = True
#                 payment.save(update_fields=["zoho_payment_id", "pushed_to_zoho"])
#                 print(f"[✅ Success] Payment {payment.payment_number} pushed to Zoho.")
#             else:
#                 print(f"[❌ Failed] Payment {payment.payment_number}: {data}")
#         except Exception as e:
#             print(f"[Error] Failed to push payment {payment.payment_number}: {e}")
def push_payments_to_zoho(user):
    access_token, org_id = get_valid_zoho_access_token(user)
    base_url = "https://www.zohoapis.com/books/v3"
    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "Content-Type": "application/json"
    }

    payments = Payment.objects.filter(user=user, zoho_payment_id__isnull=True, pushed_to_zoho=False)

    for payment in payments:
        vendor = payment.vendor
        purchase = payment.agst_invoice

        if not vendor or not vendor.zoho_contact_id:
            print(f"[Skipped] Missing Zoho contact ID for vendor in payment {payment.payment_number}")
            continue

        # 🔍 Find Zoho account ID using payment_mode from Account table
        try:
            account = Account.objects.get(user=user, account_name__iexact=payment.payment_mode.strip())
            account_id = account.zoho_account_id
            if not account_id:
                print(f"[ERROR] Missing zoho_account_id for Account: '{account.account_name}'")
                continue
        except Account.DoesNotExist:
            print(f"[ERROR] No matching Account found for payment_mode: '{payment.payment_mode}'")
            continue

        # 🧾 Construct payload
        payload = {
            "vendor_id": vendor.zoho_contact_id,
            "payment_mode": payment.payment_mode,
            "amount": float(payment.amount),
            "date": str(payment.payment_date),
            # "description": f"Payment for invoice {invoice.invoice_number if invoice else 'N/A'}",
            "account_id": account_id
        }

        if purchase and purchase.zoho_bill_id:
            payload["bills"] = [{
                "bill_id": purchase.zoho_bill_id,
                "amount_applied": float(payment.amount)
            }]

        # 🚀 Send to Zoho
        try:
            response = requests.post(
                f"{base_url}/vendorpayments?organization_id={org_id}",
                headers=headers,
                json=payload
            )
            data = response.json()

            if ("payment" in data or "vendorpayment" in data) and "payment_id" in data.get("vendorpayment", {}):
                   zoho_payment_id = data["vendorpayment"]["payment_id"]
                   payment.zoho_payment_id = zoho_payment_id
                   payment.pushed_to_zoho = True
                   payment.save(update_fields=["zoho_payment_id", "pushed_to_zoho"])
                   print(f"[✅ Success] Payment {payment.payment_number} pushed to Zoho.")
            else:
                print(f"[❌ Failed] Payment {payment.payment_number}: {data}")
        except Exception as e:
            print(f"[Error] Failed to push payment {payment.payment_number}: {e}")


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
        # push_receipts_to_zoho(user)
        push_purchases_to_zoho(user)
        push_payments_to_zoho(user)
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


#Quick Migrations Masters count
class TotalRecordsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        total_ledgers = Ledger.objects.filter(user=user).count()
        total_vendors = Vendor.objects.filter(user=user).count()
        total_accounts = Account.objects.filter(user=user).count()
        total_items = Item.objects.filter(user=user).count()

        total_records = total_ledgers + total_vendors + total_accounts + total_items

        total_sales_voucher = Invoice.objects.filter(user=user).count()
        total_receipts = Receipt.objects.filter(user=user).count()

        total_records_trans = total_sales_voucher + total_receipts 

        return Response({
            "ledgers": total_ledgers,
            "vendors": total_vendors,
            "accounts": total_accounts,
            "items": total_items,
            "total": total_records,
            "total_trans": total_records_trans
        })


#For the Main Dashboard
class DataMigrationStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # Totals for fetched from Tally
        tally_ledgers = Ledger.objects.filter(user=user, fetched_from_tally=True).count()
        tally_vendors = Vendor.objects.filter(user=user, fetched_from_tally=True).count()
        tally_accounts = Account.objects.filter(user=user, fetched_from_tally=True).count()
        tally_items = Item.objects.filter(user=user, fetched_from_tally=True).count()
        tally_invoices=Invoice.objects.filter(user=user,fetched_from_tally=True).count()
        tally_receipts=Receipt.objects.filter(user=user,fetched_from_tally=True).count()

        # Totals for pushed to Zoho
        zoho_ledgers = Ledger.objects.filter(user=user, pushed_to_zoho=True).count()
        zoho_vendors = Vendor.objects.filter(user=user, pushed_to_zoho=True).count()
        zoho_accounts = Account.objects.filter(user=user, pushed_to_zoho=True).count()
        zoho_items = Item.objects.filter(user=user, pushed_to_zoho=True).count()
        zoho_invoices=Invoice.objects.filter(user=user,pushed_to_zoho=True).count()
        zoho_receipts=Receipt.objects.filter(user=user,pushed_to_zoho=True).count()

        # Pending Zoho Migration
        pending_ledgers = Ledger.objects.filter(user=user, pushed_to_zoho=False).count()
        pending_vendors = Vendor.objects.filter(user=user, pushed_to_zoho=False).count()
        pending_accounts = Account.objects.filter(user=user, pushed_to_zoho=False).count()
        pending_items = Item.objects.filter(user=user, pushed_to_zoho=False).count()
        pending_invoices=Invoice.objects.filter(user=user,pushed_to_zoho=False).count()
        pending_receipts=Receipt.objects.filter(user=user,pushed_to_zoho=False).count()

        return Response({
            "fetched_from_tally": tally_ledgers + tally_vendors + tally_accounts + tally_items + tally_invoices + tally_receipts ,
            "migrated_to_zoho": zoho_ledgers + zoho_vendors + zoho_accounts + zoho_items + zoho_invoices + zoho_receipts,
            "pending_migration_to_zoho": pending_ledgers + pending_vendors + pending_accounts + pending_items + pending_invoices + pending_receipts ,
            "customers":zoho_ledgers,
            "vendors":zoho_vendors,
            "COA":zoho_accounts,
            "items":zoho_items,
            "invoices":zoho_invoices,
            "receipts":zoho_receipts
        })
