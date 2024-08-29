from odoo import models, fields, api
from odoo.exceptions import UserError
from zeep.exceptions import Fault


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def send_order_to_ongoing(self):
        client = self.env.company.ongoing_client(action="ProcessOrder")
        auth_data = self.env.company.ongoing_auth()

        try:
            data = {**auth_data, **self._order_definition()}
            response = client.service.ProcessOrder(**data)
            print("Response:", response)

        except Fault as e:
            # Handle SOAP faults
            print(f"SOAP Fault: {e}")

        except Exception as e:
            # Handle general exceptions
            print(f"An error occurred: {e}")

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
        return {
            'co': {
                'OrderInfo': {
                    'OrderIdentification': "GoodsOwnerOrderNumber",
                    'GoodsOwnerOrderNumber': self.name,
                    'OrderOperation': 'CreateOrUpdate',
                    'DeliveryDate': self.scheduled_date
                },
                'Customer': self._customer_definition(),
                'CustomerOrderLines': self._order_line_definition()
            }

        }

    def _order_line_definition(self):
        orders = [
            {
                'CustomerOrderLine': {
                    'ArticleIdentification': "ArticleNumber",
                    'OrderLineIdentification': "ExternalOrderLineCode",
                    'ExternalOrderLineCode': line.id,
                    'ArticleNumber': line.product_id.ongoing_article_number,
                    'NumberOfItems': line.quantity,
                }
            } for line in self.move_ids_without_package]
        return orders
