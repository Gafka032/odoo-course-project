/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, useState } from "@odoo/owl";

class CourierDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.state = useState({
            stats: {
                total_pickups: 0,
                total_deliveries: 0,
                pending_pickups: 0,
                in_transit: 0,
                delivered: 0,
                success_rate: 0,
            },
            loading: true,
        });

        onWillStart(async () => {
            await this.loadDashboardData();
        });
    }

    async loadDashboardData() {
        try {
            this.state.loading = true;
            const data = await this.orm.call(
                "courier.delivery.order",
                "get_dashboard_data",
                []
            );
            this.state.stats = data;
        } catch (error) {
            console.error("Failed to load dashboard data:", error);
        } finally {
            this.state.loading = false;
        }
    }

    onPickupClick() {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Pickup Requests",
            res_model: "courier.pickup.request",
            views: [[false, "list"], [false, "form"]],
            domain: [["state", "in", ["draft", "confirmed", "assigned"]]],
        });
    }

    onDeliveryClick() {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Delivery Orders",
            res_model: "courier.delivery.order",
            views: [[false, "list"], [false, "form"]],
            domain: [["state", "in", ["draft", "confirmed", "in_transit"]]],
        });
    }

    onRefreshClick() {
        this.loadDashboardData();
    }
}

CourierDashboard.template = "courier_delivery.Dashboard";
CourierDashboard.props = {};

registry.category("actions").add("courier_delivery.dashboard", CourierDashboard);

export default CourierDashboard;
