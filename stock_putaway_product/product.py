# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution, third party addon
#    Copyright (C) 2017- Vertel AB (<http://vertel.se>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import models, fields, api, _
import logging
_logger = logging.getLogger(__name__)

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    stock_location_id = fields.Many2one(string='Stock Location', comodel_name='stock.location', help="The stock location where this product should be warehoused. Can be defined on Templates or Variants. Variants have priority.")

class ProductProduct(models.Model):
    _inherit = 'product.product'

    stock_location_id = fields.Many2one(string='Stock Location', comodel_name='stock.location', help="The stock location where this product should be warehoused. Can be defined on Templates or Variants. Variants have priority.")

class ProductPutawayStrategy(models.Model):
    _inherit = 'product.putaway'

    @api.model
    def _get_putaway_options(self):
        return super(ProductPutawayStrategy, self)._get_putaway_options() + [('fixed_per_product', 'Fixed Location per Product')]

    method = fields.Selection(string="Method", selection=_get_putaway_options, required=True)

    @api.model
    def putaway_apply(self, putaway_strat, product):
        if putaway_strat.method == 'fixed_per_product':
            if product.stock_location_id:
                return product.stock_location_id.id
            if product.product_tmpl_id.stock_location_id:
                return product.product_tmpl_id.stock_location_id.id
        else:
            return super(ProductPutawayStrategy, self).putaway_apply(putaway_strat, product)
