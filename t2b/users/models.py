from django.db import models
from django.conf import settings

class Customer(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    contact_name = models.CharField(max_length=255)
    company_name = models.CharField(max_length=255)
    website = models.URLField(blank=True, null=True)
    billing_address = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    class Meta:
        unique_together = ['user', 'company_name']

    def __str__(self):
        return self.company_name


class Vendor(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    contact_name = models.CharField(max_length=255)
    company_name = models.CharField(max_length=255)
    website = models.URLField(blank=True, null=True)
    billing_address = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    class Meta:
        unique_together = ['user', 'company_name']

    def __str__(self):
        return self.company_name

