from odoo import models, fields, api, _


class CourierDeliveryZone(models.Model):
    """
    Model for managing delivery zones.
    
    This model defines geographical zones for deliveries with specific
    pricing factors and delivery time estimates.
    
    Delivery zones are used to organize the geographical areas for courier operations,
    with each zone having specific pricing rules and delivery time estimates.
    Zones can be assigned to specific couriers and can be used for automatic
    assignment of deliveries based on address information.
    
    Features include:
    - Map view for visual zone management
    - Automatic zone assignment based on address
    - ZIP code and city-based zone matching
    - Enhanced geocoding for accurate address validation
    - Zone-based pricing calculation
    - Courier assignment to zones for efficient scheduling
    """
    _name = 'courier.delivery.zone'
    _description = 'Delivery Zone'
    _order = 'name'

    name = fields.Char(
        string='Zone Name',
        required=True,
        help="Name of the delivery zone"
    )
    code = fields.Char(
        string='Zone Code',
        required=True,
        help="Unique code for the delivery zone"
    )
    description = fields.Text(
        string='Description',
        help="Description of the delivery zone"
    )
    factor = fields.Float(
        string='Price Factor',
        default=1.0,
        required=True,
        help="Price multiplier for deliveries in this zone"
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        help="Whether this zone is active"
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        help="Company related to this zone"
    )
    courier_ids = fields.Many2many(
        'res.users',
        string='Assigned Couriers',
        domain=[('is_courier', '=', True)],
        help="Couriers assigned to this delivery zone"
    )
    delivery_time_estimate = fields.Float(
        string='Estimated Delivery Time (hours)',
        default=24.0,
        help="Average estimated time for deliveries in this zone"
    )
    color = fields.Integer(
        string='Color',
        help="Color used in kanban view"
    )
    city_names = fields.Char(
        string='Cities',
        help="Cities included in this delivery zone (comma-separated)"
    )
    zip_codes = fields.Char(
        string='ZIP Codes',
        help="ZIP codes included in this zone (comma-separated)"
    )
    delivery_count = fields.Integer(
        string='Delivery Count',
        compute='_compute_delivery_count',
        help="Number of deliveries in this zone"
    )
    courier_count = fields.Integer(
        string='Courier Count',
        compute='_compute_courier_count',
        help="Number of couriers assigned to this zone"
    )

    _sql_constraints = [
        ('code_uniq', 'unique(code, company_id)', 'Zone code must be unique per company!')
    ]

    @api.depends('courier_ids')
    def _compute_courier_count(self):
        """
        Compute the number of couriers assigned to this zone.
        """
        for zone in self:
            zone.courier_count = len(zone.courier_ids)

    def _compute_delivery_count(self):
        """
        Compute the number of deliveries in this zone.
        """
        for zone in self:
            zone.delivery_count = self.env['courier.delivery.order'].search_count([
                ('zone_id', '=', zone.id)
            ])

    def action_view_deliveries(self):
        """
        Open the delivery orders related to this zone.
        
        Returns:
            Action to display the related delivery orders
        """
        self.ensure_one()
        return {
            'name': _('Delivery Orders'),
            'view_mode': 'tree,form',
            'res_model': 'courier.delivery.order',
            'domain': [('zone_id', '=', self.id)],
            'type': 'ir.actions.act_window',
            'context': {'default_zone_id': self.id}
        }

    def action_view_couriers(self):
        """
        Open the couriers assigned to this zone.
        
        Returns:
            Action to display the related couriers
        """
        self.ensure_one()
        return {
            'name': _('Couriers'),
            'view_mode': 'tree,form',
            'res_model': 'res.users',
            'domain': [('id', 'in', self.courier_ids.ids)],
            'type': 'ir.actions.act_window',
        }

    @api.model
    def get_zone_for_address(self, partner_id):
        """
        Find the appropriate delivery zone for a given address.
        
        Args:
            partner_id: ID of the partner (address)
            
        Returns:
            Delivery zone record or False if not found
        """
        if not partner_id:
            return False
            
        partner = self.env['res.partner'].browse(partner_id)
        
        # First try to match by city
        if partner.city:
            zones = self.search([
                ('city_names', 'ilike', partner.city),
                ('company_id', '=', self.env.company.id),
                ('active', '=', True)
            ])
            if zones:
                return zones[0]
        
        # Then try to match by ZIP code
        if partner.zip:
            zones = self.search([
                ('active', '=', True),
                ('company_id', '=', self.env.company.id)
            ])
            for zone in zones:
                if zone.zip_codes:
                    zip_list = [z.strip() for z in zone.zip_codes.split(',')]
                    if partner.zip in zip_list:
                        return zone
        
        # Default zone (first active one)
        return self.search([
            ('active', '=', True),
            ('company_id', '=', self.env.company.id)
        ], limit=1)
