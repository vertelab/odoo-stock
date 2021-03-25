# -*- coding: utf-8 -*-

from odoo import models, fields, api, http
from odoo.addons.website_sale_stock.controllers.variant import WebsiteSaleStockVariantController
from odoo.addons.website_sale_stock.models.product_template import ProductTemplate

import logging
_logger = logging.getLogger(__name__)


class Product(models.Model):
    _inherit = 'product.product'

    product_availability = fields.Selection([("in_stock", "In stock"),
        ("limited", "Limited"), ("out_of_stock", "Out of stock")],
        default="in_stock", required=True)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def _get_combination_info(self, combination=False, product_id=False,add_qty=1,
        pricelist=False, parent_combination=False, only_template=False):
        combination_info = super(ProductTemplate, self)._get_combination_info(combination=combination,
        product_id=product_id, add_qty=add_qty, pricelist=pricelist,
        parent_combination=parent_combination, only_template=only_template)

        if not self.env.context.get('website_sale_stock_ma'):
            return combination_info

        if combination_info['product_id']:
            product = self.env['product.product'].sudo().browse(combination_info['product_id'])

        else:
            product = self.sudo()

        product_availability = product.product_availability
        unlimited = 2147483648
        info = {"virtual_available": {"in_stock": unlimited, "limited": unlimited, "out_of_stock": 0},
            "available_threshold": {"in_stock": 0, "limited": unlimited, "out_of_stock": 0},
            }
        combination_info.update({
            'virtual_available': info['virtual_available'][product_availability],
            'virtual_available_formatted': "Limited",
            'product_type': product.type,
            'inventory_availability': product.inventory_availability,
            'available_threshold': info['available_threshold'][product_availability],
            'custom_message': product.custom_message,
            'product_template': product.product_tmpl_id.id,
            'cart_qty': product.cart_qty,
            'uom_name': product.uom_id.name,
        })
        return combination_info


class WebsiteSaleMaVariantController(WebsiteSaleStockVariantController):
    
    @http.route()
    def get_combination_info_website(self, product_template_id, 
        product_id, combination, add_qty, **kw):
        kw['context'] = kw.get('context', {})
        kw['context'].update(website_sale_stock_ma=True)
        combination = super(WebsiteSaleStockVariantController, self).get_combination_info_website(product_template_id,
            product_id, combination, add_qty, **kw)
        return combination
