# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    product_availability = fields.Selection([("in_stock", "In stock"),
        ("limited", "Limited"), ("out_of_stock", "Out of stock")],
        default="in_stock", required=True)
