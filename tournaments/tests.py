from datetime import timedelta
import json
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone
from PIL import Image
from rest_framework.test import APITestCase

from shops.models import Shop
from tournaments.models import BuyInEvent, PokerTournament, Tournament, TournamentEntry


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


class TournamentFlowTests(APITestCase):
    def create_payload(self, **overrides):
        return {
            "title": "New tournament",
            "game_type": "CHESS",
            "start_time": self.start.isoformat(),
            "registration_deadline": self.start.isoformat(),
            "entry_fee": 100,
            "max_participants": 10,
            "prize_structure": json.dumps({"1": 500}),
            **overrides,
        }

    @staticmethod
    def image_file(name):
        content = BytesIO()
        Image.new("RGB", (1, 1), color="white").save(content, format="PNG")
        return SimpleUploadedFile(name, content.getvalue(), content_type="image/png")

    def setUp(self):
        users = get_user_model()
        self.owner = users.objects.create_user(
            username="owner", email="owner@example.com", role="SHOP_OWNER"
        )
        self.player = users.objects.create_user(
            username="player", email="player@example.com", role="PLAYER", money=1000
        )
        self.other = users.objects.create_user(
            username="other", email="other@example.com", role="SHOP_OWNER"
        )
        self.shop = Shop.objects.create(owner=self.owner, name="Poker shop")
        self.start = timezone.now() + timedelta(days=1)
        self.tournament = Tournament.objects.create(
            shop=self.shop,
            title="Poker",
            game_type="POKER",
            status="RUNNING",
            start_time=self.start,
            registration_deadline=self.start + timedelta(hours=1),
            prize_structure={"1": 1000},
            entry_fee=100,
            max_participants=10,
        )
        self.poker = PokerTournament.objects.create(
            tournament=self.tournament,
            max_entries=10,
            max_reentries=2,
            max_addons=3,
            starting_chips=1000,
            reentry_chips=1000,
            addon_chips=500,
            reentry_fee=80,
            addon_fee=50,
            blind_structure={
                "levels": [
                    {
                        "level": 1,
                        "small_blind": 10,
                        "big_blind": 20,
                        "ante": 0,
                        "duration_minutes": 10,
                    }
                ]
            },
        )
        self.buyin_url = reverse(
            "tournament-buyin", kwargs={"tournament_id": self.tournament.id}
        )

    def buyin(self, kind="ENTRY", expected=200):
        self.client.force_authenticate(self.player)
        response = self.client.post(self.buyin_url, {"type": kind}, format="json")
        self.assertEqual(response.status_code, expected, response.data)
        return response

    def manage(self, action, entry, expected=200):
        self.client.force_authenticate(self.owner)
        response = self.client.patch(
            reverse(f"entry-{action}", kwargs={"entry_id": entry.id}),
            {"table_number": 1, "seat_number": 1},
            format="json",
        )
        self.assertEqual(response.status_code, expected, response.data)
        entry.refresh_from_db()
        return response

    def enter(self, approve=False):
        response = self.buyin()
        entry = TournamentEntry.objects.get(id=response.data["entry_id"])
        if approve:
            self.manage("approve", entry)
        return entry

    def test_entry_charges_once_and_starts_pending(self):
        entry = self.enter()
        self.player.refresh_from_db()
        self.assertEqual(self.player.money, 900)
        self.assertEqual(entry.status, "REGISTERED")
        self.assertEqual(entry.approval_status, "PENDING")
        self.assertEqual(entry.total_entries_cache, 1)
        self.assertEqual(
            list(entry.buyin_events.values_list("type", "amount")), [("ENTRY", 100)]
        )
        self.buyin(expected=400)
        self.player.refresh_from_db()
        self.assertEqual(self.player.money, 900)
        self.assertEqual(entry.buyin_events.count(), 1)

    def test_pending_entry_cannot_request_addon(self):
        entry = self.enter()
        response = self.buyin("ADDON", expected=400)
        self.assertEqual(
            response.json(), ["Wait for approval before requesting another addon."]
        )
        entry.refresh_from_db()
        self.player.refresh_from_db()
        self.assertEqual(self.player.money, 900)
        self.assertEqual(entry.total_addons_cache, 0)
        self.assertEqual(entry.buyin_events.count(), 1)

    def test_pending_addon_cannot_charge_again(self):
        entry = self.enter(approve=True)
        self.buyin("ADDON")
        self.buyin("ADDON", expected=400)
        entry.refresh_from_db()
        self.player.refresh_from_db()
        self.assertEqual(self.player.money, 850)
        self.assertEqual(entry.approval_status, "PENDING")
        self.assertEqual(entry.total_addons_cache, 1)
        self.assertEqual(entry.buyin_events.filter(type="ADDON").count(), 1)

    def test_approved_addon_allows_next_request_without_increasing_live_players(self):
        entry = self.enter(approve=True)
        self.buyin("ADDON")
        self.manage("approve", entry)
        self.poker.refresh_from_db()
        self.tournament.refresh_from_db()
        self.assertEqual(self.poker.total_addons_cache, 1)
        self.assertEqual(self.tournament.live_players_cache, 1)
        self.buyin("ADDON")
        self.player.refresh_from_db()
        self.assertEqual(self.player.money, 800)

    def test_rejected_addon_refunds_and_allows_retry(self):
        entry = self.enter(approve=True)
        self.buyin("ADDON")
        self.manage("reject", entry)
        self.player.refresh_from_db()
        self.assertEqual(self.player.money, 900)
        self.assertEqual(entry.status, "REGISTERED")
        self.assertEqual(entry.total_addons_cache, 0)
        event = entry.buyin_events.get(type="ADDON")
        self.assertTrue(event.refunded)
        self.assertIsNotNone(event.refunded_at)
        self.buyin("ADDON")

    def test_entry_approval_updates_counts_and_prevents_double_approval(self):
        entry = self.enter(approve=True)
        self.poker.refresh_from_db()
        self.tournament.refresh_from_db()
        self.assertEqual(self.poker.total_entries_cache, 1)
        self.assertEqual(self.tournament.live_players_cache, 1)
        self.assertEqual(entry.approval_status, "APPROVED")
        self.assertEqual(entry.approved_by_id, self.owner.id)
        self.assertIsNotNone(entry.approved_at)
        self.assertEqual((entry.table_number, entry.seat_number), (1, 1))
        self.manage("approve", entry, expected=400)
        self.tournament.refresh_from_db()
        self.assertEqual(self.tournament.live_players_cache, 1)

    def test_rejected_entry_refunds_once_and_can_reapply(self):
        entry = self.enter()
        self.manage("reject", entry)
        self.assertEqual(entry.status, "CANCELED")
        self.assertEqual(entry.total_entries_cache, 0)
        self.player.refresh_from_db()
        self.assertEqual(self.player.money, 1000)
        self.manage("reject", entry, expected=400)
        retry = self.buyin()
        self.assertEqual(retry.data["entry_id"], entry.id)
        self.player.refresh_from_db()
        self.assertEqual(self.player.money, 900)

    def test_bust_and_reentry_reset_seat_and_restore_live_count_on_approval(self):
        entry = self.enter(approve=True)
        self.manage("bust", entry)
        self.assertEqual(entry.status, "BUSTED")
        self.assertIsNotNone(entry.busted_at)
        self.tournament.refresh_from_db()
        self.assertEqual(self.tournament.live_players_cache, 0)
        self.buyin("REENTRY")
        entry.refresh_from_db()
        self.assertEqual(entry.total_reentries_cache, 1)
        self.assertEqual(entry.approval_status, "PENDING")
        self.assertIsNone(entry.busted_at)
        self.assertIsNone(entry.table_number)
        self.assertIsNone(entry.seat_number)
        self.buyin("ADDON", expected=400)
        self.manage("approve", entry)
        self.poker.refresh_from_db()
        self.tournament.refresh_from_db()
        self.player.refresh_from_db()
        self.assertEqual(self.player.money, 820)
        self.assertEqual(self.poker.total_reentries_cache, 1)
        self.assertEqual(self.tournament.live_players_cache, 1)

    def test_reentry_requires_bust(self):
        self.enter(approve=True)
        self.buyin("REENTRY", expected=400)
        self.player.refresh_from_db()
        self.assertEqual(self.player.money, 900)

    def test_insufficient_balance_does_not_create_entry_or_event(self):
        self.player.money = 99
        self.player.save(update_fields=["money"])
        self.buyin(expected=400)
        self.assertFalse(TournamentEntry.objects.exists())
        self.assertFalse(BuyInEvent.objects.exists())
        self.player.refresh_from_db()
        self.assertEqual(self.player.money, 99)

    def test_closed_tournaments_reject_buyin(self):
        for status in ["REGI_CLOSED", "FINISHED", "CANCELED"]:
            with self.subTest(status=status):
                self.tournament.status = status
                self.tournament.save(update_fields=["status"])
                self.buyin(expected=400)
        self.assertFalse(BuyInEvent.objects.exists())

    def test_invalid_buyin_type_is_rejected(self):
        self.buyin("INVALID", expected=400)
        self.assertFalse(BuyInEvent.objects.exists())

    def test_entry_capacity_is_enforced(self):
        self.poker.total_entries_cache = self.poker.max_entries
        self.poker.save(update_fields=["total_entries_cache"])
        self.buyin(expected=400)
        self.assertFalse(TournamentEntry.objects.exists())

    def test_addon_limit_is_enforced_after_approval(self):
        entry = self.enter(approve=True)
        entry.total_addons_cache = self.poker.max_addons
        entry.save(update_fields=["total_addons_cache"])
        self.buyin("ADDON", expected=400)
        self.player.refresh_from_db()
        self.assertEqual(self.player.money, 900)

    def test_other_owner_cannot_manage_entry(self):
        entry = self.enter()
        self.client.force_authenticate(self.other)
        for action in ["approve", "reject", "bust"]:
            with self.subTest(action=action):
                response = self.client.patch(
                    reverse(f"entry-{action}", kwargs={"entry_id": entry.id}),
                    {},
                    format="json",
                )
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.json(), ["Not your tournament."])
        entry.refresh_from_db()
        self.assertEqual(entry.approval_status, "PENDING")

    def test_cancel_refunds_all_unrefunded_events_and_resets_poker_counts(self):
        entry = self.enter(approve=True)
        self.buyin("ADDON")
        self.manage("reject", entry)
        self.buyin("ADDON")
        self.manage("approve", entry)
        self.client.force_authenticate(self.owner)
        url = reverse("tournament-cancel", kwargs={"tournament_id": self.tournament.id})
        self.assertEqual(self.client.post(url).status_code, 200)
        self.player.refresh_from_db()
        self.poker.refresh_from_db()
        self.tournament.refresh_from_db()
        self.assertEqual(self.player.money, 1000)
        self.assertEqual(self.tournament.status, "CANCELED")
        self.assertEqual(self.tournament.live_players_cache, 0)
        self.assertEqual(
            (
                self.poker.total_entries_cache,
                self.poker.total_reentries_cache,
                self.poker.total_addons_cache,
            ),
            (0, 0, 0),
        )
        self.assertFalse(entry.buyin_events.filter(refunded=False).exists())

    def test_list_filters_and_pagination(self):
        response = self.client.get(
            reverse("tournament-list"),
            {"game_type": "POKER", "status": "RUNNING", "page_size": 1},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], self.tournament.id)
        self.assertIsNone(response.data["results"][0]["primary_image"])
        self.assertEqual(
            self.client.get(reverse("tournament-list"), {"game_type": "CHESS"}).data[
                "count"
            ],
            0,
        )

    def test_my_tournaments_and_detail_include_only_own_entries(self):
        entry = self.enter()
        response = self.client.get(reverse("my-tournaments"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        url = reverse(
            "my-tournament-detail", kwargs={"tournament_id": self.tournament.id}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["entry"]["id"], entry.id)
        self.assertEqual(response.data["entry"]["buyin_events"][0]["amount"], 100)
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get(reverse("my-tournaments")).data["count"], 0)
        self.assertEqual(self.client.get(url).status_code, 400)

    def test_shop_detail_and_entries_are_owner_scoped(self):
        self.enter()
        self.client.force_authenticate(self.owner)
        detail = reverse("shop-tournament-detail", kwargs={"pk": self.tournament.id})
        entries = reverse("shop-tournament-entries", kwargs={"pk": self.tournament.id})
        response = self.client.get(detail)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("entries", response.data)
        response = self.client.get(entries)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["player_email"], self.player.email)
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get(detail).status_code, 404)
        self.assertEqual(self.client.get(entries).data["count"], 0)

    def test_create_and_edit_multipart_tournament(self):
        self.client.force_authenticate(self.owner)
        data = {
            "title": "Chess",
            "game_type": "CHESS",
            "start_time": self.start.isoformat(),
            "registration_deadline": self.start.isoformat(),
            "entry_fee": 100,
            "max_participants": 10,
            "prize_structure": json.dumps({"1": 500}),
        }
        response = self.client.post(
            reverse("tournament-create"), data, format="multipart"
        )
        self.assertEqual(response.status_code, 201, response.data)
        created = Tournament.objects.get(id=response.data["data"]["id"])
        self.assertEqual(created.shop_id, self.shop.id)
        self.assertEqual(created.prize_structure, {"1": 500})
        self.assertFalse(PokerTournament.objects.filter(tournament=created).exists())
        response = self.client.patch(
            reverse("tournament-edit", kwargs={"pk": created.id}),
            {"title": "Renamed", "prize_structure": json.dumps({"1": 600})},
            format="multipart",
        )
        self.assertEqual(response.status_code, 200, response.data)
        created.refresh_from_db()
        self.assertEqual(created.title, "Renamed")
        self.assertEqual(created.prize_structure, {"1": 600})

    def test_edit_rejects_deadline_before_start(self):
        self.client.force_authenticate(self.owner)
        response = self.client.patch(
            reverse("tournament-edit", kwargs={"pk": self.tournament.id}),
            {"registration_deadline": (self.start - timedelta(hours=1)).isoformat()},
            format="multipart",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "Registration deadline must be equal to or after start time.",
            response.data["non_field_errors"],
        )

    def test_other_owner_cannot_edit_tournament(self):
        Shop.objects.create(owner=self.other, name="Other shop")
        self.client.force_authenticate(self.other)
        response = self.client.patch(
            reverse("tournament-edit", kwargs={"pk": self.tournament.id}),
            {"title": "Forbidden"},
            format="multipart",
        )
        self.assertEqual(response.status_code, 403)
        self.tournament.refresh_from_db()
        self.assertEqual(self.tournament.title, "Poker")

    def test_create_poker_with_nested_settings(self):
        self.client.force_authenticate(self.owner)
        poker_data = {
            "max_entries": 10,
            "max_reentries": 2,
            "max_addons": 3,
            "starting_chips": 1000,
            "reentry_chips": 1000,
            "addon_chips": 500,
            "blind_structure": self.poker.blind_structure,
            "reentry_fee": 80,
            "addon_fee": 50,
        }
        response = self.client.post(
            reverse("tournament-create"),
            self.create_payload(
                game_type="POKER", poker_tournament=json.dumps(poker_data)
            ),
            format="multipart",
        )
        self.assertEqual(response.status_code, 201, response.data)
        created = Tournament.objects.get(id=response.data["data"]["id"])
        self.assertEqual(created.poker_tournament.addon_fee, 50)
        self.assertEqual(
            created.poker_tournament.blind_structure, self.poker.blind_structure
        )

    def test_create_rejects_missing_poker_settings_and_past_start(self):
        self.client.force_authenticate(self.owner)
        for data, message in [
            (
                self.create_payload(game_type="POKER"),
                "Poker tournament settings are required for poker tournaments.",
            ),
            (
                self.create_payload(
                    start_time=(timezone.now() - timedelta(days=1)).isoformat()
                ),
                "Start time must be in the future.",
            ),
        ]:
            with self.subTest(message=message):
                response = self.client.post(
                    reverse("tournament-create"), data, format="multipart"
                )
                self.assertEqual(response.status_code, 400)
                self.assertIn(message, response.data["non_field_errors"])
        self.assertEqual(Tournament.objects.count(), 1)

    def test_images_create_preserve_and_replace_primary(self):
        self.client.force_authenticate(self.owner)
        response = self.client.post(
            reverse("tournament-create"),
            self.create_payload(
                images=[self.image_file("first.png"), self.image_file("second.png")]
            ),
            format="multipart",
        )
        self.assertEqual(response.status_code, 201, response.data)
        created = Tournament.objects.get(id=response.data["data"]["id"])
        primary = created.images.get(is_primary=True)
        secondary = created.images.get(is_primary=False)
        url = reverse("tournament-edit", kwargs={"pk": created.id})
        self.assertEqual(
            self.client.patch(
                url, {"title": "No image change"}, format="multipart"
            ).status_code,
            200,
        )
        self.assertEqual(created.images.count(), 2)
        response = self.client.patch(
            url,
            {
                "existing_image_ids": json.dumps([secondary.id]),
                "images": [self.image_file("replacement.png")],
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertFalse(created.images.filter(id=primary.id).exists())
        self.assertTrue(created.images.filter(id=secondary.id).exists())
        self.assertEqual(created.images.count(), 2)
        new_primary = created.images.get(is_primary=True)
        self.assertNotEqual(new_primary.id, secondary.id)
        self.assertIn("replacement", new_primary.image.name)

    def test_reject_reentry_restores_busted_status_and_refunds(self):
        entry = self.enter(approve=True)
        self.manage("bust", entry)
        self.buyin("REENTRY")
        self.manage("reject", entry)
        self.player.refresh_from_db()
        self.assertEqual(self.player.money, 900)
        self.assertEqual(entry.status, "BUSTED")
        self.assertEqual(entry.total_reentries_cache, 0)
        self.assertTrue(entry.buyin_events.get(type="REENTRY").refunded)

    def test_addon_and_reentry_limits_of_zero_disable_requests(self):
        entry = self.enter(approve=True)
        self.poker.max_addons = 0
        self.poker.max_reentries = 0
        self.poker.save(update_fields=["max_addons", "max_reentries"])
        self.buyin("ADDON", expected=400)
        self.manage("bust", entry)
        self.buyin("REENTRY", expected=400)
        self.player.refresh_from_db()
        self.assertEqual(self.player.money, 900)

    def test_cancel_rejects_other_owner_and_finished_tournament(self):
        url = reverse("tournament-cancel", kwargs={"tournament_id": self.tournament.id})
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.post(url).status_code, 400)
        self.client.force_authenticate(self.owner)
        self.tournament.status = "FINISHED"
        self.tournament.save(update_fields=["status"])
        self.assertEqual(self.client.post(url).status_code, 400)
        self.tournament.refresh_from_db()
        self.assertEqual(self.tournament.status, "FINISHED")
