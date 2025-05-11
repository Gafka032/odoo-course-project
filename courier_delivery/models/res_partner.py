from odoo import models, fields, api


class ResPartner(models.Model):
    """
    Extend the res.partner model to add courier delivery fields.
    
    This extension adds delivery-related fields to partners for better
    integration with the courier delivery module.
    """
    _inherit = 'res.partner'

    is_delivery_address = fields.Boolean(
        string='Is Delivery Address',
        help="Check if this address is used for deliveries"
    )
    delivery_notes = fields.Text(
        string='Delivery Notes',
        help="Special instructions for couriers delivering to this address"
    )
    preferred_delivery_time = fields.Selection([
        ('morning', 'Morning (8:00-12:00)'),
        ('afternoon', 'Afternoon (12:00-17:00)'),
        ('evening', 'Evening (17:00-21:00)'),
        ('any', 'Any Time')
    ], string='Preferred Delivery Time', default='any',
        help="Preferred time of day for deliveries")
    
    delivery_zone_id = fields.Many2one(
        'courier.delivery.zone',
        string='Delivery Zone',
        compute='_compute_delivery_zone',
        store=True,
        help="Delivery zone for this address"
    )
    
    pickup_request_ids = fields.One2many(
        'courier.pickup.request',
        'partner_id',
        string='Pickup Requests',
        help="Pickup requests made by this partner"
    )
    delivery_order_ids = fields.One2many(
        'courier.delivery.order',
        'partner_id',
        string='Delivery Orders',
        help="Delivery orders for this partner"
    )
    recipient_delivery_ids = fields.One2many(
        'courier.delivery.order',
        'recipient_id',
        string='Received Deliveries',
        help="Deliveries where this partner is the recipient"
    )
    
    pickup_count = fields.Integer(
        string='Pickup Count',
        compute='_compute_pickup_count',
        help="Number of pickup requests made by this partner"
    )
    delivery_count = fields.Integer(
        string='Delivery Count',
        compute='_compute_delivery_count',
        help="Number of delivery orders for this partner"
    )
    received_delivery_count = fields.Integer(
        string='Received Delivery Count',
        compute='_compute_received_delivery_count',
        help="Number of deliveries where this partner is the recipient"
    )

    @api.depends('city', 'zip', 'country_id', 'state_id')
    def _compute_delivery_zone(self):
        """
        Compute the delivery zone based on the partner's address.
        """
        DeliveryZone = self.env['courier.delivery.zone']
        for partner in self:
            partner.delivery_zone_id = DeliveryZone.get_zone_for_address(partner.id)

    @api.depends('pickup_request_ids')
    def _compute_pickup_count(self):
        """
        Compute the number of pickup requests made by this partner.
        """
        for partner in self:
            partner.pickup_count = len(partner.pickup_request_ids)

    @api.depends('delivery_order_ids')
    def _compute_delivery_count(self):
        """
        Compute the number of delivery orders for this partner.
        """
        for partner in self:
            partner.delivery_count = len(partner.delivery_order_ids)

    @api.depends('recipient_delivery_ids')
    def _compute_received_delivery_count(self):
        """
        Compute the number of deliveries where this partner is the recipient.
        """
        for partner in self:
            partner.received_delivery_count = len(partner.recipient_delivery_ids)

    def action_view_pickups(self):
        """
        Open the pickup requests made by this partner.
        
        Returns:
            Action to display the related pickup requests
        """
        self.ensure_one()
        return {
            'name': 'Pickup Requests',
            'view_mode': 'tree,form',
            'res_model': 'courier.pickup.request',
            'domain': [('partner_id', '=', self.id)],
            'type': 'ir.actions.act_window',
            'context': {'default_partner_id': self.id}
        }

    def action_view_deliveries(self):
        """
        Open the delivery orders for this partner.
        
        Returns:
            Action to display the related delivery orders
        """
        self.ensure_one()
        return {
            'name': 'Delivery Orders',
            'view_mode': 'tree,form',
            'res_model': 'courier.delivery.order',
            'domain': [('partner_id', '=', self.id)],
            'type': 'ir.actions.act_window',
            'context': {'default_partner_id': self.id}
        }

    def action_view_received_deliveries(self):
        """
        Open the deliveries where this partner is the recipient.
        
        Returns:
            Action to display the related received deliveries
        """
        self.ensure_one()
        return {
            'name': 'Received Deliveries',
            'view_mode': 'tree,form',
            'res_model': 'courier.delivery.order',
            'domain': [('recipient_id', '=', self.id)],
            'type': 'ir.actions.act_window',
            'context': {'default_recipient_id': self.id}
        }
