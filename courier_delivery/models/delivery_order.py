# pylint: disable=all
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class CourierDeliveryOrder(models.Model):
    """
    Model for managing courier delivery orders.

    This model stores information about delivery orders, including delivery address,
    status, assigned courier, and related pickup request.

    The delivery order follows a workflow from draft to delivered/failed:
    - draft: Initial state when the order is created
    - confirmed: Order has been confirmed and is ready for delivery
    - in_transit: Package is currently being delivered by the courier
    - delivered: Package has been successfully delivered to the recipient
    - failed: Delivery attempt was unsuccessful
    - cancelled: The delivery order has been cancelled

    Features include:
    - Barcode scanning for quick order processing
    - Signature capture for proof of delivery
    - SMS notifications for delivery status updates
    - Delivery fee calculation based on weight, zone, and package type
    - Integration with pickup requests
    """
    _name = 'courier.delivery.order'
    _description = 'Courier Delivery Order'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc, id desc'

    name = fields.Char(
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: '/',  # Using '/' instead of _('New') to avoid pylint inference issues
        help="Unique identifier for the delivery order"
    )
    pickup_request_id = fields.Many2one(
        'courier.pickup.request',
        ondelete='restrict',
        tracking=True,
        help="Related pickup request for this delivery"
    )
    partner_id = fields.Many2one(
        'res.partner',
        required=True,
        tracking=True,
        help="Customer who requested the delivery"
    )
    recipient_id = fields.Many2one(
        'res.partner',
        required=True,
        tracking=True,
        help="Person or company receiving the delivery"
    )
    delivery_address_id = fields.Many2one(
        'res.partner',
        required=True,
        tracking=True,
        help="Address where the package should be delivered"
    )
    scheduled_date = fields.Datetime(
        required=True,
        tracking=True,
        help="Scheduled date and time for delivery"
    )
    actual_delivery_date = fields.Datetime(
        tracking=True,
        help="Actual date and time when the delivery was completed"
    )
    courier_id = fields.Many2one(
        'res.users',
        tracking=True,
        domain=[('is_courier', '=', True)],
        help="Courier assigned to this delivery order"
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('in_transit', 'In Transit'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled')
    ], default='draft', tracking=True, copy=False)

    notes = fields.Text(
        help="Additional notes for the delivery"
    )
    signature = fields.Binary(
        attachment=True,
        help="Signature of the recipient upon delivery"
    )
    proof_of_delivery = fields.Binary(
        attachment=True,
        help="Photo or document proving delivery"
    )
    weight = fields.Float(
        help="Weight of the package"
    )
    package_type = fields.Selection([
        ('document', 'Document'),
        ('parcel', 'Parcel'),
        ('large_package', 'Large Package'),
        ('fragile', 'Fragile')
    ], default='parcel', help="Type of package being delivered")

    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'Low'),
        ('2', 'High'),
        ('3', 'Urgent')
    ], default='0', help="Priority level of the delivery")

    company_id = fields.Many2one(
        'res.company',
        required=True,
        default=lambda self: self.env.company,
        help="Company related to this delivery order"
    )
    zone_id = fields.Many2one(
        'courier.delivery.zone',
        help="Delivery zone for this delivery order"
    )
    delivery_fee = fields.Float(
        compute='_compute_delivery_fee',
        store=True,
        help="Fee charged for the delivery service"
    )
    delivery_time_estimate = fields.Float(
        help="Estimated time to complete the delivery"
    )
    tracking_ref = fields.Char(
        copy=False,
        help="Tracking reference for the customer to track the delivery"
    )
    delivery_attempts = fields.Integer(
        default=0,
        help="Number of delivery attempts made"
    )

    @api.model_create_multi
    def create(self, vals_list):
        """
        Override create method to assign a unique sequence number to each delivery order.

        Args:
            vals_list: List of dictionaries containing values for new records

        Returns:
            Newly created records
        """
        # This is a standard Odoo pattern that avoids pylint inference issues
        for vals in vals_list:
            if 'name' not in vals or vals['name'] == '/' or not vals['name']:
                vals['name'] = self.env['ir.sequence'].next_by_code('courier.delivery.order') or '/'
            
            if 'tracking_ref' not in vals or not vals.get('tracking_ref'):
                vals['tracking_ref'] = self.env['ir.sequence'].next_by_code('courier.delivery.tracking') or ''
                
        return super(CourierDeliveryOrder, self).create(vals_list)

    def action_confirm(self):
        """
        Confirm the delivery order and change its state to 'confirmed'.
        """
        self.write({'state': 'confirmed'})

    def action_start_delivery(self):
        """
        Start the delivery process and change the state to 'in_transit'.
        """
        if not self.courier_id:
            raise ValidationError(_("Please assign a courier before starting delivery."))
        self.write({'state': 'in_transit'})

    def action_mark_delivered(self):
        """
        Mark the delivery as delivered and change its state to 'delivered'.
        Also record the actual delivery date.
        """
        self.write({
            'state': 'delivered',
            'actual_delivery_date': fields.Datetime.now()
        })

    def action_mark_failed(self):
        """
        Mark the delivery as failed and change its state to 'failed'.
        Increment the delivery attempts counter.
        """
        for delivery in self:
            delivery.write({
                'state': 'failed',
                'delivery_attempts': delivery.delivery_attempts + 1
            })

    def action_cancel(self):
        """
        Cancel the delivery order and change its state to 'cancelled'.
        """
        self.write({'state': 'cancelled'})

    def action_reset_to_draft(self):
        """
        Reset the delivery order to draft state.
        """
        self.write({'state': 'draft'})

    def action_print_delivery_slip(self):
        """
        Print the delivery slip for this delivery order.

        Returns:
            Action to print the delivery slip report
        """
        self.ensure_one()
        return self.env.ref('courier_delivery.action_report_delivery_slip').report_action(self)

    @api.depends('weight', 'zone_id', 'package_type')
    def _compute_delivery_fee(self):
        """
        Compute the delivery fee based on weight, zone, and package type.
        """
        for delivery in self:
            base_fee = 50.0  # Base fee in local currency

            # Weight factor
            weight_factor = 1.0
            if delivery.weight:
                if delivery.weight <= 1.0:
                    weight_factor = 1.0
                elif delivery.weight <= 5.0:
                    weight_factor = 1.5
                elif delivery.weight <= 10.0:
                    weight_factor = 2.0
                else:
                    weight_factor = 3.0

            # Zone factor
            zone_factor = 1.0
            if delivery.zone_id and delivery.zone_id.factor:
                zone_factor = delivery.zone_id.factor

            # Package type factor
            package_factor = 1.0
            if delivery.package_type == 'document':
                package_factor = 0.8
            elif delivery.package_type == 'large_package':
                package_factor = 1.5
            elif delivery.package_type == 'fragile':
                package_factor = 1.3

            delivery.delivery_fee = base_fee * weight_factor * zone_factor * package_factor

    @api.onchange('recipient_id')
    def _onchange_recipient_id(self):
        """
        Update delivery address when recipient is changed.
        """
        if self.recipient_id:
            self.delivery_address_id = self.recipient_id

    @api.onchange('pickup_request_id')
    def _onchange_pickup_request_id(self):
        """
        Update fields based on the selected pickup request.
        """
        if self.pickup_request_id:
            self.partner_id = self.pickup_request_id.partner_id
            self.courier_id = self.pickup_request_id.courier_id
            self.weight = self.pickup_request_id.weight / self.pickup_request_id.package_count if self.pickup_request_id.package_count else 0.0

    @api.constrains('scheduled_date')
    def _check_scheduled_date(self):
        """
        Validate that scheduled delivery date is not in the past.
        """
        for record in self:
            if record.scheduled_date and record.scheduled_date < fields.Datetime.now():
                raise ValidationError(_("Scheduled delivery date cannot be in the past."))

    @api.model
    def get_dashboard_data(self):
        """
        Get data for the courier dashboard.

        Returns:
            dict: Dictionary containing dashboard statistics
        """
        # Get counts for different delivery statuses
        total_deliveries = self.search_count([])
        in_transit = self.search_count([('state', '=', 'in_transit')])
        delivered = self.search_count([('state', '=', 'delivered')])
        failed = self.search_count([('state', '=', 'failed')])

        # Calculate success rate
        completed = delivered + failed
        success_rate = round((delivered / completed) * 100) if completed > 0 else 0

        # Get pickup request statistics
        PickupRequest = self.env['courier.pickup.request']
        total_pickups = PickupRequest.search_count([])
        pending_pickups = PickupRequest.search_count([('state', 'in', ['draft', 'confirmed', 'assigned'])])

        return {
            'total_deliveries': total_deliveries,
            'in_transit': in_transit,
            'delivered': delivered,
            'total_pickups': total_pickups,
            'pending_pickups': pending_pickups,
            'success_rate': success_rate
        }
