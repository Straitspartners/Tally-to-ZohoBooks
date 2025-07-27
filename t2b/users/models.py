# models.py

# from django.db import models
# from django.conf import settings

# class Ledger(models.Model):
#     user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)
#     name = models.CharField(max_length=255)
#     parent = models.CharField(max_length=255, blank=True, null=True)
#     phone = models.CharField(max_length=20, null=True, blank=True)  # Changed from IntegerField
#     email = models.EmailField(null=True, blank=True)  # Changed to EmailField
#     address = models.TextField(blank=True, null=True)

#     def __str__(self):
#         return f"{self.name} - {self.parent}"

#     class Meta:
#         unique_together = ['user', 'name']

from django.db import models
from django.conf import settings

class ZohoTax(models.Model):
    tax_name = models.CharField(max_length=50)
    tax_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    zoho_tax_id = models.CharField(max_length=100, null=True, blank=True)
    fetched_from_tally = models.BooleanField(default=False)
    pushed_to_zoho = models.BooleanField(default=False)


class Ledger(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=255)
    parent = models.CharField(max_length=255, blank=True, null=True)
    
    email = models.EmailField(null=True, blank=True)
    address = models.TextField(blank=True, null=True)
    
    ledger_mobile = models.CharField(max_length=20, null=True, blank=True)
    
    website = models.URLField(null=True, blank=True)
    state_name = models.CharField(max_length=100, null=True, blank=True)
    country_name = models.CharField(max_length=100, null=True, blank=True)
    pincode = models.CharField(max_length=10, null=True, blank=True)

    zoho_contact_id = models.CharField(max_length=100, null=True, blank=True)

    fetched_from_tally = models.BooleanField(default=False)
    pushed_to_zoho = models.BooleanField(default=False)



    def __str__(self):
        return f"{self.name} - {self.parent}"

    class Meta:
        unique_together = ['user', 'name' , 'parent']


# models.py
class Vendor(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=255)
    parent = models.CharField(max_length=255, blank=True, null=True)
    
    email = models.EmailField(null=True, blank=True)
    address = models.TextField(blank=True, null=True)
    
    ledger_mobile = models.CharField(max_length=20, null=True, blank=True)
    website = models.URLField(null=True, blank=True)
    state_name = models.CharField(max_length=100, null=True, blank=True)
    country_name = models.CharField(max_length=100, null=True, blank=True)
    pincode = models.CharField(max_length=10, null=True, blank=True)

    zoho_contact_id = models.CharField(max_length=100, null=True, blank=True)

    fetched_from_tally = models.BooleanField(default=False)
    pushed_to_zoho = models.BooleanField(default=False)



    def __str__(self):
        return f"{self.name} - {self.parent}"

    class Meta:
        unique_together = ['user', 'name' , 'parent']


class Account(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)
    account_name = models.CharField(max_length=255)
    account_code = models.CharField(max_length=255, unique=True)
    account_type = models.CharField(max_length=255)
    zoho_account_id = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    fetched_from_tally = models.BooleanField(default=False)
    pushed_to_zoho = models.BooleanField(default=False)


    def __str__(self):
        return self.account_name
    
class Item(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=255)
    rate = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    description = models.TextField(blank=True, null=True)
    sku = models.CharField(max_length=100, blank=True, null=True)
    product_type = models.CharField(max_length=100, blank=True, null=True)
    account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True)

    gst_applicable = models.CharField(max_length=50, default="Not Applicable")
    gst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    hsn_code = models.CharField(max_length=20, blank=True, null=True)

    fetched_from_tally = models.BooleanField(default=False)
    pushed_to_zoho = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    

class ZohoBooksCredential(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    # OAuth App Credentials
    client_id = models.CharField(max_length=255)
    client_secret = models.CharField(max_length=255)

    # Token Management
    access_token = models.TextField()
    refresh_token = models.TextField()
    token_expires_at = models.DateTimeField()

    # Required for all Zoho Books API calls
    organization_id = models.CharField(max_length=100)

    connected_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Zoho Credential for {self.user.username}"



class Invoice(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    customer_name = models.CharField(max_length=255)
    invoice_number = models.CharField(max_length=100)
    invoice_date = models.DateField()
    cgst = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    sgst = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    zoho_invoice_id = models.CharField(max_length=100, null=True, blank=True)
    fetched_from_tally = models.BooleanField(default=False)
    pushed_to_zoho = models.BooleanField(default=False)

    class Meta:
        unique_together = ['user', 'invoice_number']

    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.customer_name}"

class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, related_name='items', on_delete=models.CASCADE)
    item_name = models.CharField(max_length=255)
    quantity = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    fetched_from_tally = models.BooleanField(default=False)
    pushed_to_zoho = models.BooleanField(default=False)
    

    def __str__(self):
        return f"{self.item_name} ({self.quantity})"

class Receipt(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    receipt_number = models.CharField(max_length=100)
    receipt_date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_mode = models.CharField(max_length=50)

    customer = models.ForeignKey(Ledger, on_delete=models.SET_NULL, null=True, blank=True)
    customer_zoho_id = models.CharField(max_length=100, null=True, blank=True)

    agst_invoice = models.ForeignKey(Invoice, on_delete=models.SET_NULL, null=True, blank=True)
    invoice_zoho_id = models.CharField(max_length=100, null=True, blank=True)
    invoice_total_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # 👈 New field

    zoho_receipt_id = models.CharField(max_length=100, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    fetched_from_tally = models.BooleanField(default=False)
    pushed_to_zoho = models.BooleanField(default=False)

    class Meta:
        unique_together = ['user', 'receipt_number']

    def __str__(self):
        return f"Receipt {self.receipt_number} - {self.customer.name if self.customer else 'Unknown'}"


class Purchase(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    vendor_name = models.CharField(max_length=255)
    purchase_number = models.CharField(max_length=100)
    purchase_ledger = models.CharField(max_length=255,default=None)  # <- Add this
    purchase_date = models.DateField()
    cgst = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sgst = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    fetched_from_tally = models.BooleanField(default=False)
    pushed_to_zoho = models.BooleanField(default=False)
    zoho_bill_id = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.purchase_number} - {self.vendor_name}"


class PurchaseItem(models.Model):
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name="items")
    account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True)
    item_name = models.CharField(max_length=255)
    quantity = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    fetched_from_tally = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.item_name} ({self.quantity})"


class Payment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    payment_number = models.CharField(max_length=100)
    payment_date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_mode = models.CharField(max_length=50)

    vendor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, null=True, blank=True)
    vendor_zoho_id = models.CharField(max_length=100, null=True, blank=True)

    agst_invoice = models.ForeignKey(Purchase, on_delete=models.SET_NULL, null=True, blank=True)
    invoice_zoho_id = models.CharField(max_length=100, null=True, blank=True)
    invoice_total_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    zoho_payment_id = models.CharField(max_length=100, null=True, blank=True)

    fetched_from_tally = models.BooleanField(default=False)
    pushed_to_zoho = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'payment_number']


