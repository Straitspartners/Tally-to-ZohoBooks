from django.contrib import admin
from .models import Ledger


@admin.register(Ledger)
class LedgerAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'ledger_type', 'parent', 'phone', 'email')  # Shown columns
    list_filter = ('user', 'ledger_type')  # Right-side filters
    search_fields = ('name', 'phone', 'email', 'parent')  # Search bar fields
    ordering = ('user', 'ledger_type', 'name')  # Default ordering

    # Optional: Add read-only fields
    readonly_fields = ('user', 'name')

    # Optional: Customize list per page
    list_per_page = 25
