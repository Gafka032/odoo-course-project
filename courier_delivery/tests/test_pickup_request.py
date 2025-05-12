from datetime import datetime, timedelta
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestPickupRequest(TransactionCase):
    """
    Test cases for the courier.pickup.request model.
    """

    def setUp(self):
        """
        Set up test data for pickup request tests.
        """
        super(TestPickupRequest, self).setUp()

        # Get demo data
        self.partner = self.env.ref('base.res_partner_1')
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

        # Create a test pickup request
        self.pickup_request = self.env['courier.pickup.request'].create({
            'partner_id': self.partner.id,
            'pickup_address_id': self.partner.id,
            'request_date': datetime.now(),
            'pickup_date': datetime.now() + timedelta(days=1),
            'zone_id': self.zone.id,
            'weight': 10.0,
            'package_count': 2
        })

    def test_pickup_request_creation(self):
        """
        Test that pickup request is created correctly with a sequence number.
        """
        self.assertTrue(self.pickup_request.name,
                        "Pickup request should have a name")
        self.assertNotEqual(self.pickup_request.name, 'New',
                            "Pickup request should have a sequence number")
        self.assertEqual(self.pickup_request.state, 'draft',
                         "New pickup request should be in draft state")
        self.assertEqual(self.pickup_request.partner_id, self.partner,
                         "Partner should be set correctly")

    def test_pickup_request_workflow(self):
        """
        Test the pickup request workflow: draft -> confirmed -> assigned
        -> picked.
        """
        # Test confirm action
        self.pickup_request.action_confirm()
        self.assertEqual(self.pickup_request.state, 'confirmed',
                         "Pickup request should be in confirmed state")

        # Test assign courier action
        with self.assertRaises(ValidationError):
            # Should raise error if no courier assigned
            self.pickup_request.action_assign_courier()

        # Assign courier and try again
        self.pickup_request.courier_id = self.courier.id
        self.pickup_request.action_assign_courier()
        self.assertEqual(self.pickup_request.state, 'assigned',
                         "Pickup request should be in assigned state")

        # Test mark as picked action
        self.pickup_request.action_mark_picked()
        self.assertEqual(self.pickup_request.state, 'picked',
                         "Pickup request should be in picked state")

        # Test cancel action
        self.pickup_request.action_cancel()
        self.assertEqual(self.pickup_request.state, 'cancelled',
                         "Pickup request should be in cancelled state")

        # Test reset to draft action
        self.pickup_request.action_reset_to_draft()
        self.assertEqual(self.pickup_request.state, 'draft',
                         "Pickup request should be back in draft state")

    def test_pickup_date_validation(self):
        """
        Test that pickup date validation works correctly.
        """
        # Test with past date
        with self.assertRaises(ValidationError):
            self.pickup_request.write({
                'pickup_date': datetime.now() - timedelta(days=1)
            })

        # Test with future date (should work)
        future_date = datetime.now() + timedelta(days=2)
        self.pickup_request.write({
            'pickup_date': future_date
        })
        self.assertEqual(self.pickup_request.pickup_date.date(),
                         future_date.date(),
                         "Pickup date should be updated correctly")

    def test_onchange_partner(self):
        """
        Test that onchange_partner updates pickup address correctly.
        """
        new_partner = self.env.ref('base.res_partner_2')
        self.pickup_request.partner_id = new_partner.id
        self.pickup_request._onchange_partner_id()
        self.assertEqual(self.pickup_request.pickup_address_id, new_partner,
                         "Pickup address should be updated when partner "
                         "changes")

    def test_delivery_count(self):
        """
        Test that delivery count is computed correctly.
        """
        # Initially there should be no deliveries
        self.assertEqual(self.pickup_request.delivery_count, 0,
                         "New pickup request should have no deliveries")

        # Create a delivery order linked to this pickup request
        self.env['courier.delivery.order'].create({
            'pickup_request_id': self.pickup_request.id,
            'partner_id': self.partner.id,
            'recipient_id': self.partner.id,
            'delivery_address_id': self.partner.id,
            'scheduled_date': datetime.now() + timedelta(days=1),
        })

        # Refresh and check count
        self.pickup_request._compute_delivery_count()
        self.assertEqual(self.pickup_request.delivery_count, 1,
                         "Pickup request should have one delivery")
