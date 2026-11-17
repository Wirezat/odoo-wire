from odoo import http
from odoo.exceptions import AccessError
from odoo.tests.common import HttpCase, new_test_user, tagged

ECO_HEADERS = {"Remote-Groups": "admin, eco", "Remote-User": "wirezat"}


@tagged("post_install", "-at_install")
class TestWireAutologin(HttpCase):
    def setUp(self):
        """Start every test anonymously, in table mode, with admin carrying the Authelia user ``wirezat``."""
        super().setUp()
        self.admin = self.env.ref("base.user_admin")
        self.env["ir.config_parameter"].set_param("wire_autologin.mode", "table")
        self.admin.sudo().wire_remote_user = "wirezat"
        self.authenticate(None, None)

    def _post_login(self, login, credential_type, headers=None):
        """POST the login form with an explicit credential type.

        Args:
            login (str): Login sent in the form.
            credential_type (str): Value of the ``type`` form field.
            headers (dict): Extra request headers, e.g. ``Remote-Groups``.

        Returns:
            requests.Response: Final response after redirects.
        """
        return self.url_open(
            "/web/login",
            data={
                "login": login,
                "password": "unused",
                "type": credential_type,
                "csrf_token": http.Request.csrf_token(self),
            },
            headers=headers,
        )

    def _session_uid(self):
        """Return the uid of the current test session.

        Returns:
            int | None: Id of the logged-in user, or None for an anonymous session.
        """
        return self.make_jsonrpc_request("/web/session/get_session_info")["uid"]

    def _assert_login_form(self, res):
        """Assert that the response is the regular login form.

        Args:
            res (requests.Response): Response to check.
        """
        self.assertEqual(res.status_code, 200)
        self.assertIn('name="password"', res.text)

    def test_remote_user_type_for_mapped_login_logs_in(self):
        """POST with type wire_remote_user for the mapped login signs that user in."""
        res = self._post_login("admin", "wire_remote_user", headers=ECO_HEADERS)
        self.assertEqual(res.request.path_url, "/odoo")

    def test_remote_user_type_without_header_is_rejected(self):
        """POST with type wire_remote_user but no header stays on the login form."""
        res = self._post_login("admin", "wire_remote_user")
        self.assertTrue(res.request.path_url.startswith("/web/login"))

    def test_remote_user_type_for_other_login_is_rejected(self):
        """POST with type wire_remote_user for a login other than the mapped one stays on the login form."""
        new_test_user(self.env, "internal_user")
        res = self._post_login("internal_user", "wire_remote_user", headers=ECO_HEADERS)
        self.assertTrue(res.request.path_url.startswith("/web/login"))

    def test_table_mode_logs_in_mapped_user(self):
        """GET in table mode signs in the user mapped to Remote-User and redirects to /odoo."""
        res = self.url_open("/web/login", headers=ECO_HEADERS)
        self.assertEqual(res.request.path_url, "/odoo")
        self.assertEqual(self._session_uid(), self.admin.id)

    def test_table_mode_without_mapping_shows_form(self):
        """GET in table mode for an unmapped Remote-User shows the regular form."""
        self._assert_login_form(self.url_open("/web/login", headers={**ECO_HEADERS, "Remote-User": "nobody"}))

    def test_email_mode_logs_in_user_with_matching_login(self):
        """GET in email mode signs in the user whose login equals Remote-Email, ignoring case."""
        user = new_test_user(self.env, "sso.user@example.com")
        self.env["ir.config_parameter"].set_param("wire_autologin.mode", "email")
        self.url_open("/web/login", headers={**ECO_HEADERS, "Remote-Email": "SSO.User@example.com"})
        self.assertEqual(self._session_uid(), user.id)

    def test_email_mode_without_match_shows_form(self):
        """GET in email mode with an unknown Remote-Email shows the regular form."""
        self.env["ir.config_parameter"].set_param("wire_autologin.mode", "email")
        headers = {**ECO_HEADERS, "Remote-Email": "unknown@example.com"}
        self._assert_login_form(self.url_open("/web/login", headers=headers))

    def test_email_mode_with_ambiguous_email_shows_form(self):
        """GET in email mode shows the regular form when two users share Remote-Email."""
        new_test_user(self.env, "dup_one", email="dup@example.com")
        new_test_user(self.env, "dup_two", email="dup@example.com")
        self.env["ir.config_parameter"].set_param("wire_autologin.mode", "email")
        self._assert_login_form(self.url_open("/web/login", headers={**ECO_HEADERS, "Remote-Email": "dup@example.com"}))

    def test_header_without_eco_shows_form(self):
        """GET without group eco shows the regular form even for a mapped Remote-User."""
        self._assert_login_form(self.url_open("/web/login", headers={**ECO_HEADERS, "Remote-Groups": "admin"}))

    def test_no_autologin_shows_form(self):
        """GET with no_autologin shows the regular form despite a mapped Remote-User."""
        self._assert_login_form(self.url_open("/web/login?no_autologin=1", headers=ECO_HEADERS))

    def test_logout_behind_authelia_redirects_to_authelia_logout(self):
        """Logout with Authelia headers redirects to the Authelia logout URL with the Odoo target as ``rd``."""
        self.env["ir.config_parameter"].set_param("wire_autologin.logout_url", "https://auth.example.com/logout")
        self.url_open("/web/login", headers=ECO_HEADERS)
        res = self.url_open("/web/session/logout", headers=ECO_HEADERS, allow_redirects=False)
        location = res.headers["Location"]
        self.assertTrue(location.startswith("https://auth.example.com/logout?rd="), location)
        self.assertTrue(location.endswith("%2Fodoo"), location)

    def test_archived_target_shows_form(self):
        """GET for a mapped but archived user shows the regular form instead of an error."""
        self.admin.active = False
        self._assert_login_form(self.url_open("/web/login", headers=ECO_HEADERS))

    def test_authelia_field_needs_group(self):
        """A system user without the group "Authelia-Benutzer verwalten" cannot set the Authelia user."""
        sysadmin = new_test_user(self.env, "sysadmin", groups="base.group_system")
        target = new_test_user(self.env, "target_user")
        with self.assertRaises(AccessError):
            target.with_user(sysadmin).write({"wire_remote_user": "someone"})
