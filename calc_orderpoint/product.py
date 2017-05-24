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
from datetime import timedelta,date
import logging
_logger = logging.getLogger(__name__)
import time

class product_template(models.Model):
    _inherit = 'product.template'

    @api.one
    @api.depends('product_variant_ids.sale_order_lines')
    def _consumtion_per_day(self):
        sales = self.env['sale.order.line'].search([('product_id','in',self.product_variant_ids.mapped('id')),('order_id.date_order','>',fields.Date.to_string(date.today() - timedelta(days=365)))],order='order_id desc')
        if len(sales)>0:
            sale_nbr_days = (date.today() - fields.Date.from_string(sales[0].order_id.date_order)).days
            qty = sum(sales.mapped('product_uom_qty'))
            self.consumtion_per_day = qty / sale_nbr_days
            self.virtual_available_days = self.virtual_available / (self.consumtion_per_day or 1.0)
            self.instock_percent = self.sudo().virtual_available / (self.orderpoint_computed or 1.0) * 100
    consumtion_per_day = fields.Float(compute="_consumtion_per_day",store=True)
    orderpoint_computed = fields.Float(compute="_consumtion_per_day",store=True)
    virtual_available_days = fields.Float(compute="_consumtion_per_day",store=True)
    instock_percent = fields.Integer(compute="_consumtion_per_day",store=True)
   

class product_product(models.Model):
    _inherit = 'product.product'

    @api.one
    @api.depends('sale_order_lines','seller_ids.delay','produce_delay')
    def _consumtion_per_day(self):
        sales = self.env['sale.order.line'].search([('product_id','=',self.id),('order_id.date_order','>',fields.Date.to_string(date.today() - timedelta(days=365)))],order='order_id desc')
        if len(sales)>0:
            sale_nbr_days = (date.today() - fields.Date.from_string(sales[0].order_id.date_order)).days
            self.sales_count = sum(sales.mapped('product_uom_qty'))
            self.consumtion_per_day = self.sales_count / sale_nbr_days
            if min(self.seller_ids.mapped('delay') or [0.0])>0.0:
                delay = min(self.seller_ids.mapped('delay')) + self.company_id.po_lead
            else:
                delay = self.produce_delay + self.company_id.manufacturing_lead
            self.orderpoint_computed =  self.consumtion_per_day * delay
            self.virtual_available_days = self.virtual_available / (self.consumtion_per_day or 1.0)
            self.instock_percent = self.sudo().virtual_available / (self.orderpoint_computed or 1.0) * 100
            
    sales_count = fields.Integer(compute="_consumtion_per_day",string='# Sales',store=True)  # Initially defined in sale-module
    consumtion_per_day = fields.Float(compute="_consumtion_per_day",store=True)
    orderpoint_computed = fields.Float(compute="_consumtion_per_day",store=True)
    virtual_available_days = fields.Float(compute="_consumtion_per_day",store=True)
    instock_percent = fields.Integer(compute="_consumtion_per_day",store=True)

    sale_order_lines = fields.One2many(comodel_name='sale.order.line',inverse_name="product_id")	
        

class stock_warehouse_orderpoint(models.Model):
    _inherit = "stock.warehouse.orderpoint"

    orderpoint_computed = fields.Float(related="product_id.orderpoint_computed")
    