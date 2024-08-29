import logging

from odoo import models, fields, api
from zeep.exceptions import Fault

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def send_order_to_ongoing(self):
        client = self.env.company.ongoing_client(action="ProcessOrder")
        auth_data = self.env.company.ongoing_auth()

        try:
            data = {**auth_data, **self._order_definition()}
            response = client.service.ProcessOrder(**data)
            _logger.info(f"Response: {response}")
            self.message_post(body="Order synced to ongoing successfully.")
        except Fault as e:
            # Handle SOAP faults
            _logger.error(f"SOAP Fault: {e}")
        except Exception as e:
            # Handle general exceptions
            _logger.error(f"An error occurred: {e}")

    def _customer_definition(self):
        return {
            'CustomerOperation': 'CreateOrUpdate',
            'CustomerIdentification': "FullNameAndAddress",
            'CustomerNumber': 'CN124',
            'Name': self.partner_id.name,
            'Address': self.partner_id.street or None,
            'Address2': self.partner_id.street2 or None,
            'PostCode': self.partner_id.zip or None,
            'City': self.partner_id.city or None,
            'CountryCode': self.partner_id.country_id.code or 'SE',
            'IsVisible': True,
            'NotifyBySMS': True,
            'NotifyByEmail': True,
            'NotifyByTelephone': False
        }

    def _order_definition(self):
        data = {
            'co': {
                'OrderInfo': {
                    'OrderIdentification': "GoodsOwnerOrderNumber",
                    'GoodsOwnerOrderNumber': self.name,
                    'OrderOperation': 'CreateOrUpdate',
                    'DeliveryDate': self.scheduled_date
                },
                'Customer': self._customer_definition(),
                'CustomerOrderLines': {
                    'CustomerOrderLine': self._order_line_definition()
                }
            }

        }
        return data

    def _order_line_definition(self):
        orders = [
            {
                'ArticleIdentification': "ArticleNumber",
                'OrderLineIdentification': "ArticleNumber",
                'ExternalOrderLineCode': i + 1,
                'ArticleNumber': line.product_id.ongoing_article_number,
                'NumberOfItems': line.quantity,
            }
            for i, line in enumerate(self.move_ids_without_package)
        ]
        return orders
