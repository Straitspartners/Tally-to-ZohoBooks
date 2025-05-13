# from rest_framework import serializers
# from .models import Ledger

# class LedgerSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Ledger
#         fields = ['name', 'parent', 'closing_balance']

from rest_framework import serializers
from .models import Ledger

class LedgerSerializer(serializers.ModelSerializer):
    """
    Serializer for Ledger model to convert data to/from JSON.
    """
    class Meta:
        model = Ledger
        fields = ['id', 'name', 'parent', 'phone', 'user', 'email']
        
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
