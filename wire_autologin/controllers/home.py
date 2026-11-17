from urllib.parse import urljoin

from werkzeug.urls import url_encode

from odoo import http
from odoo.addons.web.controllers.home import Home
from odoo.addons.web.controllers.session import Session
from odoo.addons.web.controllers.utils import ensure_db
from odoo.exceptions import AccessDenied
from odoo.http import request

from ..models.res_users import CREDENTIAL_TYPE, DEFAULT_LOGOUT_URL, LOGOUT_URL_PARAM


class WireAutologinHome(Home):
    @http.route()
    def web_login(self, redirect=None, **kw):
        """Sign in the mapped Odoo user without the login form when Authelia sends group ``eco``.

        Args:
            redirect (str): URL to go to after login.
            **kw: Remaining request parameters; ``no_autologin`` forces the regular form.

        Returns:
            werkzeug.wrappers.Response: Redirect after automatic login, otherwise the regular login response.
        """
        if request.httprequest.method == "GET" and request.session.uid is None and "no_autologin" not in kw:
            ensure_db()
            user = request.env["res.users"]._wire_resolve_user(request.httprequest)
            if not user:
                return super().web_login(redirect=redirect, **kw)
            try:
                auth_info = request.session.authenticate(request.env, {"login": user.login, "type": CREDENTIAL_TYPE})
            except AccessDenied:
                return super().web_login(redirect=redirect, **kw)
            return request.redirect(self._login_redirect(auth_info["uid"], redirect=redirect))
        return super().web_login(redirect=redirect, **kw)


class WireAutologinSession(Session):
    @http.route()
    def logout(self, redirect="/odoo"):
        """End the Odoo session and, behind Authelia, the Authelia session too.

        Args:
            redirect (str): URL to go to after the next login.

        Returns:
            werkzeug.wrappers.Response: Redirect to the Authelia logout URL with ``redirect`` as absolute ``rd``
            when the request carries ``Remote-User``, otherwise the regular logout response.
        """
        response = super().logout(redirect=redirect)
        if not request.httprequest.headers.get("Remote-User"):
            return response
        logout_url = request.env["ir.config_parameter"].sudo().get_param(LOGOUT_URL_PARAM, DEFAULT_LOGOUT_URL)
        target = urljoin(request.httprequest.host_url, redirect)
        return request.redirect(f"{logout_url}?{url_encode({'rd': target})}", code=303, local=False)
