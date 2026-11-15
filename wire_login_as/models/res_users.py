from odoo import models
from odoo.exceptions import AccessDenied
from odoo.http import request

CREDENTIAL_TYPE = "wire_login_as"


class ResUsers(models.Model):
    _inherit = "res.users"

    def _check_credentials(self, credential, env):
        """Accept the ``wire_login_as`` credential when a system user switches to an active internal user.

        The switching user is taken from the current session; ``self.env.user`` is the target here.

        :param dict credential: login credential with at least ``type``
        :param dict env: authentication environment passed by ``authenticate``
        :return: auth_info with ``uid``, ``auth_method`` and ``mfa``
        :rtype: dict
        :raise AccessDenied: if neither a parent method nor this rule accepts the credential
        """
        try:
            return super()._check_credentials(credential, env)
        except AccessDenied:
            target = self.env.user
            if not (
                credential["type"] == CREDENTIAL_TYPE
                and request
                and request.session.uid
                and self.env["res.users"].sudo().browse(request.session.uid).has_group("base.group_system")
                and target.active
                and not target.share
            ):
                raise
            return {"uid": target.id, "auth_method": CREDENTIAL_TYPE, "mfa": "skip"}

    def action_wire_login_as(self):
        """Replace the current session with a session of this user, without password.

        :return: URL action that reloads the web client as the new user
        :rtype: dict
        """
        self.ensure_one()
        request.session.authenticate(request.env, {"login": self.login, "type": CREDENTIAL_TYPE})
        return {"type": "ir.actions.act_url", "url": "/odoo", "target": "self"}
