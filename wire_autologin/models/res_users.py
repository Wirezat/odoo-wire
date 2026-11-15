from odoo import models
from odoo.exceptions import AccessDenied
from odoo.http import request

ECO_GROUP = "eco"
CREDENTIAL_TYPE = "wire_remote_user"


def has_eco_group(httprequest):
    """Tell whether the forward-auth header lists the Authelia group ``eco``.

    :param werkzeug.wrappers.Request httprequest: incoming HTTP request
    :return: True if ``Remote-Groups`` contains ``eco`` as one of its comma-separated entries
    :rtype: bool
    """
    groups = httprequest.headers.get("Remote-Groups", "")
    return ECO_GROUP in (group.strip() for group in groups.split(","))


class ResUsers(models.Model):
    _inherit = "res.users"

    def _check_credentials(self, credential, env):
        """Accept the ``wire_remote_user`` credential for admin when Authelia sends group ``eco``.

        :param dict credential: login credential with at least ``type``
        :param dict env: authentication environment passed by ``authenticate``
        :return: auth_info with ``uid``, ``auth_method`` and ``mfa``
        :rtype: dict
        :raise AccessDenied: if neither a parent method nor this rule accepts the credential
        """
        try:
            return super()._check_credentials(credential, env)
        except AccessDenied:
            if not (
                credential["type"] == CREDENTIAL_TYPE
                and request
                and has_eco_group(request.httprequest)
                and self.env.user == self.env.ref("base.user_admin")
            ):
                raise
            return {"uid": self.env.user.id, "auth_method": CREDENTIAL_TYPE, "mfa": "skip"}
