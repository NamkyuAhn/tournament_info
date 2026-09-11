from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from shops.models import Shop


class UserAPITests(APITestCase):
    def setUp(self):
        self.payload = {
            "email": "player@example.com",
            "password": "test-password-123",
            "name": "Player",
            "role": "PLAYER",
        }
        self.user = get_user_model().objects.create_user(
            username="player", **self.payload
        )

    def test_signup_returns_public_fields_and_hashes_password(self):
        data = {**self.payload, "email": "new@example.com"}
        response = self.client.post("/api/users/signup/", data, format="json")
        self.assertEqual(response.status_code, 201)
        created = get_user_model().objects.get(email=data["email"])
        self.assertEqual(
            response.json(),
            {
                "id": created.id,
                "email": data["email"],
                "name": "Player",
                "role": "PLAYER",
            },
        )
        self.assertTrue(created.check_password(data["password"]))
        self.assertNotEqual(created.password, data["password"])
        self.assertEqual(created.money, 0)

    def test_signup_requires_each_field(self):
        for field in self.payload:
            with self.subTest(field=field):
                data = {**self.payload, "email": "new@example.com"}
                del data[field]
                response = self.client.post("/api/users/signup/", data, format="json")
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.json(), {"detail": "missing required fields"})
        self.assertEqual(get_user_model().objects.count(), 1)

    def test_duplicate_email_is_rejected(self):
        response = self.client.post("/api/users/signup/", self.payload, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"detail": "email already exists"})
        self.assertEqual(get_user_model().objects.count(), 1)

    def test_login_tokens_authenticate_me(self):
        response = self.client.post("/api/users/login/", self.payload, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(AccessToken(response.data["access"])["user_id"], self.user.id)
        self.assertEqual(
            RefreshToken(response.data["refresh"])["user_id"], self.user.id
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
        profile = self.client.get("/api/users/me/")
        self.assertEqual(profile.status_code, 200)
        self.assertEqual(
            profile.json(),
            {
                "id": self.user.id,
                "email": self.user.email,
                "name": "Player",
                "role": "PLAYER",
                "money": 0,
                "shop_name": "",
            },
        )

    def test_login_rejects_wrong_password_and_missing_fields(self):
        for data, code, message in [
            ({}, 400, "email and password required"),
            ({"email": self.user.email}, 400, "email and password required"),
            (
                {"email": self.user.email, "password": "wrong"},
                401,
                "invalid credentials",
            ),
        ]:
            with self.subTest(data=data):
                response = self.client.post("/api/users/login/", data, format="json")
                self.assertEqual(response.status_code, code)
                self.assertEqual(response.json(), {"detail": message})

    def test_inactive_user_cannot_login(self):
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])
        self.assertEqual(
            self.client.post(
                "/api/users/login/", self.payload, format="json"
            ).status_code,
            401,
        )

    def test_private_endpoints_require_authentication(self):
        self.assertEqual(self.client.get("/api/users/me/").status_code, 401)
        self.assertEqual(
            self.client.post("/api/users/charge-money/", {"amount": 100}).status_code,
            401,
        )

    def test_owner_profile_includes_shop_name(self):
        self.user.role = "SHOP_OWNER"
        self.user.save(update_fields=["role"])
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.get("/api/users/me/").data["shop_name"], "")
        Shop.objects.create(owner=self.user, name="My shop")
        self.assertEqual(self.client.get("/api/users/me/").data["shop_name"], "My shop")

    def test_money_charge_accumulates_balance(self):
        self.client.force_authenticate(self.user)
        for amount, balance in [(100, 100), ("200", 300)]:
            response = self.client.post(
                "/api/users/charge-money/", {"amount": amount}, format="json"
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.json(),
                {
                    "message": "Money charged successfully.",
                    "amount": int(amount),
                    "money": balance,
                },
            )
            self.user.refresh_from_db()
            self.assertEqual(self.user.money, balance)

    def test_invalid_charge_does_not_change_balance(self):
        self.client.force_authenticate(self.user)
        for data, message in [
            ({}, "amount is required."),
            ({"amount": None}, "amount is required."),
            ({"amount": "abc"}, "amount must be an integer."),
            ({"amount": "1.5"}, "amount must be an integer."),
            ({"amount": 0}, "amount must be greater than 0."),
            ({"amount": -1}, "amount must be greater than 0."),
        ]:
            with self.subTest(data=data):
                response = self.client.post(
                    "/api/users/charge-money/", data, format="json"
                )
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.json(), {"detail": message})
                self.user.refresh_from_db()
                self.assertEqual(self.user.money, 0)
