from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied


from tournaments.serializers.my_tournament_serializers import (
    MyTournamentSerializer,
    MyTournamentDetailSerializer
)

from tournaments.services.my_tournament_services import (
    TournamentPlayerManageService
)



class MyTournamentListView(
    generics.ListAPIView
):

    serializer_class = MyTournamentSerializer

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