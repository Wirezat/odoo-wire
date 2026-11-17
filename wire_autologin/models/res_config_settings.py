from odoo import fields, models

from .res_users import DEFAULT_LOGOUT_URL, LOGOUT_URL_PARAM


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    wire_autologin_mode = fields.Selection(
        [("table", "Tabelle"), ("email", "E-Mail")],
        string="Zuordnung",
        default="table",
        config_parameter="wire_autologin.mode",
    )
    wire_autologin_logout_url = fields.Char(
        string="Abmelde-URL",
        default=DEFAULT_LOGOUT_URL,
        config_parameter=LOGOUT_URL_PARAM,
    )
