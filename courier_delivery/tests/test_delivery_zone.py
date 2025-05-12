from odoo.tests.common import TransactionCase


class TestDeliveryZone(TransactionCase):
    """
    Test cases for the courier.delivery.zone model.
    """

    def setUp(self):
        """
        Set up test data for delivery zone tests.
        """
        super(TestDeliveryZone, self).setUp()

        # Create test couriers
        self.courier1 = self.env.ref('base.user_demo')
        self.courier2 = self.env.ref('base.user_admin')

        # Set courier flag on demo users
        self.courier1.write({'is_courier': True})
        self.courier2.write({'is_courier': True})

        # Create a test partner
        self.partner = self.env['res.partner'].create({
            'name': 'Test Partner',
            'street': 'Test Street',
            'city': 'Test City',
            'zip': '12345',
            'country_id': self.env.ref('base.ua').id
        })

        # Create a test zone
        self.zone = self.env['courier.delivery.zone'].create({
            'name': 'Test Zone',
            'code': 'TEST',
            'factor': 1.2,
            'active': True,
            'delivery_time_estimate': 3.0,
            'courier_ids': [(6, 0, [self.courier1.id])],
            'zip_codes': '12345,12346,12347'
        })

    def test_zone_creation(self):
        """
        Test that delivery zone is created correctly.
        """
        self.assertTrue(self.zone.name, "Zone should have a name")
        self.assertEqual(self.zone.code, 'TEST',
                         "Zone code should be set correctly")
        self.assertEqual(self.zone.factor, 1.2,
                         "Price factor should be set correctly")
        self.assertTrue(self.zone.active, "Zone should be active")
        self.assertEqual(self.zone.delivery_time_estimate, 3.0,
                         "Delivery time estimate should be set correctly")
        self.assertEqual(len(self.zone.courier_ids), 1,
                         "Zone should have one courier")

    def test_courier_count(self):
        """
        Test that courier count is computed correctly.
        """
        # Initially there should be one courier
        self.assertEqual(self.zone.courier_count, 1,
                         "Zone should have one courier")

        # Add another courier
        self.zone.write({
            'courier_ids': [(4, self.courier2.id)]
        })

        # Refresh and check count
        self.zone._compute_courier_count()
        self.assertEqual(self.zone.courier_count, 2,
                         "Zone should have two couriers")

        # Remove all couriers
        self.zone.write({
            'courier_ids': [(5, 0, 0)]
        })

        # Refresh and check count
        self.zone._compute_courier_count()
        self.assertEqual(self.zone.courier_count, 0,
                         "Zone should have no couriers")

    def test_delivery_count(self):
        """
        Test that delivery count is computed correctly.
        """
        # Initially there should be no deliveries
        self.assertEqual(self.zone.delivery_count, 0,
                         "New zone should have no deliveries")

        # Create a delivery order associated with this zone
        # Using a future date to avoid validation errors
        from datetime import datetime, timedelta
        future_date = ((datetime.now() + timedelta(days=30)).
                       strftime('%Y-%m-%d %H:%M:%S'))

        self.env['courier.delivery.order'].create({
            'partner_id': self.partner.id,
            'recipient_id': self.partner.id,
            'delivery_address_id': self.partner.id,
            'scheduled_date': future_date,
            'zone_id': self.zone.id,
        })

        # Refresh and check count
        self.zone._compute_delivery_count()
        self.assertEqual(self.zone.delivery_count, 1,
                         "Zone should have one delivery")

        # Create another delivery order
        # Using a future date to avoid validation errors
        future_date2 = ((datetime.now() + timedelta(days=60)).
                        strftime('%Y-%m-%d %H:%M:%S'))

        self.env['courier.delivery.order'].create({
            'partner_id': self.partner.id,
            'recipient_id': self.partner.id,
            'delivery_address_id': self.partner.id,
            'scheduled_date': future_date2,
            'zone_id': self.zone.id,
        })

        # Refresh and check count
        self.zone._compute_delivery_count()
        self.assertEqual(self.zone.delivery_count, 2,
                         "Zone should have two deliveries")

    def test_get_zone_for_address(self):
        """
        Test that get_zone_for_address works correctly.
        """
        # Create a partner with matching ZIP code
        partner_match = self.env['res.partner'].create({
            'name': 'Partner with matching ZIP',
            'street': 'Match Street',
            'city': 'Match City',
            'zip': '12345',  # Matches zone's ZIP codes
            'country_id': self.env.ref('base.ua').id
        })

        # Create a partner with non-matching ZIP code
        partner_no_match = self.env['res.partner'].create({
            'name': 'Partner with non-matching ZIP',
            'street': 'No Match Street',
            'city': 'No Match City',
            'zip': '99999',  # Doesn't match any zone
            'country_id': self.env.ref('base.ua').id
        })

        # Test with matching partner
        found_zone = (self.env['courier.delivery.zone'].
                      get_zone_for_address(partner_match.id))
        self.assertEqual(found_zone.id, self.zone.id,
                         "Should find the correct zone for matching ZIP")

        # Test with partner that does not match any zone
        # Must return the first active zone
        found_zone = (self.env['courier.delivery.zone'].
                      get_zone_for_address(partner_no_match.id))
        # We check that the zone was found, but we do not check the specific ID
        self.assertTrue(found_zone,
                        "Should return an active zone for "
                        "non-matching ZIP")

        # Create another zone with higher priority
        zone2 = self.env['courier.delivery.zone'].create({
            'name': 'Another Zone',
            'code': 'ANOTHER',
            'factor': 1.0,
            'active': True,
            'zip_codes': '99999'
        })

        # Test again with non-matching partner
        # Now should find the new zone
        found_zone = (self.env['courier.delivery.zone'].
                      get_zone_for_address(partner_no_match.id))
        self.assertEqual(found_zone.id, zone2.id,
                         "Should find the correct zone for newly matching ZIP")
