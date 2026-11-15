from odoo import http
from odoo.addons.web.controllers.home import Home
from odoo.addons.web.controllers.utils import ensure_db
from odoo.exceptions import AccessDenied
from odoo.http import request

from ..models.res_users import CREDENTIAL_TYPE, has_eco_group


class WireAutologinHome(Home):
    @http.route()
    def web_login(self, redirect=None, **kw):
        """Sign in admin without the login form when Authelia sends group ``eco``.

        :param str redirect: URL to go to after login
        :param kw: remaining request parameters, ``no_autologin`` forces the regular form
        :return: redirect after automatic login, otherwise the regular login response
        :rtype: werkzeug.wrappers.Response
        """
        if (
            request.httprequest.method == "GET"
            and request.session.uid is None
            and "no_autologin" not in kw
            and has_eco_group(request.httprequest)
        ):
            ensure_db()
            login = request.env.ref("base.user_admin").sudo().login
            try:
                auth_info = request.session.authenticate(request.env, {"login": login, "type": CREDENTIAL_TYPE})
            except AccessDenied:
                return super().web_login(redirect=redirect, **kw)
            return request.redirect(self._login_redirect(auth_info["uid"], redirect=redirect))
        return super().web_login(redirect=redirect, **kw)
