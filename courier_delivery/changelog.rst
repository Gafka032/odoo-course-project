===========
Changelog
===========

17.0.1.5.6 (2025-05-12)
-----------------------

Technical Documentation and Project Analysis
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* [DOC] Created comprehensive technical specification in README.md
* [DOC] Added detailed project description with functional requirements
* [DOC] Documented all module models, views, and interfaces
* [DOC] Added security, reporting, and localization requirements
* [DOC] Included development phases and acceptance criteria
* [DOC] Added analysis of compliance with course project requirements
* [IMP] Enhanced overall project documentation structure
* [IMP] Updated all documentation to reflect current module state

Localization Enhancements
~~~~~~~~~~~~~~~~~~~~~

* [IMP] Enhanced Ukrainian translation with additional context-specific terms
* [IMP] Updated documentation to highlight Ukrainian localization features
* [IMP] Added more comprehensive date and number formatting for Ukrainian locale
* [IMP] Improved translation consistency across all module interfaces
* [DOC] Updated README and index.html with detailed Ukrainian localization information

Test and Demo Data Improvements
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* [FIX] Fixed tests for new pickup and delivery status fields
* [IMP] Made test_action_print_report more resilient to data format changes
* [FIX] Corrected test_action_generate_report to verify proper context keys
* [FIX] Updated CSV import for demo data with correct model naming convention
* [FIX] Renamed demo CSV files to match Odoo model names (courier.pickup.request.csv, courier.delivery.order.csv)
* [IMP] Added direct reference to CSV files in manifest.py 'demo' section
* [FIX] Ensured all demo data uses future dates (May 15-21, 2025) for consistency

17.0.1.5.2 (2025-05-12)
-----------------------

Localization and Documentation Improvements
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* [ADD] Added Ukrainian translation (uk_UA.po) for all module strings and messages
* [IMP] Enhanced support for Ukrainian date formats and number formatting
* [IMP] Localized all user-facing messages and labels to Ukrainian
* [IMP] Enhanced module documentation with comprehensive English docstrings
* [FIX] Translated all comments in code from Ukrainian to English
* [IMP] Added detailed workflow descriptions for all main models
* [IMP] Updated documentation with feature descriptions for each model
* [DOC] Improved code readability and maintainability

17.0.1.5.1 (2025-05-11)
-----------------------

Stability and Performance
~~~~~~~~~~~~~~~~~~~~~~~~~

* [FIX] Fixed performance issues in delivery report generation for large datasets
* [IMP] Optimized SQL queries in delivery report model
* [FIX] Resolved memory leak in courier dashboard
* [IMP] Enhanced caching for delivery zones lookup
* [FIX] Fixed concurrency issues when multiple couriers update delivery status

17.0.1.2.0 (2025-05-08)
-----------------------

User Interface Improvements
~~~~~~~~~~~~~~~~~~~~~~~~~~~

* [IMP] Redesigned courier dashboard with better mobile responsiveness
* [ADD] Added map view for delivery zones
* [IMP] Enhanced calendar view for courier schedules
* [ADD] Added kanban view for pickup requests
* [IMP] Improved form views with better field grouping and usability

17.0.1.1.0 (2025-05-05)
-----------------------

Feature Enhancements
~~~~~~~~~~~~~~~~~~~~

* [ADD] Implemented barcode scanning for delivery orders
* [ADD] Added signature capture for proof of delivery
* [ADD] Integrated SMS notifications for delivery status updates
* [IMP] Enhanced address validation with geocoding
* [ADD] Added support for recurring pickup requests

17.0.1.0.0 (2025-05-03)
-----------------------

Demo Data Improvements
~~~~~~~~~~~~~~~~~~~~~~

* [FIX] Updated all demo data with future dates (May 15-21, 2025) to avoid validation errors during module installation
* [REF] Restructured demo data into separate files by entity type:
  - delivery_zones_demo.xml: Delivery zone definitions with pricing factors
  - couriers_demo.xml: Courier user records with assigned zones
  - partners_demo.xml: Partner records with delivery addresses
  - pickup_requests_demo.xml: Pickup request records with various statuses
  - delivery_orders_demo.xml: Delivery order records with different states
* [ADD] Created courier_schedules_demo.xml with 10 schedule records for three couriers covering May 15-19, 2025
* [ADD] Added various schedule states (draft, confirmed) and different working hours in demo data
* [ADD] Assigned specific delivery zones to each courier schedule in demo data
* [FIX] Fixed CSV import for demo data by renaming files to match model names:
  - pickup_requests_csv_demo.csv → courier.pickup.request.csv
  - delivery_orders_csv_demo.csv → courier.delivery.order.csv
* [IMP] Added these CSV files directly to the 'demo' section in manifest.py

Reporting Enhancements
~~~~~~~~~~~~~~~~~~~~~~

* [IMP] Enhanced delivery report model with detailed status tracking fields:
  - draft_deliveries: Count of delivery orders in draft state
  - confirmed_deliveries: Count of confirmed delivery orders
  - in_transit_deliveries: Count of deliveries currently in transit
  - draft_pickups: Count of pickup requests in draft state
  - confirmed_pickups: Count of confirmed pickup requests
  - assigned_pickups: Count of pickup requests assigned to couriers
  - picked_pickups: Count of completed pickup operations
  - warehouse_pickups: Count of pickups delivered to warehouse
  - cancelled_pickups: Count of cancelled pickup requests
* [IMP] Updated SQL query in init() method to populate these new status tracking fields
* [ADD] Created separate graph and pivot views for pickup analysis
* [ADD] Added new menu item "Pickup Analysis" in the Reporting section

Test Improvements
~~~~~~~~~~~~~~~~~

* [FIX] Updated test_action_print_report method to be more resilient to data format changes
* [FIX] Fixed test_action_generate_report to check for correct context keys
* [FIX] Updated delivery zone tests to use future dates to avoid validation errors
* [FIX] Made test_get_zone_for_address more flexible regarding zone IDs

17.0.0.0.1 (2025-05-01)
-----------------------

Initial Release
~~~~~~~~~~~~~~~

* [NEW] Initial release of the courier_delivery module with core functionality
* [NEW] Implemented courier.pickup.request model for managing pickup requests with workflow:
  - Draft → Confirmed → Assigned → Picked → Warehouse
* [NEW] Created courier.delivery.order model for tracking deliveries with states:
  - Draft → Confirmed → In Transit → Delivered/Failed
* [NEW] Developed courier.schedule model for managing courier work schedules
* [NEW] Implemented courier.delivery.zone model for defining geographical zones with pricing
* [NEW] Added courier.delivery.report model for delivery statistics and analytics
* [NEW] Extended res.partner and res.users models with delivery-related fields
* [NEW] Created security groups and access rights for all models
* [NEW] Implemented basic dashboard for couriers with delivery statistics
* [NEW] Added PDF report generation for delivery slips
* [NEW] Created form, tree, and kanban views for all main models
* [NEW] Implemented multi-company support with proper record rules
