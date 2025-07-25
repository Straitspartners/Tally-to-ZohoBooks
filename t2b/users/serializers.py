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
    
class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['user','account_name', 'account_code', 'account_type']

class ZohoBooksCredentialSerializer(serializers.ModelSerializer):
    class Meta:
        model = ZohoBooksCredential
        fields = [
            "client_id", "client_secret", "refresh_token", "organization_id"
        ]

class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ['id', 'user', 'name', 'rate', 'description', 'sku', 'product_type', 'account']



## Signup,Sigin,Forgot Password

from django.contrib.auth.models import User
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'confirm_password')

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords must match.")
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        return User.objects.create_user(**validated_data)

class LoginSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    password = serializers.CharField()

class ResetPasswordEmailRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

class SetNewPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    token = serializers.CharField()
    uidb64 = serializers.CharField()

class InvoiceItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceItem
        fields = ['item_name', 'quantity', 'amount']

class InvoiceSerializer(serializers.ModelSerializer):
    items = InvoiceItemSerializer(many=True)

    class Meta:
        model = Invoice
        fields = [
            'customer_name', 'invoice_number', 'invoice_date',
            'cgst', 'sgst', 'total_amount', 'items'
        ]

