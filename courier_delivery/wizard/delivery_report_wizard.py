from datetime import timedelta
from odoo import models, fields, api, _


class DeliveryReportWizard(models.TransientModel):
    """
    Wizard for generating delivery reports.

    This wizard allows users to select parameters for generating
    delivery reports, such as date range, courier, and delivery zone.
    """
    _name = 'courier.delivery.report.wizard'
    _description = 'Delivery Report Wizard'

    date_from = fields.Date(
        string='Start Date',
        default=lambda self: fields.Date.today() - timedelta(days=30),
        required=True,
        help="Start date for the report"
    )
    date_to = fields.Date(
        string='End Date',
        default=fields.Date.today,
        required=True,
        help="End date for the report"
    )
    courier_id = fields.Many2one(
        'res.users',
        string='Courier',
        domain=[('is_courier', '=', True)],
        help="Filter report by courier"
    )
    zone_id = fields.Many2one(
        'courier.delivery.zone',
        string='Delivery Zone',
        help="Filter report by delivery zone"
    )
    report_type = fields.Selection([
        ('summary', 'Summary Report'),
        ('detailed', 'Detailed Report'),
        ('courier', 'Courier Performance'),
        ('zone', 'Zone Analysis')
    ], default='summary', required=True,
        help="Type of report to generate")

    company_id = fields.Many2one(
        'res.company',
        required=True,
        default=lambda self: self.env.company,
        help="Company for which to generate the report"
    )
    include_cancelled = fields.Boolean(
        default=False,
        help="Include cancelled deliveries in the report"
    )

    @api.onchange('report_type')
    def _onchange_report_type(self):
        """
        Clear filters when report type changes.
        """
        if self.report_type == 'courier':
            self.zone_id = False
        elif self.report_type == 'zone':
            self.courier_id = False

    def action_generate_report(self):
        """
        Generate the delivery report based on the selected parameters.

        Returns:
            Action to display the generated report
        """
        self.ensure_one()

        # Ensure the report view is updated
        self.env['courier.delivery.report'].init()

        # Prepare domain based on filters
        domain = [
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
        ]

        if self.courier_id:
            domain.append(('courier_id', '=', self.courier_id.id))

        if self.zone_id:
            domain.append(('zone_id', '=', self.zone_id.id))

        if not self.include_cancelled:
            domain.append(('cancelled_deliveries', '=', 0))

        # Prepare context
        context = {
            'search_default_group_by_date': 1,
        }

        # Add appropriate grouping based on report type
        if self.report_type in ('courier', 'detailed'):
            context['search_default_group_by_courier'] = 1

        if self.report_type in ('zone', 'detailed'):
            context['search_default_group_by_zone'] = 1

        if self.report_type == 'summary':
            context['search_default_group_by_company'] = 1

        # Set default values if filters are applied
        if self.courier_id:
            context['default_courier_id'] = self.courier_id.id

        if self.zone_id:
            context['default_zone_id'] = self.zone_id.id

        # Return action to display report
        view_mode = 'pivot,graph,tree'
        if self.report_type == 'detailed':
            view_mode = 'tree,pivot,graph'

        return {
            'name': _('Delivery Report'),
            'type': 'ir.actions.act_window',
            'res_model': 'courier.delivery.report',
            'view_mode': view_mode,
            'domain': domain,
            'context': context,
            'target': 'current',
        }

    def action_print_report(self):
        """
        Print the delivery report as PDF.

        Returns:
            Action to print the report
        """
        self.ensure_one()

        data = {
            'date_from': self.date_from,
            'date_to': self.date_to,
            'courier_id': self.courier_id.id if self.courier_id else False,
            'zone_id': self.zone_id.id if self.zone_id else False,
            'report_type': self.report_type,
            'include_cancelled': self.include_cancelled,
            'company_id': self.company_id.id,
        }

        return (self.env.ref
                ('courier_delivery.action_report_delivery_statistics')
                .report_action(self, data=data))
