from django.shortcuts import render
from django.contrib.auth import authenticate, get_user_model

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated

import uuid

User = get_user_model()

class LoginView(APIView):
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response(
                {"detail": "email and password required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(request, email=email, password=password)

        if not user:
            return Response(
                {"detail": "invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        refresh = RefreshToken.for_user(user)

        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        })

class SignupView(APIView):
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        name = request.data.get("name")
        role = request.data.get("role")

        if not all([email, password, name, role]):
            return Response(
                {"detail": "missing required fields"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if User.objects.filter(email=email).exists():
            return Response(
                {"detail": "email already exists"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = User.objects.create_user(
            email=email,
            username=str(uuid.uuid4()),
            name=name,
            password=password,
            role=role,
        )

        return Response(
            {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "role": user.role,
            },
            status=status.HTTP_201_CREATED
        )

class UserInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        return Response({
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "money": user.money,
        })