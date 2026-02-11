from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import Shop

class ShopCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role != 'SHOP_OWNER':
            return Response(
                {"detail": "only shop owner allowed"},
                status=status.HTTP_403_FORBIDDEN
            )

        if hasattr(request.user, 'shop'):
            return Response(
                {"detail": "shop already exists"},
                status=status.HTTP_400_BAD_REQUEST
            )

        name = request.data.get("name")
        if not name:
            return Response(
                {"detail": "name required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if Shop.objects.filter(name=name).exists():
            return Response(
                {"detail": "shop name already exists"},
                status=status.HTTP_400_BAD_REQUEST
            )

        shop = Shop.objects.create(
            name=name,
            owner=request.user
        )

        return Response(
            {
                "id": shop.id,
                "name": shop.name,
            },
            status=status.HTTP_201_CREATED
        )