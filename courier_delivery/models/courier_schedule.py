from datetime import timedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class CourierSchedule(models.Model):
    """
    Model for managing courier work schedules.

    This model tracks courier availability, working hours, and assigned
    deliveries.
    It provides a comprehensive scheduling system for managing courier
    resources
    and optimizing delivery operations.

    The schedule follows a workflow from draft to completed:
    - draft: Initial state when the schedule is created
    - confirmed: Schedule has been confirmed and assigned
    - completed: Schedule has been completed
    - cancelled: Schedule has been cancelled

    Features include:
    - Enhanced calendar view for easy scheduling
    - Mobile-responsive interface for couriers
    - Assignment of delivery zones to couriers for specific time periods
    - Tracking of deliveries and pickups per schedule
    - Workload analysis and optimization
    - Integration with delivery orders and pickup requests
    """
    _name = 'courier.schedule'
    _description = 'Courier Work Schedule'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char(
        string='Reference',
        compute='_compute_name',
        store=True,
        help="Unique identifier for the schedule entry"
    )
    courier_id = fields.Many2one(
        'res.users',
        string='Courier',
        required=True,
        tracking=True,
        domain=[('is_courier', '=', True)],
        help="Courier assigned to this schedule"
    )
    date = fields.Date(
        required=True,
        tracking=True,
        help="Date of the schedule"
    )
    start_time = fields.Float(
        required=True,
        tracking=True,
        help="Start time of the shift (in hours, e.g., 8.5 for 8:30)"
    )
    end_time = fields.Float(
        required=True,
        tracking=True,
        help="End time of the shift (in hours, e.g., 17.5 for 17:30)"
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], default='draft', tracking=True)

    zone_ids = fields.Many2many(
        'courier.delivery.zone',
        help="Delivery zones assigned to this courier for this schedule"
    )
    notes = fields.Text(
        help="Additional notes for this schedule"
    )
    delivery_order_ids = fields.One2many(
        'courier.delivery.order',
        'courier_id',
        domain="[('scheduled_date', '>=', date_start), "
               "('scheduled_date', '<=', date_end)]",
        help="Delivery orders assigned to this courier during this schedule"
    )
    pickup_request_ids = fields.One2many(
        'courier.pickup.request',
        'courier_id',
        domain="[('pickup_date', '>=', date_start), "
               "('pickup_date', '<=', date_end)]",
        help="Pickup requests assigned to this courier during this schedule"
    )
    date_start = fields.Datetime(
        compute='_compute_date_range',
        store=True,
        help="Start datetime of the schedule"
    )
    date_end = fields.Datetime(
        compute='_compute_date_range',
        store=True,
        help="End datetime of the schedule"
    )
    working_hours = fields.Float(
        compute='_compute_working_hours',
        store=True,
        help="Total working hours for this schedule"
    )
    delivery_count = fields.Integer(
        compute='_compute_delivery_count',
        help="Number of deliveries assigned during this schedule"
    )
    pickup_count = fields.Integer(
        compute='_compute_pickup_count',
        help="Number of pickups assigned during this schedule"
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        help="Company related to this schedule"
    )
    color = fields.Integer(
        help="Color used in calendar view"
    )

    @api.depends('courier_id', 'date')
    def _compute_name(self):
        """
        Compute a unique name for the schedule based on courier and date.
        """
        for schedule in self:
            if schedule.courier_id and schedule.date:
                schedule.name = f"{schedule.courier_id.name} - {schedule.date}"
            else:
                schedule.name = _("New Schedule")

    @api.depends('date', 'start_time', 'end_time')
    def _compute_date_range(self):
        """
        Compute the start and end datetime of the schedule.
        """
        for schedule in self:
            if schedule.date:
                # Convert float hours to hours and minutes
                start_hour = int(schedule.start_time)
                start_minute = int((schedule.start_time % 1) * 60)

                end_hour = int(schedule.end_time)
                end_minute = int((schedule.end_time % 1) * 60)

                schedule.date_start = (fields.Datetime.to_datetime(
                    schedule.date) + timedelta(hours=start_hour,
                                               minutes=start_minute))
                schedule.date_end = (fields.Datetime.to_datetime(
                    schedule.date) + timedelta(hours=end_hour,
                                               minutes=end_minute))
            else:
                schedule.date_start = False
                schedule.date_end = False

    @api.depends('start_time', 'end_time')
    def _compute_working_hours(self):
        """
        Compute the total working hours for this schedule.
        """
        for schedule in self:
            if schedule.end_time >= schedule.start_time:
                schedule.working_hours = (schedule.end_time -
                                          schedule.start_time)
            else:
                # Handle overnight shifts
                schedule.working_hours = ((24 - schedule.start_time) +
                                          schedule.end_time)

    @api.depends('delivery_order_ids')
    def _compute_delivery_count(self):
        """
        Compute the number of deliveries assigned during this schedule.
        """
        for schedule in self:
            schedule.delivery_count = len(schedule.delivery_order_ids)

    @api.depends('pickup_request_ids')
    def _compute_pickup_count(self):
        """
        Compute the number of pickups assigned during this schedule.
        """
        for schedule in self:
            schedule.pickup_count = len(schedule.pickup_request_ids)

    def action_confirm(self):
        """
        Confirm the schedule and change its state to 'confirmed'.
        """
        self.write({'state': 'confirmed'})

    def action_start(self):
        """
        Start the schedule and change its state to 'in_progress'.
        """
        self.write({'state': 'in_progress'})

    def action_complete(self):
        """
        Complete the schedule and change its state to 'completed'.
        """
        self.write({'state': 'completed'})

    def action_cancel(self):
        """
        Cancel the schedule and change its state to 'cancelled'.
        """
        self.write({'state': 'cancelled'})

    def action_reset_to_draft(self):
        """
        Reset the schedule to draft state.
        """
        self.write({'state': 'draft'})

    def action_view_deliveries(self):
        """
        Open the delivery orders related to this schedule.

        Returns:
            Action to display the related delivery orders
        """
        self.ensure_one()
        return {
            'name': _('Delivery Orders'),
            'view_mode': 'tree,form',
            'res_model': 'courier.delivery.order',
            'domain': [
                ('courier_id', '=', self.courier_id.id),
                ('scheduled_date', '>=', self.date_start),
                ('scheduled_date', '<=', self.date_end)
            ],
            'type': 'ir.actions.act_window',
            'context': {'default_courier_id': self.courier_id.id}
        }

    def action_view_pickups(self):
        """
        Open the pickup requests related to this schedule.

        Returns:
            Action to display the related pickup requests
        """
        self.ensure_one()
        return {
            'name': _('Pickup Requests'),
            'view_mode': 'tree,form',
            'res_model': 'courier.pickup.request',
            'domain': [
                ('courier_id', '=', self.courier_id.id),
                ('pickup_date', '>=', self.date_start),
                ('pickup_date', '<=', self.date_end)
            ],
            'type': 'ir.actions.act_window',
            'context': {'default_courier_id': self.courier_id.id}
        }

    @api.constrains('start_time', 'end_time')
    def _check_times(self):
        """
        Validate that end time is after start time for same-day schedules.
        """
        for schedule in self:
            if schedule.end_time < schedule.start_time:
                # This is an overnight shift, which is allowed
                pass
            elif schedule.end_time == schedule.start_time:
                raise ValidationError(_("End time must be different from start"
                                        " time."))

    @api.constrains('courier_id', 'date', 'start_time', 'end_time')
    def _check_overlap(self):
        """
        Check for overlapping schedules for the same courier.
        """
        for schedule in self:
            # Find overlapping schedules
            domain = [
                ('id', '!=', schedule.id),
                ('courier_id', '=', schedule.courier_id.id),
                ('date', '=', schedule.date),
                ('state', 'not in', ['cancelled']),
            ]

            # Check for time overlap
            overlaps = self.env['courier.schedule'].search(domain)
            for overlap in overlaps:
                # Check if schedules overlap
                if (schedule.start_time < overlap.end_time
                        and schedule.end_time > overlap.start_time):
                    raise ValidationError(_(
                        "This schedule overlaps with another schedule for the "
                        "same courier on the same day."
                    ))
