from odoo import http
from odoo.tests.common import HttpCase, JsonRpcException, new_test_user, tagged


@tagged("post_install", "-at_install")
class TestWireLoginAs(HttpCase):
    @classmethod
    def setUpClass(cls):
        """Create one internal and one portal target user."""
        super().setUpClass()
        cls.internal = new_test_user(cls.env, "internal_user")
        cls.portal = new_test_user(cls.env, "portal_user", groups="base.group_portal")

    def _login_as(self, user):
        """Press the "Anmelden als" button on ``user`` through JSON-RPC.

        :param res.users user: target user of the switch
        :return: action returned by the button
        :rtype: dict
        """
        return self.make_jsonrpc_request(
            "/web/dataset/call_button/res.users/action_wire_login_as",
            {"model": "res.users", "method": "action_wire_login_as", "args": [[user.id]], "kwargs": {}},
        )

    def _session_uid(self):
        """Return the uid of the current test session.

        :return: id of the logged-in user, or None for an anonymous session
        :rtype: int | None
        """
        return self.make_jsonrpc_request("/web/session/get_session_info")["uid"]

    def test_admin_switches_to_internal_user(self):
        """Admin pressing the button ends up in a session of the internal user."""
        self.authenticate("admin", "admin")
        self._login_as(self.internal)
        self.assertEqual(self._session_uid(), self.internal.id)

    def test_non_system_user_cannot_switch(self):
        """A user without base.group_system gets an error from the button."""
        other = new_test_user(self.env, "other_user")
        self.authenticate("internal_user", "internal_user")
        with self.assertRaises(JsonRpcException):
            self._login_as(other)

    def test_switch_to_portal_user_is_rejected(self):
        """Switching to a portal user is rejected."""
        self.authenticate("admin", "admin")
        with self.assertRaises(JsonRpcException):
            self._login_as(self.portal)

    def test_login_as_type_without_session_is_rejected(self):
        """POST with type wire_login_as and no session stays on the login form."""
        self.authenticate(None, None)
        res = self.url_open(
            "/web/login",
            data={
                "login": "internal_user",
                "password": "unused",
                "type": "wire_login_as",
                "csrf_token": http.Request.csrf_token(self),
            },
        )
        self.assertTrue(res.request.path_url.startswith("/web/login"))
