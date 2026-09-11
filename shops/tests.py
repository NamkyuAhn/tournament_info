from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

from shops.models import Shop


class ShopAPITests(APITestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(
            username="owner", email="owner@example.com", role="SHOP_OWNER"
        )
        self.other = get_user_model().objects.create_user(
            username="other", email="other@example.com", role="SHOP_OWNER"
        )
        self.other_shop = Shop.objects.create(owner=self.other, name="Other shop")
        self.client.force_authenticate(self.owner)
        self.create_url = reverse("shop-create")
        self.update_url = reverse("shop-update")

    def test_create_assigns_authenticated_owner(self):
        response = self.client.post(
            self.create_url, {"name": "My shop", "owner": self.other.id}
        )
        self.assertEqual(response.status_code, 201)
        shop = Shop.objects.get(owner=self.owner)
        self.assertEqual(response.json(), {"id": shop.id, "name": "My shop"})

    def test_create_rejects_second_shop(self):
        Shop.objects.create(owner=self.owner, name="My shop")
        response = self.client.post(self.create_url, {"name": "Second shop"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"detail": "shop already exists"})
        self.assertEqual(Shop.objects.filter(owner=self.owner).count(), 1)

    def test_create_requires_unique_nonempty_name(self):
        for data, message in [
            ({}, "name required"),
            ({"name": ""}, "name required"),
            ({"name": "Other shop"}, "shop name already exists"),
        ]:
            with self.subTest(data=data):
                response = self.client.post(self.create_url, data)
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.json(), {"detail": message})
        self.assertFalse(Shop.objects.filter(owner=self.owner).exists())

    def test_update_only_changes_own_shop(self):
        shop = Shop.objects.create(owner=self.owner, name="My shop")
        response = self.client.patch(
            self.update_url, {"name": "Renamed", "id": self.other_shop.id}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"id": shop.id, "name": "Renamed"})
        self.other_shop.refresh_from_db()
        self.assertEqual(self.other_shop.name, "Other shop")

    def test_update_allows_unchanged_name(self):
        Shop.objects.create(owner=self.owner, name="My shop")
        self.assertEqual(
            self.client.patch(self.update_url, {"name": "My shop"}).status_code, 200
        )

    def test_update_rejects_missing_or_duplicate_name(self):
        shop = Shop.objects.create(owner=self.owner, name="My shop")
        for data, message in [
            ({}, "name required"),
            ({"name": "Other shop"}, "shop name already exists"),
        ]:
            with self.subTest(data=data):
                response = self.client.patch(self.update_url, data)
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.json(), {"detail": message})
                shop.refresh_from_db()
                self.assertEqual(shop.name, "My shop")

    def test_update_requires_existing_shop(self):
        response = self.client.patch(self.update_url, {"name": "New"})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "shop does not exist"})

    def test_player_cannot_create_or_update_shop(self):
        self.owner.role = "PLAYER"
        self.owner.save(update_fields=["role"])
        for method, url in [
            (self.client.post, self.create_url),
            (self.client.patch, self.update_url),
        ]:
            response = method(url, {"name": "Forbidden"})
            self.assertEqual(response.status_code, 403)
            self.assertEqual(response.json(), {"detail": "only shop owner allowed"})

    def test_anonymous_requests_are_rejected(self):
        self.client.force_authenticate(None)
        self.assertEqual(
            self.client.post(self.create_url, {"name": "No"}).status_code, 401
        )
        self.assertEqual(
            self.client.patch(self.update_url, {"name": "No"}).status_code, 401
        )
