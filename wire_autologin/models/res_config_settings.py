from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    wire_autologin_mode = fields.Selection(
        [("table", "Tabelle"), ("email", "E-Mail")],
        string="Zuordnung",
        default="table",
        config_parameter="wire_autologin.mode",
    )
