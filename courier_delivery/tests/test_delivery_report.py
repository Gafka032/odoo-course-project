from datetime import datetime, timedelta
from odoo.tests.common import TransactionCase


class TestDeliveryReport(TransactionCase):
    """
    Test cases for the courier.delivery.report model and wizard.
    """

    def setUp(self):
        """
        Set up test data for delivery report tests.
        """
        super(TestDeliveryReport, self).setUp()

        # Create test data
        self.partner = self.env.ref('base.res_partner_1')
        self.recipient = self.env.ref('base.res_partner_2')
        self.courier = self.env.ref('base.user_demo')

        # Set courier flag on demo user
        self.courier.write({'is_courier': True})

        # Create a test zone
        self.zone = self.env['courier.delivery.zone'].create({
            'name': 'Test Zone',
            'code': 'TEST',
            'factor': 1.0,
            'active': True
        })

        # Create test delivery orders
        self.delivery1 = self.env['courier.delivery.order'].create({
            'partner_id': self.partner.id,
            'recipient_id': self.recipient.id,
            'delivery_address_id': self.recipient.id,
            'scheduled_date': datetime.now() + timedelta(days=1),
            'courier_id': self.courier.id,
            'zone_id': self.zone.id,
            'state': 'delivered',
            'actual_delivery_date': datetime.now(),
            'weight': 5.0,
            'package_type': 'parcel'
        })

        self.delivery2 = self.env['courier.delivery.order'].create({
            'partner_id': self.partner.id,
            'recipient_id': self.recipient.id,
            'delivery_address_id': self.recipient.id,
            'scheduled_date': datetime.now() + timedelta(days=1),
            'courier_id': self.courier.id,
            'zone_id': self.zone.id,
            'state': 'failed',
            'weight': 8.0,
            'package_type': 'fragile'
        })

        # Create report wizard
        self.report_wizard = self.env['courier.delivery.report.wizard'].create({
            'date_from': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
            'date_to': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
            'report_type': 'summary'
        })

    def test_report_wizard_creation(self):
        """
        Test that report wizard is created correctly.
        """
        self.assertTrue(self.report_wizard.date_from, "Wizard should have a start date")
        self.assertTrue(self.report_wizard.date_to, "Wizard should have an end date")
        self.assertEqual(self.report_wizard.report_type, 'summary', "Report type should be set correctly")

    def test_report_wizard_onchange(self):
        """
        Test that onchange methods in the wizard work correctly.
        """
        # Test onchange_report_type
        self.report_wizard.courier_id = self.courier.id
        self.report_wizard.zone_id = self.zone.id

        # Change to courier report type
        self.report_wizard.report_type = 'courier'
        self.report_wizard._onchange_report_type()
        self.assertEqual(self.report_wizard.courier_id.id, self.courier.id, "Courier should remain set")
        self.assertFalse(self.report_wizard.zone_id, "Zone should be cleared for courier report")

        # Change to zone report type
        self.report_wizard.courier_id = self.courier.id  # Set it again
        self.report_wizard.report_type = 'zone'
        self.report_wizard._onchange_report_type()
        self.assertFalse(self.report_wizard.courier_id, "Courier should be cleared for zone report")
        self.assertFalse(self.report_wizard.zone_id, "Zone should be cleared initially")

        # Set zone and check it remains
        self.report_wizard.zone_id = self.zone.id
        self.assertEqual(self.report_wizard.zone_id.id, self.zone.id, "Zone should be set correctly")

    def test_report_wizard_action_generate(self):
        """
        Test that the generate report action works correctly.
        """
        # Set specific filters
        self.report_wizard.write({
            'courier_id': self.courier.id,
            'report_type': 'courier'
        })

        # Generate report
        result = self.report_wizard.action_generate_report()

        # Check result
        self.assertEqual(result['type'], 'ir.actions.act_window', "Should return a window action")
        self.assertEqual(result['res_model'], 'courier.delivery.report', "Should target the report model")
        self.assertIn('domain', result, "Result should contain a domain")
        self.assertIn('context', result, "Result should contain a context")

        # Check domain includes our filters
        domain = result['domain']
        courier_filter = False
        for filter_item in domain:
            if filter_item[0] == 'courier_id':
                courier_filter = True
                self.assertEqual(filter_item[2], self.courier.id, "Domain should filter by the selected courier")
        self.assertTrue(courier_filter, "Domain should include courier filter")

        # Check that the context contains the necessary keys for filtering
        self.assertIn('search_default_group_by_date', result['context'], "Context should include date grouping")
        self.assertIn('search_default_group_by_courier', result['context'], "Context should include courier grouping for courier report type")

    def test_report_wizard_action_print(self):
        """
        Test that the print report action works correctly.
        """
        # Set specific filters
        self.report_wizard.write({
            'zone_id': self.zone.id,
            'report_type': 'zone'
        })

        # Check that the method exists and does not cause errors
        try:
            result = self.report_wizard.action_print_report()
            # If the method executed without errors, the test passed.
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"Method action_print_report raised an exception: {e}")

        # Check that the result exists
        self.assertTrue(result, "Should return a report action")

    def test_delivery_report_fields(self):
        """
        Test that the delivery report model correctly includes all required fields.
        """
        # Force initialization of the SQL view
        self.env['courier.delivery.report'].init()

        # Get report data
        report_data = self.env['courier.delivery.report'].search([], limit=1)

        # Check that we have report data
        self.assertTrue(report_data, "Should have generated report data")

        # Check that all required fields exist in the model
        # Delivery status fields
        self.assertTrue(hasattr(report_data, 'draft_deliveries'), "Should have draft_deliveries field")
        self.assertTrue(hasattr(report_data, 'confirmed_deliveries'), "Should have confirmed_deliveries field")
        self.assertTrue(hasattr(report_data, 'in_transit_deliveries'), "Should have in_transit_deliveries field")
        self.assertTrue(hasattr(report_data, 'successful_deliveries'), "Should have successful_deliveries field")
        self.assertTrue(hasattr(report_data, 'failed_deliveries'), "Should have failed_deliveries field")
        self.assertTrue(hasattr(report_data, 'cancelled_deliveries'), "Should have cancelled_deliveries field")

        # Pickup status fields
        self.assertTrue(hasattr(report_data, 'total_pickups'), "Should have total_pickups field")
        self.assertTrue(hasattr(report_data, 'draft_pickups'), "Should have draft_pickups field")
        self.assertTrue(hasattr(report_data, 'confirmed_pickups'), "Should have confirmed_pickups field")
        self.assertTrue(hasattr(report_data, 'assigned_pickups'), "Should have assigned_pickups field")
        self.assertTrue(hasattr(report_data, 'picked_pickups'), "Should have picked_pickups field")
        self.assertTrue(hasattr(report_data, 'warehouse_pickups'), "Should have warehouse_pickups field")
        self.assertTrue(hasattr(report_data, 'cancelled_pickups'), "Should have cancelled_pickups field")
