from rest_framework import serializers
from .models import Ledger

class LedgerSerializer(serializers.ModelSerializer):
    """
    Serializer for Ledger model to convert data to/from JSON.
    Includes validation and the new 'ledger_type' field.
    """

    class Meta:
        model = Ledger
        fields = ['id', 'name', 'parent', 'phone', 'user', 'email', 'ledger_type']
        read_only_fields = ['user']  # user should be automatically set from the request context

    def validate_name(self, value):
        if not value:
            raise serializers.ValidationError("Ledger name cannot be empty.")
        return value

    def validate_ledger_type(self, value):
        valid_types = ['customers', 'vendors', 'coa', 'items']
        if value and value not in valid_types:
            raise serializers.ValidationError(f"Invalid ledger type. Must be one of: {', '.join(valid_types)}.")
        return value
