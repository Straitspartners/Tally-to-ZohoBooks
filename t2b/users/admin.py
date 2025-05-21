from django.contrib import admin
from .models import Customer, Vendor

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'contact_name', 'user', 'email', 'phone')
    search_fields = ('company_name', 'contact_name', 'email', 'phone')

@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'contact_name', 'user', 'email', 'phone')
    search_fields = ('company_name', 'contact_name', 'email', 'phone')
