# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Enterprise Management Solution, third party addon
#    Copyright (C) 2018 Vertel AB (<http://vertel.se>).
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
from odoo import models, fields, api, _

import logging
_logger = logging.getLogger(__name__)


class stock_warehouse_orderpoint(models.Model):
    _inherit = 'stock.warehouse.orderpoint'

    supplier_id = fields.Many2one(string='Supplier', comodel_name='res.partner', compute='_supplier_id', store=True)
    categ_id = fields.Many2one(string='Category', comodel_name='product.category', related='product_id.categ_id')
    public_categ_id = fields.Many2one(string='Public category', comodel_name='product.public.category', compute='_public_categ_id', store=True)

    @api.one
    @api.depends('product_id', 'product_id.seller_ids', 'product_id.seller_ids.name')
    def _supplier_id(self):
        # get the first supplier
        seller_ids = self.product_id.seller_ids
        if len(seller_ids) > 0:
            self.supplier_id = seller_ids[0].name

    @api.one
    @api.depends('product_id', 'product_id.public_categ_ids')
    def _public_categ_id(self):
        # get first public category
        public_categ_ids = self.product_id.public_categ_ids
        if len(public_categ_ids) > 0:
            self.public_categ_id = public_categ_ids[0]
