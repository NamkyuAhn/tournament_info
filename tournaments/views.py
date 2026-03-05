from django.shortcuts import render
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from .models import Tournament
from .serializers import TournamentListSerializer, TournamentDetailSerializer, TournamentCreateSerializer
from .services import create_tournament

class TournamentListView(generics.ListAPIView):
    serializer_class = TournamentListSerializer

    def get_queryset(self):
        queryset = Tournament.objects.select_related("shop")

        status = self.request.query_params.get("status")

        if status:
            queryset = queryset.filter(status=status)

        return queryset.order_by("-start_time")

class TournamentDetailView(generics.RetrieveAPIView):
    serializer_class = TournamentDetailSerializer
    lookup_field = "id"

    def get_queryset(self):
        return Tournament.objects.select_related("shop")

class TournamentCreateView(generics.CreateAPIView):
    serializer_class = TournamentCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        if user.role != "SHOP_OWNER":
            raise PermissionDenied("Only shop owners can create tournaments.")

        tournament = create_tournament(
            shop=user.shop,
            validated_data=serializer.validated_data,
            images=request.FILES.getlist("images"),
        )

        response_serializer = TournamentDetailSerializer(tournament)

        return Response(
            {
                "message": "Tournament created successfully.",
                "data": response_serializer.data,
            },
            status=201,
        )