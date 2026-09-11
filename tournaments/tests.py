from datetime import timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from shops.models import Shop
from tournaments.models import BuyInEvent, Tournament, TournamentEntry


class TournamentStatusAPITests(APITestCase):
    """Cancel exclusively through the refund API; preserve other transitions."""

    @classmethod
    def setUpTestData(cls):
        user_model = get_user_model()
        cls.owner = user_model.objects.create_user(
            username="owner", email="owner@example.com", role="SHOP_OWNER"
        )
        cls.player = user_model.objects.create_user(
            username="player", email="player@example.com", role="PLAYER", money=900
        )
        cls.shop = Shop.objects.create(owner=cls.owner, name="Test Shop")
        start = timezone.now() + timedelta(days=1)
        cls.tournament = Tournament.objects.create(
            shop=cls.shop,
            title="Original title",
            game_type="CHESS",
            start_time=start,
            registration_deadline=start + timedelta(hours=1),
            prize_structure={"1": 1000},
            entry_fee=100,
            max_participants=10,
            live_players_cache=1,
        )
        cls.entry = TournamentEntry.objects.create(
            tournament=cls.tournament, player=cls.player, approval_status="APPROVED"
        )
        cls.event = BuyInEvent.objects.create(entry=cls.entry, type="ENTRY", amount=100)

    def setUp(self):
        self.client.force_authenticate(self.owner)
        self.edit_url = reverse("tournament-edit", kwargs={"pk": self.tournament.pk})
        self.status_url = reverse(
            "tournament-status-update", kwargs={"tournament_id": self.tournament.pk}
        )
        self.cancel_url = reverse(
            "tournament-cancel", kwargs={"tournament_id": self.tournament.pk}
        )

    def test_edit_rejects_canceled_without_saving_any_fields(self):
        response = self.client.patch(
            self.edit_url,
            {"status": "CANCELED", "title": "Must not save"},
            format="multipart",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {"status": ["CANCELED status can only be set through the cancel API."]},
        )
        self.tournament.refresh_from_db()
        self.player.refresh_from_db()
        self.event.refresh_from_db()
        self.entry.refresh_from_db()
        self.assertEqual(self.tournament.status, "WAITING")
        self.assertEqual(self.tournament.title, "Original title")
        self.assertIsNone(self.tournament.canceled_at)
        self.assertEqual(self.tournament.live_players_cache, 1)
        self.assertEqual(self.player.money, 900)
        self.assertFalse(self.event.refunded)
        self.assertEqual(self.entry.status, "REGISTERED")

    def test_status_endpoint_still_rejects_canceled(self):
        response = self.client.patch(
            self.status_url, {"status": "CANCELED"}, format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {"detail": "CANCELED status can only be set through the cancel API."},
        )
        self.tournament.refresh_from_db()
        self.assertEqual(self.tournament.status, "WAITING")

    def test_other_status_transitions_remain_unrestricted(self):
        statuses = ["WAITING", "RUNNING", "REGI_CLOSED", "FINISHED"]
        for url, request_format in [
            (self.edit_url, "multipart"),
            (self.status_url, "json"),
        ]:
            for current in statuses:
                for target in statuses:
                    with self.subTest(url=url, current=current, target=target):
                        Tournament.objects.filter(pk=self.tournament.pk).update(
                            status=current
                        )
                        response = self.client.patch(
                            url, {"status": target}, format=request_format
                        )
                        self.assertEqual(response.status_code, 200, response.data)
                        self.tournament.refresh_from_db()
                        self.assertEqual(self.tournament.status, target)

    def test_edit_without_status_still_updates_title(self):
        response = self.client.patch(
            self.edit_url, {"title": "New title"}, format="multipart"
        )
        self.assertEqual(response.status_code, 200)
        self.tournament.refresh_from_db()
        self.assertEqual(self.tournament.title, "New title")
        self.assertEqual(self.tournament.status, "WAITING")

    def test_cancel_endpoint_refunds_once_and_cancels_entry(self):
        response = self.client.post(self.cancel_url)
        self.assertEqual(response.status_code, 200)
        self.tournament.refresh_from_db()
        self.entry.refresh_from_db()
        self.event.refresh_from_db()
        self.player.refresh_from_db()
        self.assertEqual(self.tournament.status, "CANCELED")
        self.assertEqual(self.tournament.live_players_cache, 0)
        self.assertIsNotNone(self.tournament.canceled_at)
        self.assertEqual(self.entry.status, "CANCELED")
        self.assertTrue(self.event.refunded)
        self.assertIsNotNone(self.event.refunded_at)
        self.assertEqual(self.player.money, 1000)
        self.assertEqual(self.client.post(self.cancel_url).status_code, 400)
        self.player.refresh_from_db()
        self.assertEqual(self.player.money, 1000)

    def test_player_cannot_edit_status(self):
        self.client.force_authenticate(self.player)
        response = self.client.patch(
            self.edit_url, {"status": "RUNNING"}, format="multipart"
        )
        self.assertEqual(response.status_code, 403)

    def test_anonymous_user_cannot_edit_status(self):
        self.client.force_authenticate(None)
        response = self.client.patch(
            self.edit_url, {"status": "RUNNING"}, format="multipart"
        )
        self.assertEqual(response.status_code, 401)
