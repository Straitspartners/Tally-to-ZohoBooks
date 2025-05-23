from django.db import models
from django.conf import settings

class Ledger(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=255)
    parent = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=20, null=True, blank=True)  # Changed from IntegerField
    email = models.EmailField(null=True, blank=True)  # Changed to EmailField

    def __str__(self):
        return f"{self.name} - {self.parent}"

    class Meta:
        unique_together = ['user', 'name']
