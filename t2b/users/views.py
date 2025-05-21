from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token

from .models import Customer, Vendor
from .serializers import CustomerSerializer, VendorSerializer


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sync_customers(request):
    user = request.user
    customers = request.data

    if not isinstance(customers, list):
        return Response({"error": "Expected a list of customers."}, status=status.HTTP_400_BAD_REQUEST)

    count = 0
    for entry in customers:
        if not entry.get("company_name"):
            continue
        Customer.objects.update_or_create(
            user=user,
            company_name=entry["company_name"],
            defaults={
                "contact_name": entry.get("contact_name", ""),
                "website": entry.get("website", ""),
                "billing_address": entry.get("billing_address", ""),
                "phone": entry.get("phone", ""),
                "email": entry.get("email", "")
            }
        )
        count += 1

    return Response({"message": f"{count} customers synced successfully."})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sync_vendors(request):
    user = request.user
    vendors = request.data

    if not isinstance(vendors, list):
        return Response({"error": "Expected a list of vendors."}, status=status.HTTP_400_BAD_REQUEST)

    count = 0
    for entry in vendors:
        if not entry.get("company_name"):
            continue
        Vendor.objects.update_or_create(
            user=user,
            company_name=entry["company_name"],
            defaults={
                "contact_name": entry.get("contact_name", ""),
                "website": entry.get("website", ""),
                "billing_address": entry.get("billing_address", ""),
                "phone": entry.get("phone", ""),
                "email": entry.get("email", "")
            }
        )
        count += 1

    return Response({"message": f"{count} vendors synced successfully."})


class CustomAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = serializer.validated_data['user']
            token, created = Token.objects.get_or_create(user=user)
            return Response({'token': token.key})
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)


# Installers :

# pip install requests

#for production 

# pip install pycopg2
# pip install psycopg2-binary
# pip install whitenoise