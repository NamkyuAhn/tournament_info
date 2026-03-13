from django.shortcuts import render
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from tournaments.models import Tournament
from tournaments.serializers.serializers import TournamentListSerializer, TournamentDetailSerializer, TournamentCreateSerializer, TournamentEditSerializer, TournamentBuyInSerializer
from tournaments.services.services import create_tournament, update_tournament, TournamentBuyInService

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
    
class TournamentEditView(generics.UpdateAPIView):
    serializer_class = TournamentEditSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Tournament.objects.all()

    def update(self, request, *args, **kwargs):
        user = request.user

        if user.role != "SHOP_OWNER":
            raise PermissionDenied("Only shop owners can edit tournaments.")

        tournament = self.get_object()

        if tournament.shop != user.shop:
            raise PermissionDenied("You can only edit your own shop tournaments.")

        serializer = self.get_serializer(
            tournament,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)

        updated_tournament = update_tournament(
            tournament,
            serializer.validated_data
        )

        response_serializer = TournamentDetailSerializer(updated_tournament)

        return Response(
            {
                "message": "Tournament updated successfully.",
                "data": response_serializer.data
            }
        )

class TournamentBuyInView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request, tournament_id):

        serializer = TournamentBuyInSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        buyin_type = serializer.validated_data["type"]

        tournament = Tournament.objects.get(id=tournament_id)

        entry = TournamentBuyInService.execute(
            user=request.user,
            tournament=tournament,
            buyin_type=buyin_type
        )

        return Response(
            {
                "message": "Buy-in successful.",
                "entry_id": entry.id
            },
            status=status.HTTP_200_OK
        )
