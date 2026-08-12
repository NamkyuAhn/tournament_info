from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from tournaments.pagination import TournamentPagination
from tournaments.models import Tournament

from tournaments.serializers.user_serializers import (
    MyTournamentSerializer,
    MyTournamentDetailSerializer,
    TournamentBuyInSerializer
)

from tournaments.services.user_services import (
    TournamentBuyInService,
    TournamentPlayerManageService
)

class TournamentBuyInView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    def post(
        self,
        request,
        tournament_id
    ):

        serializer = (
            TournamentBuyInSerializer(
                data=request.data
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        tournament = (
            Tournament.objects
            .get(id=tournament_id)
        )

        entry = (
            TournamentBuyInService.execute(
                user=request.user,
                tournament=tournament,
                buyin_type=serializer.validated_data[
                    "type"
                ],
            )
        )

        return Response(
            {
                "message": (
                    "Buy-in successful."
                ),
                "entry_id": entry.id,
            },
            status=status.HTTP_200_OK,
        )

class MyTournamentListView(
    generics.ListAPIView
):

    serializer_class = MyTournamentSerializer
    pagination_class = TournamentPagination
    
    def get_queryset(self):

        return (
            TournamentPlayerManageService
            .get_my_tournaments(
                self.request.user
            )
        )

class MyTournamentDetailView(
    generics.RetrieveAPIView
):

    serializer_class = (
        MyTournamentDetailSerializer
    )

    def get(self, request, *args, **kwargs):

        entry = (
            TournamentPlayerManageService
            .get_my_tournament_detail(
                user=request.user,
                tournament_id=kwargs[
                    "tournament_id"
                ],
            )
        )

        serializer = self.get_serializer(
            entry.tournament,
            context={
                "request": request,
                "entry": entry,
            }
        )

        return Response(
            serializer.data
        )

