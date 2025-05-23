from rest_framework import serializers
from .models import *

class LedgerSerializer(serializers.ModelSerializer):
    """
    Serializer for Ledger model to convert data to/from JSON.
    """
    class Meta:
        model = Ledger
        fields = ['id',
        'user',
        'name',
        'parent',
        'email',
        'address',
        'ledger_mobile',
        'website',
        'state_name',
        'country_name',
        'pincode']
        
    # Optional: You can add validation for fields here if necessary.
    # def validate_closing_balance(self, value):
    #     try:
    #         return float(value)
    #     except ValueError:
    #         raise serializers.ValidationError("Closing balance must be a number.")
        
    def validate_name(self, value):
        if not value:
            raise serializers.ValidationError("Ledger name cannot be empty.")
        return value

class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = ['id', 'user', 'name', 'parent', 'email', 'address', 'ledger_mobile', 'website', 'state_name', 'country_name', 'pincode']
    
    def validate_name(self, value):
        if not value:
            raise serializers.ValidationError("Vendor name cannot be empty.")
        return value