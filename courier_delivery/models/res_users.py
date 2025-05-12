from odoo import models, fields, api


class ResUsers(models.Model):
    """
    Extend the res.users model to add courier-specific fields.

    This extension adds fields to track courier capabilities, schedules,
    and delivery statistics.
    """
    _inherit = 'res.users'

    is_courier = fields.Boolean(
        help="Check if this user is a courier"
    )
    courier_zone_ids = fields.Many2many(
        'courier.delivery.zone',
        string='Delivery Zones',
        help="Delivery zones this courier is assigned to"
    )
    vehicle_type = fields.Selection([
        ('bicycle', 'Bicycle'),
        ('motorcycle', 'Motorcycle'),
        ('car', 'Car'),
        ('van', 'Van'),
        ('truck', 'Truck')
    ], help="Type of vehicle used by the courier")

    license_number = fields.Char(
        help="Driver's license number"
    )
    max_weight = fields.Float(
        string='Max Weight Capacity (kg)',
        help="Maximum weight the courier can carry"
    )
    courier_schedule_ids = fields.One2many(
        'courier.schedule',
        'courier_id',
        string='Work Schedules',
        help="Work schedules for this courier"
    )
    pickup_request_ids = fields.One2many(
        'courier.pickup.request',
        'courier_id',
        string='Pickup Requests',
        help="Pickup requests assigned to this courier"
    )
    delivery_order_ids = fields.One2many(
        'courier.delivery.order',
        'courier_id',
        string='Delivery Orders',
        help="Delivery orders assigned to this courier"
    )

    schedule_count = fields.Integer(
        compute='_compute_schedule_count',
        help="Number of work schedules for this courier"
    )
    pickup_count = fields.Integer(
        compute='_compute_pickup_count',
        help="Number of pickup requests assigned to this courier"
    )
    delivery_count = fields.Integer(
        compute='_compute_delivery_count',
        help="Number of delivery orders assigned to this courier"
    )

    successful_deliveries = fields.Integer(
        compute='_compute_delivery_stats',
        help="Number of successful deliveries by this courier"
    )
    failed_deliveries = fields.Integer(
        compute='_compute_delivery_stats',
        help="Number of failed deliveries by this courier"
    )
    success_rate = fields.Float(
        compute='_compute_delivery_stats',
        help="Percentage of successful deliveries by this courier"
    )

    @api.depends('courier_schedule_ids')
    def _compute_schedule_count(self):
        """
        Compute the number of work schedules for this courier.
        """
        for user in self:
            user.schedule_count = len(user.courier_schedule_ids)

    @api.depends('pickup_request_ids')
    def _compute_pickup_count(self):
        """
        Compute the number of pickup requests assigned to this courier.
        """
        for user in self:
            user.pickup_count = len(user.pickup_request_ids)

    @api.depends('delivery_order_ids')
    def _compute_delivery_count(self):
        """
        Compute the number of delivery orders assigned to this courier.
        """
        for user in self:
            user.delivery_count = len(user.delivery_order_ids)

    @api.depends('delivery_order_ids.state')
    def _compute_delivery_stats(self):
        """
        Compute delivery statistics for this courier.
        """
        for user in self:
            deliveries = user.delivery_order_ids
            user.successful_deliveries = len(deliveries.filtered(
                lambda d: d.state == 'delivered'))
            user.failed_deliveries = len(deliveries.filtered(
                lambda d: d.state == 'failed'))

            total = len(deliveries.filtered(lambda d: d.state in ('delivered',
                                                                  'failed')))
            user.success_rate = \
                (user.successful_deliveries * 100.0 / total) if total else 0.0

    def action_view_schedules(self):
        """
        Open the work schedules for this courier.

        Returns:
            Action to display the related work schedules
        """
        self.ensure_one()
        return {
            'name': 'Work Schedules',
            'view_mode': 'tree,form,calendar',
            'res_model': 'courier.schedule',
            'domain': [('courier_id', '=', self.id)],
            'type': 'ir.actions.act_window',
            'context': {'default_courier_id': self.id}
        }

    def action_view_pickups(self):
        """
        Open the pickup requests assigned to this courier.

        Returns:
            Action to display the related pickup requests
        """
        self.ensure_one()
        return {
            'name': 'Pickup Requests',
            'view_mode': 'tree,form',
            'res_model': 'courier.pickup.request',
            'domain': [('courier_id', '=', self.id)],
            'type': 'ir.actions.act_window',
            'context': {'default_courier_id': self.id}
        }

    def action_view_deliveries(self):
        """
        Open the delivery orders assigned to this courier.

        Returns:
            Action to display the related delivery orders
        """
        self.ensure_one()
        return {
            'name': 'Delivery Orders',
            'view_mode': 'tree,form',
            'res_model': 'courier.delivery.order',
            'domain': [('courier_id', '=', self.id)],
            'type': 'ir.actions.act_window',
            'context': {'default_courier_id': self.id}
        }
