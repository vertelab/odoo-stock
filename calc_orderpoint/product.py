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
import timeit

class product_template(models.Model):
    _inherit = 'product.template'
    @api.one
    def _sales_per_day(self):
        if min(self.seller_ids.mapped('delay') or [0.0])>0.0:
            delay = min(self.seller_ids.mapped('delay')) + self.company_id.po_lead
        else:
            delay = self.produce_delay + self.company_id.manufacturing_lead
        first_sales = self.env['sale.order.line'].search([('product_id','=',self.id),('order_id.date_order','>',fields.Date.to_string(date.today() - timedelta(days=365)))],order='order_id asc',limit=1)
        if len(first_sales)>0:
            sale_nbr_days = (date.today() - fields.Date.from_string(first_sales.order_id.date_order)).days
            res = self.env['sale.report'].read_group([('product_id','in',self.product_variant_ids.mapped('id')),('date_confirm','>',fields.Date.to_string(date.today() - timedelta(days=365)))],['product_id','product_uom_qty'],['product_id'])
            if len(res)>0:
                self.consumtion_per_day = res[0]['product_uom_qty'] / sale_nbr_days
                self.orderpoint_computed =  self.consumtion_per_day * delay
                self.virtual_available_days = self.virtual_available / self.consumtion_per_day        
    consumtion_per_day = fields.Float(compute="_sales_per_day")
    orderpoint_computed = fields.Float(compute="_sales_per_day")
    virtual_available_days = fields.Float(compute="_sales_per_day")

    @api.one
    @api.depends('seller_ids','seller_ids.delay','produce_delay')
    def _instock_percent(self):
        self.instock_percent = self.virtual_available / self.orderpoint_computed * 100
    instock_percent = fields.Integer(compute="_instock_percent",store=True,help='This is how much we have in stock in percent')


class product_product(models.Model):
    _inherit = 'product.product'
    
    @api.one
    def _sales_per_day(self):
        if min(self.seller_ids.mapped('delay') or [0.0])>0.0:
            delay = min(self.seller_ids.mapped('delay')) + self.company_id.po_lead
        else:
            delay = self.produce_delay + self.company_id.manufacturing_lead
        first_sales = self.env['sale.order.line'].search([('product_id','=',self.id),('order_id.date_order','>',fields.Date.to_string(date.today() - timedelta(days=365)))],order='order_id asc',limit=1)
        if len(first_sales)>0:
            sale_nbr_days = (date.today() - fields.Date.from_string(first_sales.order_id.date_order)).days
            res = self.env['sale.report'].read_group([('product_id','=',self.id),('date_confirm','>',fields.Date.to_string(date.today() - timedelta(days=365)))],['product_id','product_uom_qty'],['product_id'])
            if len(res)>0:
                self.consumtion_per_day = res[0]['product_uom_qty'] / sale_nbr_days
                self.orderpoint_computed =  self.consumtion_per_day * delay
                self.virtual_available_days = self.virtual_available / self.consumtion_per_day
    consumtion_per_day = fields.Float(compute="_sales_per_day")
    orderpoint_computed = fields.Float(compute="_sales_per_day")
    virtual_available_days = fields.Float(compute="_sales_per_day")
    @api.one
    @api.depends('seller_ids','seller_ids.delay','produce_delay')
    def _instock_percent(self):
        op = self.orderpoint_computed or 1.0
        self.instock_percent = self.virtual_available / op * 100
    instock_percent = fields.Integer(compute="_instock_percent",store=True)
    

class stock_warehouse_orderpoint(models.Model):
    _inherit = "stock.warehouse.orderpoint"

    orderpoint_computed = fields.Float(related="product_id.orderpoint_computed")
    