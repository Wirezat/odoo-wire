{
    "name": "Wire Autologin",
    "summary": "Logs Authelia users of group eco in as their mapped Odoo user",
    "version": "19.0.1.0.0",
    "category": "Hidden",
    "license": "LGPL-3",
    "depends": ["web", "base_setup"],
    "data": [
        "security/ir.model.access.csv",
        "views/wire_autologin_mapping_views.xml",
        "views/res_config_settings_views.xml",
    ],
    "installable": True,
}
