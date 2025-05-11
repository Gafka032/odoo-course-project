from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta


class TestDeliveryOrder(TransactionCase):
    """
    Test cases for the courier.delivery.order model.
    """

    def setUp(self):
        """
        Set up test data for delivery order tests.
        """
        super(TestDeliveryOrder, self).setUp()
        
        # Get demo data
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
        
        # Create a test delivery order
        self.delivery_order = self.env['courier.delivery.order'].create({
            'pickup_request_id': self.pickup_request.id,
            'partner_id': self.partner.id,
            'recipient_id': self.recipient.id,
            'delivery_address_id': self.recipient.id,
            'scheduled_date': datetime.now() + timedelta(days=1),
            'zone_id': self.zone.id,
            'weight': 5.0,
            'package_type': 'parcel'
        })

    def test_delivery_order_creation(self):
        """
        Test that delivery order is created correctly with a sequence number.
        """
        self.assertTrue(self.delivery_order.name, "Delivery order should have a name")
        self.assertNotEqual(self.delivery_order.name, 'New', "Delivery order should have a sequence number")
        self.assertTrue(self.delivery_order.tracking_ref, "Delivery order should have a tracking reference")
        self.assertEqual(self.delivery_order.state, 'draft', "New delivery order should be in draft state")
        self.assertEqual(self.delivery_order.partner_id, self.partner, "Partner should be set correctly")
        self.assertEqual(self.delivery_order.recipient_id, self.recipient, "Recipient should be set correctly")

    def test_delivery_order_workflow(self):
        """
        Test the delivery order workflow: draft -> confirmed -> in_transit -> delivered.
        """
        # Test confirm action
        self.delivery_order.action_confirm()
        self.assertEqual(self.delivery_order.state, 'confirmed', "Delivery order should be in confirmed state")
        
        # Test start delivery action
        with self.assertRaises(ValidationError):
            # Should raise error if no courier assigned
            self.delivery_order.action_start_delivery()
        
        # Assign courier and try again
        self.delivery_order.courier_id = self.courier.id
        self.delivery_order.action_start_delivery()
        self.assertEqual(self.delivery_order.state, 'in_transit', "Delivery order should be in in_transit state")
        
        # Test mark as delivered action
        self.delivery_order.action_mark_delivered()
        self.assertEqual(self.delivery_order.state, 'delivered', "Delivery order should be in delivered state")
        self.assertTrue(self.delivery_order.actual_delivery_date, "Actual delivery date should be set")
        
        # Test cancel action (from draft state)
        self.delivery_order.action_reset_to_draft()
        self.delivery_order.action_cancel()
        self.assertEqual(self.delivery_order.state, 'cancelled', "Delivery order should be in cancelled state")
        
        # Test reset to draft action
        self.delivery_order.action_reset_to_draft()
        self.assertEqual(self.delivery_order.state, 'draft', "Delivery order should be back in draft state")

    def test_delivery_fee_computation(self):
        """
        Test that delivery fee is computed correctly.
        """
        # Test with different weights
        self.delivery_order.weight = 0.5  # Light package
        self.delivery_order._compute_delivery_fee()
        light_fee = self.delivery_order.delivery_fee
        
        self.delivery_order.weight = 7.0  # Medium package
        self.delivery_order._compute_delivery_fee()
        medium_fee = self.delivery_order.delivery_fee
        
        self.delivery_order.weight = 15.0  # Heavy package
        self.delivery_order._compute_delivery_fee()
        heavy_fee = self.delivery_order.delivery_fee
        
        self.assertLess(light_fee, medium_fee, "Heavier packages should cost more")
        self.assertLess(medium_fee, heavy_fee, "Heavier packages should cost more")
        
        # Test with different package types
        self.delivery_order.weight = 5.0  # Reset weight
        
        self.delivery_order.package_type = 'document'
        self.delivery_order._compute_delivery_fee()
        document_fee = self.delivery_order.delivery_fee
        
        self.delivery_order.package_type = 'parcel'
        self.delivery_order._compute_delivery_fee()
        parcel_fee = self.delivery_order.delivery_fee
        
        self.delivery_order.package_type = 'fragile'
        self.delivery_order._compute_delivery_fee()
        fragile_fee = self.delivery_order.delivery_fee
        
        self.assertLess(document_fee, parcel_fee, "Documents should cost less than parcels")
        self.assertLess(parcel_fee, fragile_fee, "Fragile packages should cost more than regular parcels")
        
        # Test with different zones
        expensive_zone = self.env['courier.delivery.zone'].create({
            'name': 'Expensive Zone',
            'code': 'EXP',
            'factor': 2.0,
            'active': True
        })
        
        self.delivery_order.package_type = 'parcel'  # Reset package type
        
        self.delivery_order.zone_id = self.zone  # Standard zone
        self.delivery_order._compute_delivery_fee()
        standard_zone_fee = self.delivery_order.delivery_fee
        
        self.delivery_order.zone_id = expensive_zone  # Expensive zone
        self.delivery_order._compute_delivery_fee()
        expensive_zone_fee = self.delivery_order.delivery_fee
        
        self.assertLess(standard_zone_fee, expensive_zone_fee, "Expensive zones should cost more")

    def test_scheduled_date_validation(self):
        """
        Test that scheduled date validation works correctly.
        """
        # Test with past date
        with self.assertRaises(ValidationError):
            self.delivery_order.write({
                'scheduled_date': datetime.now() - timedelta(days=1)
            })
        
        # Test with future date (should work)
        future_date = datetime.now() + timedelta(days=2)
        self.delivery_order.write({
            'scheduled_date': future_date
        })
        self.assertEqual(self.delivery_order.scheduled_date.date(), future_date.date(), 
                         "Scheduled date should be updated correctly")

    def test_onchange_recipient(self):
        """
        Test that onchange_recipient updates delivery address correctly.
        """
        new_recipient = self.env.ref('base.res_partner_3')
        self.delivery_order.recipient_id = new_recipient.id
        self.delivery_order._onchange_recipient_id()
        self.assertEqual(self.delivery_order.delivery_address_id, new_recipient, 
                         "Delivery address should be updated when recipient changes")

    def test_onchange_pickup_request(self):
        """
        Test that onchange_pickup_request updates fields correctly.
        """
        # Create a new pickup request with different values
        new_partner = self.env.ref('base.res_partner_3')
        new_courier = self.env.ref('base.user_admin')
        new_courier.write({'is_courier': True})
        
        new_pickup = self.env['courier.pickup.request'].create({
            'partner_id': new_partner.id,
            'pickup_address_id': new_partner.id,
            'request_date': datetime.now(),
            'pickup_date': datetime.now() + timedelta(days=1),
            'courier_id': new_courier.id,
            'weight': 20.0,
            'package_count': 4
        })
        
        # Update delivery order's pickup request
        self.delivery_order.pickup_request_id = new_pickup.id
        self.delivery_order._onchange_pickup_request_id()
        
        # Check that fields were updated
        self.assertEqual(self.delivery_order.partner_id, new_partner, 
                         "Partner should be updated from pickup request")
        self.assertEqual(self.delivery_order.courier_id, new_courier, 
                         "Courier should be updated from pickup request")
        self.assertEqual(self.delivery_order.weight, 5.0,  # 20.0 / 4
                         "Weight should be calculated from pickup request")
