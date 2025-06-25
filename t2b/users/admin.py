from django.contrib import admin
from .models import *

admin.site.register(Ledger)
admin.site.register(Vendor)
admin.site.register(Account)
admin.site.register(ZohoBooksCredential)
admin.site.register(Item)