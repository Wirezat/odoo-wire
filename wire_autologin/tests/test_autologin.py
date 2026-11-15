from odoo import http
from odoo.tests.common import HttpCase, new_test_user, tagged


@tagged("post_install", "-at_install")
class TestWireAutologin(HttpCase):
    def setUp(self):
        """Start every test with an anonymous session cookie."""
        super().setUp()
        self.authenticate(None, None)

    def _post_login(self, login, credential_type, headers=None):
        """POST the login form with an explicit credential type.

        :param str login: login sent in the form
        :param str credential_type: value of the ``type`` form field
        :param dict headers: extra request headers, e.g. ``Remote-Groups``
        :return: final response after redirects
        :rtype: requests.Response
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

    def test_remote_user_type_with_eco_header_logs_in_admin(self):
        """POST with type wire_remote_user and group eco signs in admin."""
        res = self._post_login("admin", "wire_remote_user", headers={"Remote-Groups": "eco"})
        self.assertEqual(res.request.path_url, "/odoo")

    def test_remote_user_type_without_header_is_rejected(self):
        """POST with type wire_remote_user but no header stays on the login form."""
        res = self._post_login("admin", "wire_remote_user")
        self.assertTrue(res.request.path_url.startswith("/web/login"))

    def test_remote_user_type_for_other_login_is_rejected(self):
        """POST with type wire_remote_user for a non-admin login stays on the login form."""
        new_test_user(self.env, "internal_user")
        res = self._post_login("internal_user", "wire_remote_user", headers={"Remote-Groups": "eco"})
        self.assertTrue(res.request.path_url.startswith("/web/login"))

    def _session_uid(self):
        """Return the uid of the current test session.

        :return: id of the logged-in user, or None for an anonymous session
        :rtype: int | None
        """
        return self.make_jsonrpc_request("/web/session/get_session_info")["uid"]

    def test_eco_header_logs_in_admin(self):
        """GET with group eco among several groups signs in admin and redirects to /odoo."""
        res = self.url_open("/web/login", headers={"Remote-Groups": "admin, eco"})
        self.assertEqual(res.request.path_url, "/odoo")
        self.assertEqual(self._session_uid(), self.env.ref("base.user_admin").id)

    def test_header_without_eco_shows_form(self):
        """GET with a header lacking eco shows the regular login form."""
        res = self.url_open("/web/login", headers={"Remote-Groups": "admin"})
        self.assertTrue(res.request.path_url.startswith("/web/login"))
        self.assertIn('name="password"', res.text)

    def test_no_autologin_shows_form(self):
        """GET with no_autologin shows the regular login form despite group eco."""
        res = self.url_open("/web/login?no_autologin=1", headers={"Remote-Groups": "eco"})
        self.assertIn('name="password"', res.text)

    def test_archived_admin_shows_form(self):
        """GET with group eco and archived admin shows the regular form instead of an error."""
        self.env.ref("base.user_admin").active = False
        res = self.url_open("/web/login", headers={"Remote-Groups": "eco"})
        self.assertEqual(res.status_code, 200)
        self.assertIn('name="password"', res.text)
