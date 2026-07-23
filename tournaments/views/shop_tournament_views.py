from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from django.db.models import Prefetch

from tournaments.models import (
    Tournament,
    TournamentEntry,
)

from tournaments.serializers.shop_tournament_serializers import (
    EntryApproveSerializer,
    ShopTournamentListSerializer,
    ShopTournamentDetailSerializer,
)

from tournaments.services.shop_tournament_player_manage_service import (
    TournamentPlayerManageService,
)


class ShopTournamentListView(
    generics.ListAPIView
):

    serializer_class = (
        ShopTournamentListSerializer
    )

    permission_classes = [
        permissions.IsAuthenticated
    ]

    def get_queryset(self):

        return (
            Tournament.objects
            .filter(
                shop__owner=self.request.user
            )
            .order_by(
                "-start_time"
            )
        )


class ShopTournamentDetailView(
    generics.RetrieveAPIView
):

    serializer_class = (
        ShopTournamentDetailSerializer
    )

    permission_classes = [
        permissions.IsAuthenticated
    ]

    def get_queryset(self):

        return (
            Tournament.objects
            .filter(
                shop__owner=self.request.user
            )
            .prefetch_related(
                Prefetch(
                    "entries",
                    queryset=(
                        TournamentEntry.objects
                        .select_related("player")
                    ),
                ),
            )
        )


class EntryApproveView(
    generics.GenericAPIView
):

    serializer_class = (
        EntryApproveSerializer
    )

    permission_classes = [
        permissions.IsAuthenticated
    ]

    def patch(
        self,
        request,
        entry_id
    ):

        serializer = self.get_serializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        TournamentPlayerManageService.approve_entry(
            owner=request.user,
            entry_id=entry_id,
            table_number=(
                serializer.validated_data.get(
                    "table_number"
                )
            ),
            seat_number=(
                serializer.validated_data.get(
                    "seat_number"
                )
            ),
        )

        return Response(
            {
                "message": (
                    "Entry approved"
                )
            },
            status=status.HTTP_200_OK,
        )


class EntryRejectView(
    APIView
):

    permission_classes = [
        IsAuthenticated
    ]

    def patch(
        self,
        request,
        entry_id
    ):

        TournamentPlayerManageService.reject_entry(
            owner=request.user,
            entry_id=entry_id,
        )

        return Response(
            {
                "message": (
                    "Entry rejected"
                )
            },
            status=status.HTTP_200_OK,
        )


class EntryBustView(
    APIView
):

    permission_classes = [
        IsAuthenticated
    ]

    def patch(
        self,
        request,
        entry_id
    ):

        TournamentPlayerManageService.bust_player(
            owner=request.user,
            entry_id=entry_id,
        )

        return Response(
            {
                "message": (
                    "Player busted"
                )
            },
            status=status.HTTP_200_OK,
        )