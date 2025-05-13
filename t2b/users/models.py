# from django.db import models
# from django.contrib.auth.models import User

# class Ledger(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     name = models.CharField(max_length=255)
#     parent = models.CharField(max_length=255, null=True, blank=True)
#     closing_balance = models.CharField(max_length=100, null=True, blank=True)
#     created_at = models.DateTimeField(auto_now_add=True)

from django.db import models
from django.conf import settings

# class Ledger(models.Model):
#     """
#     Ledger model to store ledger details coming from Tally.
#     """
#     user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,null=True)  # Link to the user
#     name = models.CharField(max_length=255, unique=True)  # Ledger name (unique for each user)
#     parent = models.CharField(max_length=255, blank=True, null=True)  # Parent group of the ledger
#     phone = models.IntegerField(null=True, blank=True)  # Phone number associated with the ledger
#     email=models.CharField(max_length=255,default="",null=True)  # Date when this ledger was created
    
#     def __str__(self):
#         return f"{self.name} - {self.parent}"

#     class Meta:
#         unique_together = ['user', 'name']  # Ensure each user can only have one ledger with a given name
# models.py
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
