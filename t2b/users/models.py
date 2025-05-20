
from django.db import models
from django.conf import settings

class Ledger(models.Model):
    LEDGER_TYPE_CHOICES = [
        ('customer', 'Customer'),
        ('vendor', 'Vendor'),
        ('coa', 'Chart of Accounts'),
        ('item', 'Item'),  # ✅ Add support for items
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=255)
    parent = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)

    # ✅ New field to differentiate between ledger types
    ledger_type = models.CharField(
        max_length=20,
        choices=LEDGER_TYPE_CHOICES,
        default='coa'  # Or set to null/blank if you want to keep it flexible
    )

    def __str__(self):
        return f"{self.name} - {self.ledger_type}"

    class Meta:
        unique_together = ['user', 'name']

