# pylint: skip-file
from datetime import timedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class CourierPickupRequest(models.Model):
    """
    Model for managing courier pickup requests.

    This model stores information about customer requests for courier pickup,
    including pickup location, time, status, and related delivery orders.

    The pickup request follows a workflow from draft to warehouse delivery:
    - draft: Initial state when the request is created
    - confirmed: Request has been confirmed by the customer
    - assigned: A courier has been assigned to the pickup
    - picked: The package has been picked up by the courier
    - warehouse: The package has been delivered to the warehouse
    - cancelled: The pickup request has been cancelled

    The model supports recurring pickup scheduling and integrates with the
    delivery order system to create subsequent delivery orders after pickup.
    """
    _name = 'courier.pickup.request'
    _description = 'Courier Pickup Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'request_date desc, id desc'

    name = fields.Char(
        string='Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
        help="Unique identifier for the pickup request"
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        tracking=True,
        help="Customer who requested the pickup"
    )
    request_date = fields.Datetime(
        default=fields.Datetime.now,
        required=True,
        tracking=True,
        help="Date and time when the pickup was requested"
    )
    pickup_date = fields.Datetime(
        required=True,
        tracking=True,
        help="Scheduled date and time for pickup"
    )
    pickup_address_id = fields.Many2one(
        'res.partner',
        string='Pickup Address',
        required=True,
        tracking=True,
        help="Address where the courier should pick up the package"
    )
    notes = fields.Text(
        help="Additional notes for the courier"
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('assigned', 'Assigned to Courier'),
        ('picked', 'Picked Up'),
        ('warehouse', 'Delivered to Warehouse'),
        ('cancelled', 'Cancelled')
    ], default='draft', tracking=True, copy=False)

    courier_id = fields.Many2one(
        'res.users',
        string='Assigned Courier',
        tracking=True,
        domain=[('is_courier', '=', True)],
        help="Courier assigned to this pickup request"
    )
    delivery_order_ids = fields.One2many(
        'courier.delivery.order',
        'pickup_request_id',
        string='Delivery Orders',
        help="Delivery orders created from this pickup request"
    )
    delivery_count = fields.Integer(
        compute='_compute_delivery_count',
        help="Number of delivery orders related to this pickup request"
    )
    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'Low'),
        ('2', 'High'),
        ('3', 'Urgent')
    ], default='0', help="Priority level of the pickup request")

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        help="Company related to this pickup request"
    )
    zone_id = fields.Many2one(
        'courier.delivery.zone',
        string='Delivery Zone',
        help="Delivery zone for this pickup request"
    )
    weight = fields.Float(
        help="Total weight of the packages to be picked up"
    )
    package_count = fields.Integer(
        default=1,
        help="Number of packages to be picked up"
    )

    @api.model_create_multi
    def create(self, vals_list):
        """
        Override create method to assign a unique sequence number to each
        pickup request.

        Args:
            vals_list: List of dictionaries containing values for new records

        Returns:
            Newly created records
        """
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = (self.env['ir.sequence'].
                                next_by_code('courier.pickup.request') or
                                _('New'))
        return super(CourierPickupRequest, self).create(vals_list)

    def action_create_delivery(self):
        """
        Create a delivery order based on this pickup request.

        Returns:
            Action to open the created delivery order form
        """
        self.ensure_one()

        # Check if pickup request is in the warehouse state
        if self.state != 'warehouse':
            raise ValidationError(_('Delivery orders can only be created '
                                    'from pickup requests that have been '
                                    'delivered to warehouse.'))

        # Create delivery order
        delivery_order = self.env['courier.delivery.order'].create({
            'pickup_request_id': self.id,
            'partner_id': self.partner_id.id,
            'recipient_id': self.partner_id.id,
            # Default recipient to customer, can be changed later
            'delivery_address_id': self.partner_id.id,
            # Default delivery address to customer, can be changed later
            'scheduled_date': fields.Datetime.now() + timedelta(days=1),
            # Schedule for next day
            'courier_id': self.courier_id.id if self.courier_id else False,
            'notes': _('Created from pickup request %s') % self.name,
            'weight': self.weight,  # Use weight from pickup request
        })

        # Open the created delivery order form
        return {
            'name': _('Delivery Order'),
            'type': 'ir.actions.act_window',
            'res_model': 'courier.delivery.order',
            'res_id': delivery_order.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_confirm(self):
        """
        Confirm the pickup request and change its state to 'confirmed'.
        """
        self.write({'state': 'confirmed'})

    def action_assign_courier(self):
        """
        Assign a courier to the pickup request and change its state
        to 'assigned'.
        """
        if not self.courier_id:
            raise ValidationError(_("Please assign a courier before "
                                    "proceeding."))
        self.write({'state': 'assigned'})

    def action_mark_picked(self):
        """
        Mark the pickup request as picked up and change its state to 'picked'.
        """
        self.write({'state': 'picked'})

    def action_mark_delivered_to_warehouse(self):
        """
        Mark the pickup request as delivered to warehouse and change its
        state to 'warehouse'.

        This status indicates that the package has been picked up from
        the customer
        and delivered to the company's warehouse for further processing.
        """
        # Check if the pickup request is in a valid state for this action
        if self.state != 'picked':
            raise ValidationError(_('Only picked up requests can be marked as'
                                    ' delivered to warehouse.'))

        self.write({'state': 'warehouse'})

    def action_cancel(self):
        """
        Cancel the pickup request and change its state to 'cancelled'.
        """
        self.write({'state': 'cancelled'})

    def action_reset_to_draft(self):
        """
        Reset the pickup request to draft state.
        """
        self.write({'state': 'draft'})

    def action_view_deliveries(self):
        """
        Open the delivery orders related to this pickup request.

        Returns:
            Action to display the related delivery orders
        """
        self.ensure_one()
        return {
            'name': _('Delivery Orders'),
            'view_mode': 'tree,form',
            'res_model': 'courier.delivery.order',
            'domain': [('pickup_request_id', '=', self.id)],
            'type': 'ir.actions.act_window',
            'context': {'default_pickup_request_id': self.id}
        }

    @api.depends('delivery_order_ids')
    def _compute_delivery_count(self):
        """
        Compute the number of delivery orders related to this pickup request.
        """
        for request in self:
            request.delivery_count = len(request.delivery_order_ids)

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """
        Update pickup address when customer is changed.
        """
        if self.partner_id:
            self.pickup_address_id = self.partner_id

    @api.constrains('pickup_date')
    def _check_pickup_date(self):
        """
        Validate that pickup date is not in the past.
        """
        for request in self:
            if (request.pickup_date and request.pickup_date <
                    fields.Datetime.now()):
                raise ValidationError(_("Pickup date cannot be in the past."))
