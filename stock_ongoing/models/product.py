import logging

from odoo import models, fields, api
from odoo.exceptions import UserError
from zeep.exceptions import Fault

_logger = logging.getLogger(__name__)


class ProductProduct(models.Model):
    _inherit = 'product.template'

    ongoing_article_number = fields.Char(string="Ongoing Article Number")

    def ongoing_article_definition(self):
        self.ensure_one()

        if not self.ongoing_article_number:
            raise UserError(f"Please set an Ongoing article number for product {self.name}.")

        article_definition = {
            'art': {
                'ArticleOperation': 'CreateOrUpdate',
                'ArticleIdentification': 'ArticleNumber',
                'ArticleNumber': self.ongoing_article_number,
                'ArticleName': 'Odoo Test',
                'ArticleDescription': 'Detta är för att testa att skapa en produkt från Odoo',
                'CountryOfOriginCode': 'SE',
                'Weight': self.weight,
                'NetWeight': self.weight,
                'Volume': self.volume,
            }
        }
        return article_definition

    def sync_product_to_ongoing(self):
        client = self.env.company.ongoing_client(action="ProcessArticle")
        auth_data = self.env.company.ongoing_auth()

        try:
            data = {**auth_data, **self.ongoing_article_definition()}
            response = client.service.ProcessArticle(**data)
            _logger.info(f"Response: {response}")
            self.message_post(body="Product synced to ongoing successfully.")
        except Fault as e:
            # Handle SOAP faults
            _logger.error(f"SOAP Fault: {e}")
        except Exception as e:
            # Handle general exceptions
            _logger.error(f"An error occurred: {e}")
