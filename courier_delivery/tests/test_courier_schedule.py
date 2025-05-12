from datetime import datetime, timedelta
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestCourierSchedule(TransactionCase):
    """
    Test cases for the courier.schedule model.
    """

    def setUp(self):
        """
        Set up test data for courier schedule tests.
        """
        super(TestCourierSchedule, self).setUp()

        # Get demo data
        self.courier = self.env.ref('base.user_demo')

        # Set courier flag on demo user
        self.courier.write({'is_courier': True})

        # Create test zones
        self.zone1 = self.env['courier.delivery.zone'].create({
            'name': 'Test Zone 1',
            'code': 'TEST1',
            'factor': 1.0,
            'active': True
        })

        self.zone2 = self.env['courier.delivery.zone'].create({
            'name': 'Test Zone 2',
            'code': 'TEST2',
            'factor': 1.2,
            'active': True
        })

        # Create a test schedule
        self.schedule = self.env['courier.schedule'].create({
            'courier_id': self.courier.id,
            'date': datetime.now().date(),
            'start_time': 8.0,  # 8:00 AM
            'end_time': 16.0,   # 4:00 PM
            'zone_ids': [(6, 0, [self.zone1.id, self.zone2.id])],
            'notes': 'Test schedule'
        })

    def test_schedule_creation(self):
        """
        Test that schedule is created correctly.
        """
        self.assertTrue(self.schedule.name, "Schedule should have a name")
        self.assertEqual(self.schedule.state, 'draft', "New schedule should be in draft state")
        self.assertEqual(self.schedule.courier_id, self.courier, "Courier should be set correctly")
        self.assertEqual(len(self.schedule.zone_ids), 2, "Schedule should have two zones")

    def test_schedule_workflow(self):
        """
        Test the schedule workflow: draft -> confirmed -> in_progress -> completed.
        """
        # Test confirm action
        self.schedule.action_confirm()
        self.assertEqual(self.schedule.state, 'confirmed', "Schedule should be in confirmed state")

        # Test start action
        self.schedule.action_start()
        self.assertEqual(self.schedule.state, 'in_progress', "Schedule should be in in_progress state")

        # Test complete action
        self.schedule.action_complete()
        self.assertEqual(self.schedule.state, 'completed', "Schedule should be in completed state")

        # Test cancel action (from draft state)
        self.schedule.action_reset_to_draft()
        self.schedule.action_cancel()
        self.assertEqual(self.schedule.state, 'cancelled', "Schedule should be in cancelled state")

        # Test reset to draft action
        self.schedule.action_reset_to_draft()
        self.assertEqual(self.schedule.state, 'draft', "Schedule should be back in draft state")

    def test_compute_working_hours(self):
        """
        Test that working hours are computed correctly.
        """
        # Regular shift
        self.schedule.start_time = 8.0
        self.schedule.end_time = 16.0
        self.schedule._compute_working_hours()
        self.assertEqual(self.schedule.working_hours, 8.0, "Working hours should be 8")

        # Partial hours
        self.schedule.start_time = 8.5
        self.schedule.end_time = 17.25
        self.schedule._compute_working_hours()
        self.assertEqual(self.schedule.working_hours, 8.75, "Working hours should be 8.75")

        # Overnight shift
        self.schedule.start_time = 22.0
        self.schedule.end_time = 6.0
        self.schedule._compute_working_hours()
        self.assertEqual(self.schedule.working_hours, 8.0, "Working hours for overnight shift should be 8")

    def test_compute_date_range(self):
        """
        Test that date range is computed correctly.
        """
        today = datetime.now().date()
        self.schedule.date = today
        self.schedule.start_time = 8.0
        self.schedule.end_time = 16.0
        self.schedule._compute_date_range()

        # Check date_start
        expected_start = datetime.combine(today, datetime.min.time()) + timedelta(hours=8)
        self.assertEqual(self.schedule.date_start.date(), expected_start.date(),
                         "Start date should be correct")
        self.assertEqual(self.schedule.date_start.hour, expected_start.hour,
                         "Start hour should be correct")

        # Check date_end
        expected_end = datetime.combine(today, datetime.min.time()) + timedelta(hours=16)
        self.assertEqual(self.schedule.date_end.date(), expected_end.date(),
                         "End date should be correct")
        self.assertEqual(self.schedule.date_end.hour, expected_end.hour,
                         "End hour should be correct")

    def test_time_validation(self):
        """
        Test that time validation works correctly.
        """
        # Test with equal start and end times
        with self.assertRaises(ValidationError):
            self.schedule.write({
                'start_time': 8.0,
                'end_time': 8.0
            })

        # Test with valid times (should work)
        self.schedule.write({
            'start_time': 8.0,
            'end_time': 16.0
        })
        self.assertEqual(self.schedule.start_time, 8.0, "Start time should be updated correctly")
        self.assertEqual(self.schedule.end_time, 16.0, "End time should be updated correctly")

    def test_overlap_validation(self):
        """
        Test that schedule overlap validation works correctly.
        """
        # Create an overlapping schedule
        with self.assertRaises(ValidationError):
            self.env['courier.schedule'].create({
                'courier_id': self.courier.id,
                'date': self.schedule.date,
                'start_time': 10.0,  # Overlaps with existing 8.0-16.0 schedule
                'end_time': 18.0,
                'zone_ids': [(6, 0, [self.zone1.id])],
            })

        # Create a non-overlapping schedule (different date)
        tomorrow = datetime.now().date() + timedelta(days=1)
        non_overlapping = self.env['courier.schedule'].create({
            'courier_id': self.courier.id,
            'date': tomorrow,
            'start_time': 8.0,
            'end_time': 16.0,
            'zone_ids': [(6, 0, [self.zone1.id])],
        })
        self.assertTrue(non_overlapping.id, "Non-overlapping schedule should be created")

        # Create a non-overlapping schedule (different time)
        evening = self.env['courier.schedule'].create({
            'courier_id': self.courier.id,
            'date': self.schedule.date,
            'start_time': 18.0,  # After existing schedule
            'end_time': 22.0,
            'zone_ids': [(6, 0, [self.zone1.id])],
        })
        self.assertTrue(evening.id, "Non-overlapping evening schedule should be created")
