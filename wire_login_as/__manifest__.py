{
    "name": "Wire Login As",
    "summary": 'Lets members of "Benutzer wechseln" switch to another internal user without password',
    "version": "19.0.1.0.0",
    "category": "Hidden",
    "license": "LGPL-3",
    "depends": ["web"],
    "data": [
        "security/wire_login_as_security.xml",
        "views/res_users_views.xml",
    ],
    "assets": {
        "web.assets_backend": ["wire_login_as/static/src/switch_user_menu.js"],
    },
    "installable": True,
}
