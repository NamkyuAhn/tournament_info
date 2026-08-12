from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied

from django.shortcuts import get_object_or_404
from django.db.models import Prefetch

import json

from tournaments.pagination import TournamentPagination, EntryPagination

from tournaments.models import (
    Tournament,
    TournamentEntry,
)

from tournaments.serializers.shop_serializers import (
    EntryApproveSerializer,
    ShopTournamentListSerializer,
    ShopTournamentDetailSerializer,
    TournamentEntrySerializer,
    TournamentCreateSerializer,
    TournamentEditSerializer
)

from tournaments.services.shop_service import (
    TournamentPlayerManageService,
    create_tournament,
    update_tournament
)

from tournaments.serializers.serializers import (
    TournamentDetailSerializer,
)


class TournamentCreateView(
    generics.CreateAPIView
):

    serializer_class = TournamentCreateSerializer

    permission_classes = [
        permissions.IsAuthenticated
    ]

    def create(
        self,
        request,
        *args,
        **kwargs
    ):

        data = {}

        for key, value in request.data.items():
            data[key] = value


        if "poker_tournament" in data:
            data["poker_tournament"] = json.loads(
                data["poker_tournament"]
            )

        if "prize_structure" in data:
            data["prize_structure"] = json.loads(
                data["prize_structure"]
            )
            
        serializer = self.get_serializer(
            data=data
        )

        serializer.is_valid(
            raise_exception=True
        )

        user = request.user

        if user.role != "SHOP_OWNER":

            raise PermissionDenied(
                "Only shop owners can create tournaments."
            )

        tournament = create_tournament(
            shop=user.shop,
            validated_data=serializer.validated_data,
            images=request.FILES.getlist(
                "images"
            ),
        )

        response_serializer = (
            TournamentDetailSerializer(
                tournament
            )
        )

        return Response(
            {
                "message": (
                    "Tournament created successfully."
                ),
                "data": response_serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )

class TournamentEditView(
    generics.UpdateAPIView
):

    serializer_class = TournamentEditSerializer

    permission_classes = [
        permissions.IsAuthenticated
    ]

    queryset = Tournament.objects.all()

    def update(
        self,
        request,
        *args,
        **kwargs
    ):

        user = request.user

        if user.role != "SHOP_OWNER":

            raise PermissionDenied(
                "Only shop owners can edit tournaments."
            )

        tournament = self.get_object()

        if tournament.shop != user.shop:

            raise PermissionDenied(
                "You can only edit your own shop tournaments."
            )


        data = request.data.dict()


        if "poker_tournament" in data:

            data["poker_tournament"] = json.loads(
                data["poker_tournament"]
            )

        if "prize_structure" in data:
            data["prize_structure"] = json.loads(
                data["prize_structure"]
            )

        existing_image_ids = None

        if "existing_image_ids" in data:

            existing_image_ids = json.loads(
                data["existing_image_ids"]
            )

            data.pop(
                "existing_image_ids",
                None
            )


        serializer = self.get_serializer(
            tournament,
            data=data,
            partial=True,
        )

        serializer.is_valid(
            raise_exception=True
        )


        updated_tournament = update_tournament(
            tournament,
            serializer.validated_data,
            images=request.FILES.getlist(
                "images"
            ),
            existing_image_ids=existing_image_ids,
        )

        response_serializer = (
            TournamentDetailSerializer(
                updated_tournament
            )
        )

        return Response(
            {
                "message": (
                    "Tournament updated successfully."
                ),
                "data": response_serializer.data,
            }
        )

class ShopTournamentListView(
    generics.ListAPIView
    ):

    serializer_class = ShopTournamentListSerializer
    pagination_class = TournamentPagination

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
                "-created_at"
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
                        .prefetch_related("buyin_events")
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

class TournamentStatusUpdateView(APIView):

    permission_classes = [
        permissions.IsAuthenticated
    ]

    def patch(self, request, tournament_id):

        tournament = get_object_or_404(
            Tournament,
            id=tournament_id,
            shop__owner=request.user
        )

        new_status = request.data.get("status")

        if not new_status:
            return Response(
                {
                    "detail": "status is required."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        valid_statuses = dict(
            Tournament.StatusChoices.choices
        )

        if new_status not in valid_statuses:
            return Response(
                {
                    "detail": "Invalid tournament status."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if new_status == Tournament.StatusChoices.CANCELED:
            return Response(
                {
                    "detail": (
                        "CANCELED status can only be set "
                        "through the cancel API."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if tournament.status == Tournament.StatusChoices.CANCELED:
            return Response(
                {
                    "detail": (
                        "Canceled tournaments cannot change status."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        tournament.status = new_status

        tournament.save(
            update_fields=["status"]
        )

        return Response(
            {
                "message": (
                    "Tournament status updated successfully."
                ),
                "status": tournament.status,
            },
            status=status.HTTP_200_OK
        )
    
class TournamentCancelView(
    APIView
    ):

        permission_classes = [
            IsAuthenticated
        ]

        def post(
            self,
            request,
            tournament_id
        ):

            TournamentPlayerManageService.cancel_tournament(
                owner=request.user,
                tournament_id=tournament_id
            )

            return Response(
                {
                    "detail": (
                        "Tournament canceled successfully."
                    )
                },
                status=status.HTTP_200_OK
            )

class ShopTournamentEntryListView(generics.ListAPIView):

    serializer_class = TournamentEntrySerializer
    pagination_class = EntryPagination

    permission_classes = [
        permissions.IsAuthenticated
    ]

    def get_queryset(self):

        return (
            TournamentEntry.objects
            .filter(
                tournament_id=self.kwargs["pk"],
                tournament__shop__owner=self.request.user
            )
            .select_related("player")
            .prefetch_related("buyin_events")
            .order_by("-created_at")
        )