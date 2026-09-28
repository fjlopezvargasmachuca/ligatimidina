from django.test import TestCase
from rest_framework.test import APITestCase

from .models import Player


class CurrentPlayerAPITest(APITestCase):

    def setUp(self):
        self.player = Player.objects.create_user(
            username="test_player",
            password="test1234",
            display_name="Test Player",
        )

    def test_anonymous_user_cannot_access_current_player(self):
        response = self.client.get(
            "/api/accounts/me/"
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_authenticated_user_can_access_current_player(self):
        self.client.force_authenticate(
            user=self.player
        )

        response = self.client.get(
            "/api/accounts/me/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["id"],
            self.player.id,
        )

        self.assertEqual(
            response.data["username"],
            "test_player",
        )

        self.assertEqual(
            response.data["display_name"],
            "Test Player",
        )

        self.assertNotIn(
            "password",
            response.data,
        )

    def test_user_can_login(self):
        response = self.client.post(
            "/api/accounts/login/",
            {
                "username": "test_player",
                "password": "test1234",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["username"],
            "test_player",
        )

        self.assertEqual(
            response.data["display_name"],
            "Test Player",
        )

        self.assertNotIn(
            "password",
            response.data,
        )

        me_response = self.client.get(
            "/api/accounts/me/"
        )

        self.assertEqual(
            me_response.status_code,
            200,
        )

        self.assertEqual(
            me_response.data["username"],
            "test_player",
        )

    def test_user_cannot_login_with_invalid_password(self):
        response = self.client.post(
            "/api/accounts/login/",
            {
                "username": "test_player",
                "password": "password_incorrecta",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertIn(
            "non_field_errors",
            response.data,
        )

        me_response = self.client.get(
            "/api/accounts/me/"
        )

        self.assertEqual(
            me_response.status_code,
            403,
        )

    def test_user_can_logout(self):
        self.client.force_authenticate(
            user=self.player
        )

        response = self.client.post(
            "/api/accounts/logout/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["detail"],
            "Sesión cerrada correctamente.",
        )

        self.client.force_authenticate(
            user=None
        )

        me_response = self.client.get(
            "/api/accounts/me/"
        )

        self.assertEqual(
            me_response.status_code,
            403,
        )

    def test_user_can_register(self):
        response = self.client.post(
            "/api/accounts/register/",
            {
                "username": "nuevo",
                "display_name": "Nuevo jugador",
                "first_name": "Nombre",
                "last_name": "Apellidos",
                "terms_accepted": True,
                "email": "nuevo@example.com",
                "password": "LigaTimidina123!",
                "password_confirm": "LigaTimidina123!",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data["pending_approval"])
        user = Player.objects.get(username="nuevo")
        self.assertEqual(user.email, "nuevo@example.com")
        self.assertFalse(user.is_active)
        self.assertTrue(user.check_password("LigaTimidina123!"))

    def test_user_cannot_register_with_different_passwords(self):
        response = self.client.post(
            "/api/accounts/register/",
            {
                "username": "nuevo",
                "display_name": "Nuevo jugador",
                "first_name": "Nombre",
                "last_name": "Apellidos",
                "terms_accepted": True,
                "email": "nuevo@example.com",
                "password": "LigaTimidina123!",
                "password_confirm": "OtraClave456!",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("password_confirm", response.data)

    def test_user_cannot_register_with_existing_username(self):
        response = self.client.post(
            "/api/accounts/register/",
            {
                "username": self.player.username,
                "display_name": "Otro jugador",
                "first_name": "Nombre",
                "last_name": "Apellidos",
                "terms_accepted": True,
                "email": "otro@example.com",
                "password": "LigaTimidina123!",
                "password_confirm": "LigaTimidina123!",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("username", response.data)

    def test_user_is_logged_in_after_register(self):
        response = self.client.post(
            "/api/accounts/register/",
            {
                "username": "pendiente",
                "display_name": "Pendiente",
                "first_name": "Nombre",
                "last_name": "Apellidos",
                "terms_accepted": True,
                "email": "pendiente@example.com",
                "password": "LigaTimidina123!",
                "password_confirm": "LigaTimidina123!",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        me_response = self.client.get("/api/accounts/me/")
        self.assertEqual(me_response.status_code, 403)
        login_response = self.client.post(
            "/api/accounts/login/",
            {"username": "pendiente", "password": "LigaTimidina123!"},
            format="json",
        )
        self.assertEqual(login_response.status_code, 400)
        self.assertIn("bloqueada o pendiente", str(login_response.data).lower())

    def test_user_can_update_profile(self):
        self.client.force_authenticate(
            user=self.player
        )

        response = self.client.patch(
            "/api/accounts/profile/",
            {
                "display_name": "Nombre Actualizado",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["display_name"],
            "Nombre Actualizado",
        )

        self.player.refresh_from_db()

        self.assertEqual(
            self.player.display_name,
            "Nombre Actualizado",
        )

    def test_anonymous_user_cannot_update_profile(self):
        response = self.client.patch(
            "/api/accounts/profile/",
            {
                "display_name": "Nombre Actualizado",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_user_cannot_change_username_from_profile(self):
        self.client.force_authenticate(
            user=self.player
        )

        response = self.client.patch(
            "/api/accounts/profile/",
            {
                "username": "otro_usuario",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.player.refresh_from_db()

        self.assertEqual(
            self.player.username,
            "test_player",
        )

    def test_user_can_change_password(self):
        self.client.force_authenticate(
            user=self.player
        )

        response = self.client.post(
            "/api/accounts/change-password/",
            {
                "current_password": "test1234",
                "new_password": "nueva1234",
                "new_password_confirm": "nueva1234",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["detail"],
            "Contraseña actualizada correctamente.",
        )

        self.player.refresh_from_db()

        self.assertTrue(
            self.player.check_password("nueva1234")
        )

    def test_user_cannot_change_password_with_wrong_current_password(self):
        self.client.force_authenticate(
            user=self.player
        )

        response = self.client.post(
            "/api/accounts/change-password/",
            {
                "current_password": "password_incorrecta",
                "new_password": "nueva1234",
                "new_password_confirm": "nueva1234",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertIn(
            "current_password",
            response.data,
        )

        self.player.refresh_from_db()

        self.assertTrue(
            self.player.check_password("test1234")
        )

    def test_user_cannot_change_password_with_different_new_passwords(self):
        self.client.force_authenticate(
            user=self.player
        )

        response = self.client.post(
            "/api/accounts/change-password/",
            {
                "current_password": "test1234",
                "new_password": "nueva1234",
                "new_password_confirm": "otra1234",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertIn(
            "new_password_confirm",
            response.data,
        )

    def test_anonymous_user_cannot_change_password(self):
        response = self.client.post(
            "/api/accounts/change-password/",
            {
                "current_password": "test1234",
                "new_password": "nueva1234",
                "new_password_confirm": "nueva1234",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_user_remains_authenticated_after_changing_password(self):
        self.client.force_authenticate(
            user=self.player
        )

        response = self.client.post(
            "/api/accounts/change-password/",
            {
                "current_password": "test1234",
                "new_password": "nueva1234",
                "new_password_confirm": "nueva1234",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        me_response = self.client.get(
            "/api/accounts/me/"
        )

        self.assertEqual(
            me_response.status_code,
            200,
        )

        self.assertEqual(
            me_response.data["username"],
            "test_player",
        )

    def test_user_cannot_update_profile_with_blank_display_name(self):
        self.client.force_authenticate(
            user=self.player
        )

        response = self.client.patch(
            "/api/accounts/profile/",
            {
                "display_name": "   ",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertIn(
            "display_name",
            response.data,
        )

        self.player.refresh_from_db()

        self.assertEqual(
            self.player.display_name,
            "Test Player",
        )

class AdminPlayerManagementAPITest(APITestCase):
    def setUp(self):
        self.admin = Player.objects.create_user(
            username="admin_accounts",
            password="AdminPass123!",
            display_name="Admin Accounts",
            is_staff=True,
        )
        self.player = Player.objects.create_user(
            username="managed_player",
            password="PlayerPass123!",
            display_name="Managed Player",
        )

    def test_non_admin_cannot_list_admin_players(self):
        self.client.force_authenticate(user=self.player)

        response = self.client.get("/api/accounts/admin/players/")

        self.assertEqual(response.status_code, 403)

    def test_admin_can_list_active_and_inactive_players(self):
        inactive = Player.objects.create_user(
            username="inactive_player",
            password="PlayerPass123!",
            display_name="Inactive Player",
            is_active=False,
        )
        self.client.force_authenticate(user=self.admin)

        response = self.client.get("/api/accounts/admin/players/")

        self.assertEqual(response.status_code, 200)
        ids = {item["id"] for item in response.data}
        self.assertIn(self.player.id, ids)
        self.assertIn(inactive.id, ids)

    def test_admin_can_create_player(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.post(
            "/api/accounts/admin/players/",
            {
                "username": "new_admin_created_player",
                "display_name": "Alta desde administración",
                "email": "alta@example.com",
                "password": "TempPass123!",
                "password_confirm": "TempPass123!",
                "is_active": True,
                "is_staff": False,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        created = Player.objects.get(username="new_admin_created_player")
        self.assertEqual(created.display_name, "Alta desde administración")
        self.assertTrue(created.check_password("TempPass123!"))
        self.assertFalse(created.is_staff)
        self.assertNotIn("password", response.data)

    def test_admin_can_edit_and_deactivate_player(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            f"/api/accounts/admin/players/{self.player.id}/",
            {"display_name": "Jugador Editado", "is_active": False},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.player.refresh_from_db()
        self.assertEqual(self.player.display_name, "Jugador Editado")
        self.assertFalse(self.player.is_active)

    def test_admin_cannot_deactivate_or_demote_self(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.patch(
            f"/api/accounts/admin/players/{self.admin.id}/",
            {
                "is_active": False,
                "is_staff": False,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)
        self.assertTrue(self.admin.is_staff)

    def test_admin_can_reset_player_password(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.post(
            f"/api/accounts/admin/players/{self.player.id}/reset-password/",
            {
                "new_password": "ResetPass123!",
                "new_password_confirm": "ResetPass123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.player.refresh_from_db()
        self.assertTrue(self.player.check_password("ResetPass123!"))

    def test_admin_password_reset_requires_matching_passwords(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.post(
            f"/api/accounts/admin/players/{self.player.id}/reset-password/",
            {
                "new_password": "ResetPass123!",
                "new_password_confirm": "DifferentPass123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("new_password_confirm", response.data)

    def test_normal_admin_cannot_block_another_admin(self):
        other_admin = Player.objects.create_user(
            username="other_admin", password="OtherAdmin123!", display_name="Other Admin",
            email="otheradmin@example.com", is_staff=True,
        )
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            f"/api/accounts/admin/players/{other_admin.id}/",
            {"is_active": False}, format="json",
        )
        self.assertEqual(response.status_code, 400)
        other_admin.refresh_from_db()
        self.assertTrue(other_admin.is_active)

    def test_superadmin_can_demote_and_block_admin(self):
        superadmin = Player.objects.create_superuser(
            username="superadmin", password="SuperAdmin123!", email="superadmin@example.com",
            display_name="Super Admin",
        )
        other_admin = Player.objects.create_user(
            username="admin_target", password="AdminTarget123!", email="admintarget@example.com",
            display_name="Admin Target", is_staff=True,
        )
        self.client.force_authenticate(user=superadmin)
        response = self.client.patch(
            f"/api/accounts/admin/players/{other_admin.id}/",
            {"is_staff": False, "is_active": False}, format="json",
        )
        self.assertEqual(response.status_code, 200)
        other_admin.refresh_from_db()
        self.assertFalse(other_admin.is_staff)
        self.assertFalse(other_admin.is_active)

