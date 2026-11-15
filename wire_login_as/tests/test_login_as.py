from odoo import http
from odoo.tests.common import HttpCase, JsonRpcException, new_test_user, tagged


@tagged("post_install", "-at_install")
class TestWireLoginAs(HttpCase):
    @classmethod
    def setUpClass(cls):
        """Create a switching user, one internal and one portal target user."""
        super().setUpClass()
        cls.switcher = new_test_user(cls.env, "switcher", groups="base.group_user,wire_login_as.group_switch_user")
        cls.internal = new_test_user(cls.env, "internal_user")
        cls.portal = new_test_user(cls.env, "portal_user", groups="base.group_portal")

    def _login_as(self, user):
        """Run the switch method on ``user`` through JSON-RPC, like the "Wechseln" button.

        :param res.users user: target user of the switch
        :return: action returned by the method
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

    def test_switch_group_member_switches_to_internal_user(self):
        """A member of "Benutzer wechseln" without system rights ends up in a session of the internal user."""
        self.authenticate("switcher", "switcher")
        self._login_as(self.internal)
        self.assertEqual(self._session_uid(), self.internal.id)

    def test_user_without_switch_group_cannot_switch(self):
        """A user without the group "Benutzer wechseln" gets an error."""
        other = new_test_user(self.env, "other_user")
        self.authenticate("internal_user", "internal_user")
        with self.assertRaises(JsonRpcException):
            self._login_as(other)

    def test_switch_to_portal_user_is_rejected(self):
        """Switching to a portal user is rejected."""
        self.authenticate("switcher", "switcher")
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

    def test_gear_action_switches_to_record_user(self):
        """The gear menu action "Benutzer wechseln" on a user form switches into that user."""
        action = self.env.ref("wire_login_as.action_server_switch_user")
        self.authenticate("switcher", "switcher")
        self.make_jsonrpc_request(
            "/web/action/run",
            {
                "action_id": action.id,
                "context": {
                    "active_model": "res.users",
                    "active_id": self.internal.id,
                    "active_ids": [self.internal.id],
                },
            },
        )
        self.assertEqual(self._session_uid(), self.internal.id)
