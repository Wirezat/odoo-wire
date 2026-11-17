from odoo import fields, models
from odoo.exceptions import AccessDenied
from odoo.http import request

ECO_GROUP = "eco"
CREDENTIAL_TYPE = "wire_remote_user"
MODE_PARAM = "wire_autologin.mode"


def has_eco_group(httprequest):
    """Tell whether the forward-auth header lists the Authelia group ``eco``.

    Args:
        httprequest (werkzeug.wrappers.Request): Incoming HTTP request.

    Returns:
        bool: True if ``Remote-Groups`` contains ``eco`` as one of its comma-separated entries.
    """
    groups = httprequest.headers.get("Remote-Groups", "")
    return ECO_GROUP in (group.strip() for group in groups.split(","))


class ResUsers(models.Model):
    _inherit = "res.users"

    wire_remote_user = fields.Char(string="Authelia-Benutzer", copy=False, groups="wire_autologin.group_authelia_admin")

    _wire_remote_user_unique = models.Constraint(
        "UNIQUE (wire_remote_user)", "Jeder Authelia-Benutzer darf nur einem Odoo-Benutzer zugeordnet sein."
    )

    def _wire_resolve_user(self, httprequest):
        """Find the Odoo user an Authelia request of group ``eco`` signs in as.

        The mode ``wire_autologin.mode`` selects the Authelia user field (``Remote-User``) or the e-mail match
        (``Remote-Email`` against login or e-mail, exactly one active user).

        Args:
            httprequest (werkzeug.wrappers.Request): Incoming HTTP request.

        Returns:
            res.users: The mapped user, or an empty recordset if there is none.
        """
        users = self.env["res.users"].sudo()
        if not has_eco_group(httprequest):
            return users
        if self.env["ir.config_parameter"].sudo().get_param(MODE_PARAM, "table") == "email":
            email = httprequest.headers.get("Remote-Email", "").strip()
            if not email:
                return users
            matches = users.search(["|", ("login", "=ilike", email), ("email", "=ilike", email)], limit=2)
            return matches if len(matches) == 1 else users
        remote_user = httprequest.headers.get("Remote-User", "").strip()
        if not remote_user:
            return users
        return users.search([("wire_remote_user", "=", remote_user)], limit=1)

    def _check_credentials(self, credential, env):
        """Accept the ``wire_remote_user`` credential for the user the Authelia headers map to.

        Args:
            credential (dict): Login credential with at least ``type``.
            env (dict): Authentication environment passed by ``authenticate``.

        Returns:
            dict: auth_info with ``uid``, ``auth_method`` and ``mfa``.

        Raises:
            AccessDenied: If neither a parent method nor this rule accepts the credential.
        """
        try:
            return super()._check_credentials(credential, env)
        except AccessDenied:
            if not (
                credential["type"] == CREDENTIAL_TYPE
                and request
                and self._wire_resolve_user(request.httprequest) == self.env.user
            ):
                raise
            return {"uid": self.env.user.id, "auth_method": CREDENTIAL_TYPE, "mfa": "skip"}
