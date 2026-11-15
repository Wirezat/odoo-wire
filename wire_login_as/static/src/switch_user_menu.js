import { registry } from "@web/core/registry";
import { user } from "@web/core/user";

/**
 * User menu entry that opens the list of users to switch into.
 *
 * @param {Object} env web client environment
 * @returns {Object} user menu item description
 */
function switchUserItem(env) {
    return {
        type: "item",
        id: "wire_switch_user",
        description: "Benutzer wechseln",
        callback: () => env.services.action.doAction("wire_login_as.action_switch_user_list"),
        sequence: 55,
    };
}

registry.category("services").add("wire_switch_user_menu", {
    /**
     * Add the user menu entry for members of "Benutzer wechseln".
     *
     * @returns {Promise<void>} resolves once the group check is done
     */
    async start() {
        if (await user.hasGroup("wire_login_as.group_switch_user")) {
            registry.category("user_menuitems").add("wire_switch_user", switchUserItem);
        }
    },
});
