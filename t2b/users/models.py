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

    def __str__(self):
        return f"{self.name} - {self.parent}"

    class Meta:
        unique_together = ['user', 'name' , 'parent']


class Account(models.Model):
    account_name = models.CharField(max_length=255)
    account_code = models.CharField(max_length=255, unique=True)
    account_type = models.CharField(max_length=255)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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

