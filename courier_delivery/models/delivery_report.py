from odoo import models, fields, api, _, tools
from datetime import datetime, timedelta


class CourierDeliveryReport(models.Model):
    """
    Model for tracking courier delivery reports and statistics.
    
    This model stores aggregated data about deliveries, success rates,
    and performance metrics for couriers and delivery zones. It provides
    comprehensive analytics for monitoring delivery performance across
    different dimensions such as courier, zone, and time period.
    
    The report includes detailed status tracking for both deliveries and pickups,
    allowing for granular analysis of the delivery workflow efficiency.
    """
    _name = 'courier.delivery.report'
    _description = 'Courier Delivery Report'
    _order = 'date desc, id desc'
    _auto = False  # This is a database view

    name = fields.Char(
        string='Report Reference',
        readonly=True,
        help="Unique identifier for the report"
    )
    date = fields.Date(
        string='Date',
        readonly=True,
        help="Date of the report"
    )
    courier_id = fields.Many2one(
        'res.users',
        string='Courier',
        readonly=True,
        help="Courier associated with this report"
    )
    zone_id = fields.Many2one(
        'courier.delivery.zone',
        string='Delivery Zone',
        readonly=True,
        help="Delivery zone associated with this report"
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        readonly=True,
        help="Company associated with this report"
    )
    total_deliveries = fields.Integer(
        string='Total Deliveries',
        readonly=True,
        help="Total number of deliveries"
    )
    successful_deliveries = fields.Integer(
        string='Successful Deliveries',
        readonly=True,
        help="Number of successful deliveries"
    )
    failed_deliveries = fields.Integer(
        string='Failed Deliveries',
        readonly=True,
        help="Number of failed deliveries"
    )
    cancelled_deliveries = fields.Integer(
        string='Cancelled Deliveries',
        readonly=True,
        help="Number of cancelled deliveries"
    )
    in_transit_deliveries = fields.Integer(
        string='In Transit Deliveries',
        readonly=True,
        help="Number of deliveries currently in transit"
    )
    draft_deliveries = fields.Integer(
        string='Draft Deliveries',
        readonly=True,
        help="Number of draft deliveries"
    )
    confirmed_deliveries = fields.Integer(
        string='Confirmed Deliveries',
        readonly=True,
        help="Number of confirmed deliveries"
    )
    success_rate = fields.Float(
        string='Success Rate (%)',
        readonly=True,
        help="Percentage of successful deliveries"
    )
    avg_delivery_time = fields.Float(
        string='Avg Delivery Time (hours)',
        readonly=True,
        help="Average time to complete deliveries"
    )
    total_pickups = fields.Integer(
        string='Total Pickups',
        readonly=True,
        help="Total number of pickups"
    )
    draft_pickups = fields.Integer(
        string='Draft Pickups',
        readonly=True,
        help="Number of draft pickup requests"
    )
    confirmed_pickups = fields.Integer(
        string='Confirmed Pickups',
        readonly=True,
        help="Number of confirmed pickup requests"
    )
    assigned_pickups = fields.Integer(
        string='Assigned Pickups',
        readonly=True,
        help="Number of pickup requests assigned to couriers"
    )
    picked_pickups = fields.Integer(
        string='Picked Up',
        readonly=True,
        help="Number of pickup requests that have been picked up"
    )
    warehouse_pickups = fields.Integer(
        string='Delivered to Warehouse',
        readonly=True,
        help="Number of pickup requests delivered to warehouse"
    )
    cancelled_pickups = fields.Integer(
        string='Cancelled Pickups',
        readonly=True,
        help="Number of cancelled pickup requests"
    )
    total_weight = fields.Float(
        string='Total Weight (kg)',
        readonly=True,
        help="Total weight of all deliveries"
    )
    total_revenue = fields.Float(
        string='Total Revenue',
        readonly=True,
        help="Total revenue from deliveries"
    )

    def init(self):
        """
        Initialize the SQL view for the delivery report.
        
        This method creates or replaces the database view that powers the delivery report.
        The view combines data from delivery orders and pickup requests to provide
        comprehensive statistics on delivery operations.
        """
        # Using SQL directly instead of non-existent ir.model.tools model
        query = """
            CREATE OR REPLACE VIEW courier_delivery_report AS (
                WITH pickup_stats AS (
                    SELECT 
                        p.create_date::date as pickup_date,
                        count(*) as pickup_count,
                        sum(CASE WHEN p.state = 'draft' THEN 1 ELSE 0 END) as draft_pickups,
                        sum(CASE WHEN p.state = 'confirmed' THEN 1 ELSE 0 END) as confirmed_pickups,
                        sum(CASE WHEN p.state = 'assigned' THEN 1 ELSE 0 END) as assigned_pickups,
                        sum(CASE WHEN p.state = 'picked' THEN 1 ELSE 0 END) as picked_pickups,
                        sum(CASE WHEN p.state = 'warehouse' THEN 1 ELSE 0 END) as warehouse_pickups,
                        sum(CASE WHEN p.state = 'cancelled' THEN 1 ELSE 0 END) as cancelled_pickups,
                        p.courier_id as pickup_courier_id,
                        p.company_id as pickup_company_id
                    FROM 
                        courier_pickup_request p
                    GROUP BY 
                        p.create_date::date, p.courier_id, p.company_id
                )
                SELECT
                    row_number() OVER () as id,
                    d.create_date::date as date,
                    d.courier_id,
                    d.zone_id,
                    d.company_id,
                    count(d.id) as total_deliveries,
                    sum(CASE WHEN d.state = 'delivered' THEN 1 ELSE 0 END) as successful_deliveries,
                    sum(CASE WHEN d.state = 'failed' THEN 1 ELSE 0 END) as failed_deliveries,
                    sum(CASE WHEN d.state = 'cancelled' THEN 1 ELSE 0 END) as cancelled_deliveries,
                    sum(CASE WHEN d.state = 'in_transit' THEN 1 ELSE 0 END) as in_transit_deliveries,
                    sum(CASE WHEN d.state = 'draft' THEN 1 ELSE 0 END) as draft_deliveries,
                    sum(CASE WHEN d.state = 'confirmed' THEN 1 ELSE 0 END) as confirmed_deliveries,
                    CASE 
                        WHEN count(d.id) > 0 
                        THEN (sum(CASE WHEN d.state = 'delivered' THEN 1 ELSE 0 END) * 100.0 / count(d.id)) 
                        ELSE 0 
                    END as success_rate,
                    CASE 
                        WHEN sum(CASE WHEN d.state = 'delivered' AND d.actual_delivery_date IS NOT NULL THEN 1 ELSE 0 END) > 0 
                        THEN avg(
                            CASE 
                                WHEN d.state = 'delivered' AND d.actual_delivery_date IS NOT NULL 
                                THEN extract(epoch from (d.actual_delivery_date - d.create_date))/3600 
                                ELSE NULL 
                            END
                        ) 
                        ELSE 0 
                    END as avg_delivery_time,
                    COALESCE(ps.pickup_count, 0) as total_pickups,
                    COALESCE(ps.draft_pickups, 0) as draft_pickups,
                    COALESCE(ps.confirmed_pickups, 0) as confirmed_pickups,
                    COALESCE(ps.assigned_pickups, 0) as assigned_pickups,
                    COALESCE(ps.picked_pickups, 0) as picked_pickups,
                    COALESCE(ps.warehouse_pickups, 0) as warehouse_pickups,
                    COALESCE(ps.cancelled_pickups, 0) as cancelled_pickups,
                    sum(d.weight) as total_weight,
                    sum(d.delivery_fee) as total_revenue,
                    concat(
                        to_char(d.create_date::date, 'YYYY-MM-DD'), 
                        CASE WHEN d.courier_id IS NOT NULL THEN concat('-C', d.courier_id) ELSE '' END,
                        CASE WHEN d.zone_id IS NOT NULL THEN concat('-Z', d.zone_id) ELSE '' END
                    ) as name
                FROM
                    courier_delivery_order d
                LEFT JOIN
                    pickup_stats ps ON d.create_date::date = ps.pickup_date AND 
                                      (d.courier_id = ps.pickup_courier_id OR (d.courier_id IS NULL AND ps.pickup_courier_id IS NULL))
                WHERE
                    d.create_date IS NOT NULL
                GROUP BY
                    d.create_date::date,
                    d.courier_id,
                    d.zone_id,
                    d.company_id,
                    ps.pickup_count,
                    ps.draft_pickups,
                    ps.confirmed_pickups,
                    ps.assigned_pickups,
                    ps.picked_pickups,
                    ps.warehouse_pickups,
                    ps.cancelled_pickups
            )
        """
        tools.drop_view_if_exists(self.env.cr, 'courier_delivery_report')
        self.env.cr.execute(query)

    @api.model
    def get_report_values(self, date_from=False, date_to=False, courier_id=False, zone_id=False):
        """
        Get report values based on filters.
        
        Args:
            date_from: Start date for the report
            date_to: End date for the report
            courier_id: Filter by courier
            zone_id: Filter by delivery zone
            
        Returns:
            Dictionary with report values
        """
        domain = []
        
        if date_from:
            domain.append(('date', '>=', date_from))
        else:
            # Default to last 30 days
            date_from = fields.Date.today() - timedelta(days=30)
            domain.append(('date', '>=', date_from))
            
        if date_to:
            domain.append(('date', '<=', date_to))
        else:
            date_to = fields.Date.today()
            domain.append(('date', '<=', date_to))
            
        if courier_id:
            domain.append(('courier_id', '=', courier_id))
            
        if zone_id:
            domain.append(('zone_id', '=', zone_id))
            
        reports = self.search(domain)
        
        # Aggregate data
        total_deliveries = sum(reports.mapped('total_deliveries'))
        successful_deliveries = sum(reports.mapped('successful_deliveries'))
        failed_deliveries = sum(reports.mapped('failed_deliveries'))
        cancelled_deliveries = sum(reports.mapped('cancelled_deliveries'))
        
        # Calculate success rate
        success_rate = 0
        if total_deliveries:
            success_rate = (successful_deliveries * 100.0) / total_deliveries
            
        # Calculate average delivery time
        delivery_times = [r.avg_delivery_time for r in reports if r.avg_delivery_time > 0]
        avg_delivery_time = sum(delivery_times) / len(delivery_times) if delivery_times else 0
        
        # Total weight and revenue
        total_weight = sum(reports.mapped('total_weight'))
        total_revenue = sum(reports.mapped('total_revenue'))
        
        return {
            'date_from': date_from,
            'date_to': date_to,
            'total_deliveries': total_deliveries,
            'successful_deliveries': successful_deliveries,
            'failed_deliveries': failed_deliveries,
            'cancelled_deliveries': cancelled_deliveries,
            'success_rate': success_rate,
            'avg_delivery_time': avg_delivery_time,
            'total_weight': total_weight,
            'total_revenue': total_revenue,
            'reports': reports,
        }
