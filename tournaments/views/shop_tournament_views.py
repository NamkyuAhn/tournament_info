from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.db.models import Prefetch
from tournaments.models import Tournament, TournamentEntry
from tournaments.serializers.shop_tournament_serializers import *
from tournaments.services.shop_tournament_player_manage_service import TournamentPlayerManageService

class ShopTournamentListView(generics.ListAPIView):

    serializer_class = ShopTournamentListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Tournament.objects.filter(shop=user.shop)

class ShopTournamentDetailView(generics.RetrieveAPIView):

    serializer_class = ShopTournamentDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Tournament.objects.filter(
            shop__owner=self.request.user
        ).prefetch_related(
            Prefetch(
                "entries",
                queryset=TournamentEntry.objects.select_related("player")
            )
        )

class EntryApproveView(generics.GenericAPIView):

    serializer_class = EntryApproveSerializer

    def patch(self, request, entry_id):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        entry = TournamentPlayerManageService.approve_entry(
            request.user,
            entry_id,
            serializer.validated_data["table_number"],
            serializer.validated_data["seat_number"]
        )

        return Response({"message": "Entry approved"})
    
class EntryRejectView(APIView):

    permission_classes = [IsAuthenticated]

    def patch(self, request, entry_id):

        TournamentPlayerManageService.reject_entry(
            request.user,
            entry_id
        )

        return Response(
            {"message": "Entry rejected"},
            status=status.HTTP_200_OK
        )   

class EntryBustView(APIView):

    permission_classes = [IsAuthenticated]

    def patch(self, request, entry_id):

        TournamentPlayerManageService.bust_player(
            request.user,
            entry_id
        )

        return Response(
            {"message": "Player busted"},
            status=status.HTTP_200_OK
        )