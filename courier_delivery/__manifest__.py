{
    'name': 'Courier Delivery',
    'version': '17.0.1.5.2' ,
    'summary': 'Manage courier pickup requests and delivery orders',
    'description': """
        Courier Delivery
        This module allows you to create requests for courier pickup and manage
        delivery orders with comprehensive tracking and reporting.
        
        Features:
        - Pickup requests management
        - Delivery orders tracking
        - Courier scheduling
        - Delivery zones with pricing
        - Performance reporting and analytics
        - PDF delivery slips
    """,
    'category': 'Services',
    'author': 'Odoo School',
    'website': 'https://odoo.school/',
    'license': 'OPL-1',
    'depends': [
        'base',
        'mail',
        'web',
    ],
    'data': [
        # Security
        'security/security.xml',
        'security/ir.model.access.csv',
        
        # Data
        'data/ir_sequence_data.xml',
        
        # Views
        'views/pickup_request_views.xml',
        'views/delivery_order_views.xml',
        'views/courier_schedule_views.xml',
        'views/delivery_zone_views.xml',
        'views/delivery_report_views.xml',
        'views/delivery_report_wizard_views.xml',
        'views/res_partner_views.xml',
        'views/res_users_views.xml',
        'views/dashboard_views.xml',
        'views/menu_views.xml',
        
        # Reports
        'report/delivery_slip_report_templates.xml',
        
        # Wizards
        'wizard/delivery_report_wizard_views.xml',
    ],
    'demo': [
        # Базові дані (зони, кур'єри, партнери)
        'demo/delivery_zones_demo.xml',
        'demo/couriers_demo.xml',
        'demo/partners_demo.xml',
        # XML-дані для основних моделей
        'demo/pickup_requests_demo.xml',
        'demo/delivery_orders_demo.xml',
        'demo/courier_schedules_demo.xml',
        # CSV-дані для додаткових записів
        'demo/courier.pickup.request.csv',
        'demo/courier.delivery.order.csv',
    ],
    'assets': {
        'web.assets_backend': [
            'courier_delivery/static/src/js/**/*',
            'courier_delivery/static/src/scss/**/*',
            'courier_delivery/static/src/xml/**/*',
        ],
    },
    'auto_install': False,
    'application': True,
    'installable': True,
    'maintainer': 'Danylo Senyuk',
    'images': ['static/description/banner.png'],
}