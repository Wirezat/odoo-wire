from odoo import fields, models


class WireAutologinMapping(models.Model):
    _name = "wire.autologin.mapping"
    _description = "Authelia-Zuordnung"
    _order = "remote_user"
    _rec_name = "remote_user"

    remote_user = fields.Char(string="Authelia-Benutzer", required=True)
    user_id = fields.Many2one("res.users", string="Odoo-Benutzer", required=True, ondelete="cascade")

    _remote_user_unique = models.Constraint(
        "UNIQUE (remote_user)", "Jeder Authelia-Benutzer darf nur einmal vorkommen."
    )
