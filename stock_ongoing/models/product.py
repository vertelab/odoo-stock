import logging

from odoo import models, fields, api
from odoo.exceptions import UserError
from zeep.exceptions import Fault

_logger = logging.getLogger(__name__)


class ProductProduct(models.Model):
    _inherit = 'product.product'

    ongoing_article_number = fields.Char(string="Ongoing Article Number")

    ongoing_article_id = fields.Char(string="Ongoing Article ID", readonly=True)

    def ongoing_article_definition(self):
        self.ensure_one()

        if not self.ongoing_article_number:
            raise UserError(f"Please set an Ongoing article number for product {self.name}.")

        article_definition = {
            'art': {
                'ArticleOperation': 'CreateOrUpdate',
                'ArticleIdentification': 'ArticleNumber',
                'ArticleNumber': self.ongoing_article_number,
                'ArticleName': self.name,
                'ArticleDescription': 'Detta är för att testa att skapa en produkt från Odoo',
                'CountryOfOriginCode': 'SE',
                'Weight': self.weight,
                'NetWeight': self.weight,
                'Volume': self.volume,
            }
        }
        return article_definition

    def sync_product_to_ongoing(self):
        self.ensure_one()
        client = self.env.company.ongoing_client(action="ProcessArticle")
        auth_data = self.env.company.ongoing_auth()

        data = {**auth_data, **self.ongoing_article_definition()}

        try:
            response = client.service.ProcessArticle(**data)
            _logger.info(f"Response: {response}")
            self.message_post(body="Product synced to ongoing successfully.")
        except Fault as e:
            # Handle SOAP faults
            _logger.error(f"SOAP Fault: {e}")
            self.message_post(body=f"SOAP Fault: {e}")
        except Exception as e:
            # Handle general exceptions
            _logger.error(f"An error occurred: {e}")
            self.message_post(body=f"An error occurred: {e}")


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def sync_product_to_ongoing(self):
        if len(self.product_variant_ids) == 1:
            self.product_variant_ids.sync_product_to_ongoing()

    @api.depends('product_variant_ids', 'product_variant_ids.ongoing_article_number')
    def _compute_ongoing_article_number(self):
        # Depends on force_company context because standard_price is company_dependent
        # on the product_product
        unique_variants = self.filtered(lambda template: len(template.product_variant_ids) == 1)
        for template in unique_variants:
            template.ongoing_article_number = template.product_variant_ids.ongoing_article_number
        for template in (self - unique_variants):
            template.ongoing_article_number = False

    def _set_ongoing_article_number(self):
        for template in self:
            if len(template.product_variant_ids) == 1:
                template.product_variant_ids.ongoing_article_number = template.ongoing_article_number

    ongoing_article_number = fields.Char(string="Ongoing Article Number", compute="_compute_ongoing_article_number",
                                         inverse="_set_ongoing_article_number")

    @api.depends('product_variant_ids', 'product_variant_ids.ongoing_article_id')
    def _compute_ongoing_article_id(self):
        # Depends on force_company context because standard_price is company_dependent
        # on the product_product
        unique_variants = self.filtered(lambda template: len(template.product_variant_ids) == 1)
        for template in unique_variants:
            template.ongoing_article_id = template.product_variant_ids.ongoing_article_id
        for template in (self - unique_variants):
            template.ongoing_article_id = False

    def _set_ongoing_article_id(self):
        for template in self:
            if len(template.product_variant_ids) == 1:
                template.product_variant_ids.ongoing_article_id = template.ongoing_article_id

    ongoing_article_id = fields.Char(string="Ongoing Article ID", readonly=True, compute="_compute_ongoing_article_id",
                                     inverse="_set_ongoing_article_id")
