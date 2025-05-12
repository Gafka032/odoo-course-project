from odoo import models, api


class DeliverySlipReport(models.AbstractModel):
    """
    Abstract model for delivery slip report.

    This model provides the data for the QWeb delivery slip report.
    """
    _name = 'report.courier_delivery.report_delivery_slip'
    _description = 'Delivery Slip Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        """
        Prepare the data for the delivery slip report.

        Args:
            docids: IDs of the documents to print
            data: Additional data

        Returns:
            Dictionary with report values
        """
        docs = self.env['courier.delivery.order'].browse(docids)

        return {
            'doc_ids': docids,
            'doc_model': 'courier.delivery.order',
            'docs': docs,
            'data': data,
        }
