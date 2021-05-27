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
from odoo import models, fields, api, _
from datetime import datetime, timedelta, date
from odoo.tools import safe_eval as eval
import pytz
import traceback

import logging
_logger = logging.getLogger(__name__)

#~ 20,00       sales_count
#~ 1,981039     so_line_ids
#~ 1,022867     sale_order_lines
#~ 0,390086     code

class product_template(models.Model):
    _inherit = 'product.template'
    
    sales_count = fields.Integer('# Sales', compute='_get_sales_count', store=True, readonly=True, default=0)  # Initially defined in sale-module
    consumption_per_day = fields.Float('Consumption per Day', default=0)
    consumption_per_month = fields.Float(string='Consumption per Month', default=0,help="Number of items that is consumed per month")
    consumption_per_year = fields.Float(string='Consumption per Year', default=0,help="Number of items that is consumed per year")
    orderpoint_computed = fields.Float('Orderpoint', default=0)
    virtual_available_days = fields.Float('Virtual Available Days', default=0)
    instock_percent = fields.Integer('Instock Percent', default=0)
    last_sales_count = fields.Datetime('Last Sales Compute', help="The last point in time when # Sales, Consumption per Day, Orderpoint, Virtual Available Days, and Instock Percent were computed.")
    earliest_sales_count = fields.Datetime('Earliest Sales Compute', help="Don't try to recompute before this time. Set when compute fails for a product.")
    virtual_available_delay = fields.Float('Delay', default=0,help="Number of days before refill of stock")
    virtual_available_netto = fields.Float('Virtual available netto', default=0,help="virtual available minus incoming")
    is_out_of_stock = fields.Boolean(string='Is out of stock',help='Check this box to ensure not to sell this product due to stock outage (instock_percent = 0)')
    
    def _consumption_per_day(self, location_ids=None):
        _logger.warn('Computing _consumption_per_day for product.template %s, %s' % (self.id, self.name))
        location_ids = location_ids or eval(self.env['ir.config_parameter'].get_param('calc_orderpoint.location_ids', '[]'))
        self.product_variant_ids._consumption_per_day(location_ids)
        variant_count = len(self.product_variant_ids) or 1
        self.sales_count = sum([p.sales_count for p in self.product_variant_ids])
        self.consumption_per_day = sum([p.consumption_per_day for p in self.product_variant_ids])
        self.consumption_per_month = sum([p.consumption_per_month for p in self.product_variant_ids])
        self.consumption_per_year = sum([p.consumption_per_year for p in self.product_variant_ids])
        delay = min([p.virtual_available_delay for p in self.product_variant_ids])
        self.virtual_available_delay = delay
        self.virtual_available_netto = self.virtual_available - self.incoming_qty
        #raise Warning(self.virtual_available, self.incoming_qty)
        self.orderpoint_computed = self.consumption_per_day * delay
        self.virtual_available_days = 0 if self.virtual_available_netto <=0 else self.virtual_available_netto/ (self.consumption_per_day or 1.0)
        
        if self.is_out_of_stock or self.virtual_available_netto <= 0:
            self.instock_percent = 0
        elif self.env.ref('stock.route_warehouse0_mto') in self.route_ids: # Make To Order are always in stock
            self.instock_percent = 100
        elif self.type == 'consu': # Consumables are always in stock
            self.instock_percent = 100
        else:
            self.instock_percent = self.sudo().virtual_available_days / (self.virtual_available_delay or 1.0) * 100
        self.last_sales_count = fields.Datetime.now()
        # update memcached_time to tell memcached to recache page.
        self.memcached_time = fields.Datetime.now()

    def _get_sales_count(self):
        pass

    def _sales_count(self):
        pass

    @api.model
    def compute_consumption_per_day(self):
        """Compute sales_count and its dependant fields. This can be a
        very taxing computation if there are many sale order lines.
        Split into many smaller batches to alleviate the problem. Default
        settings are made for 5 minute interval cron jobs. Schedule can
        be configured with the calc_orderpoint.schedule parameter.
        """
        start = datetime.now()
        tz = pytz.timezone(self.env.user.tz)
        dt = pytz.utc.localize(start).astimezone(tz)
        schedule = self.env['ir.config_parameter'].get_param('calc_orderpoint.schedule', '0 6').split()
        run = False
        for begin, end in zip(schedule[::2], schedule[1::2]):
            if dt.hour >= int(begin) and dt.hour < int(end):
                run = True
                break
        if run:
            now = fields.Datetime.now()
            location_ids = eval(self.env['ir.config_parameter'].get_param('calc_orderpoint.location_ids', '[]'))
            limit = timedelta(minutes=float(self.env['ir.config_parameter'].get_param('calc_orderpoint.time_limit', '4')))
            _logger.warn('Starting compute_consumption_per_day.')
            products = self.env['product.template'].search(
                [
                    '|',
                        ('product_variant_ids.sale_ok', '=', True),
                        ('sale_ok', '=', True),
                    ('last_sales_count', '=', False),
                    '|',
                        ('earliest_sales_count', '=', False),
                        ('earliest_sales_count', '<', now)
                ],
                limit=int(self.env['ir.config_parameter'].get_param(
                    'calc_orderpoint.product_limit', '30')))
            if not products:
                products = self.env['product.template'].search(
                    [
                        '|',
                            ('product_variant_ids.sale_ok', '=', True),
                            ('sale_ok', '=', True),
                        '|',
                            ('earliest_sales_count', '=', False),
                            ('earliest_sales_count', '<', now)
                    ],
                    order='last_sales_count asc',
                    limit=int(self.env['ir.config_parameter'].get_param(
                        'calc_orderpoint.product_limit', '30')))
            _logger.warn('Computing compute_consumption_per_day for the following products: %s' % products)
            for product in products:
                try:
                    product._consumption_per_day()
                    product.write({
                        'last_sales_count': fields.Datetime.now(),
                        'earliest_sales_count': False,
                    })
                    if (datetime.now() - start) > limit:
                        break
                except:
                    tb = traceback.format_exc()
                    tomorrow = fields.Datetime.to_string(fields.Datetime.from_string(fields.Datetime.now()) + timedelta(1))
                    subject = 'compute_consumption_per_day failed to compute %s (%s)' % (product.display_name, product.id)
                    body = 'Earliest recompute attempt set to %s.\n\n%s' % (tomorrow, tb)
                    _logger.warn('%s. %s' % (subject, body))
                    product.earliest_sales_count = tomorrow
                    product.message_post(body=body.replace('\n', '<br/>'), subject=subject, type='notification')
                    
            _logger.warn('Finished compute_consumption_per_day.')

    def calc_orderpoint(self):
        self._consumption_per_day()

class product_product(models.Model):
    _inherit = 'product.product'

    def _consumption_per_day(self, location_ids=None):
        _logger.warn('Computing _consumption_per_day for product.product %s, %s' % (self.id, self.name))
        location_ids = location_ids or []
        if self.env.context.get('location_ids'):
            locations = self.env['stock.picking.type'].browse()
            for loc in self.env['stock.picking.type'].browse(location_ids): # list of stock.location
                locations |= loc.default_location_dest_id
        else:
            locations = self.env.ref('stock.picking_type_out').default_location_dest_id
            locations |= self.env.ref('point_of_sale.picking_type_posout').default_location_dest_id
            locations |= self.env.ref('stock.location_production')
        stocks_year = self.env['stock.move'].search_read(
            [
                ('product_id', '=', self.id),
                ('date', '>', fields.Date.to_string(date.today() - timedelta(days=365))),
                ('location_dest_id', 'in', locations.mapped('id'))],
            ['product_qty', 'date'],
            order='date asc')
        stocks_month = self.env['stock.move'].search_read(
            [
                ('product_id', '=', self.id),
                ('date', '>', fields.Date.to_string(date.today() - timedelta(days=31))),
                ('location_dest_id', 'in', locations.mapped('id'))],
            ['product_qty', 'date'],
            order='date asc')
        if stocks_year:
            stock_nbr_days_year = (date.today() - fields.Date.from_string(stocks_year[0]['date'])).days
            year_count = sum([r['product_qty'] for r in stocks_year])
            self.sales_count = year_count
            self.consumption_per_year = year_count / (stock_nbr_days_year or 1) * 365
            if stocks_month:
                stock_nbr_days_month = 31
                month_count = sum([r['product_qty'] for r in stocks_month])
                self.consumption_per_month = month_count / stock_nbr_days_month * 30.5
                self.consumption_per_day = month_count / stock_nbr_days_month
            else:
                self.consumption_per_month = self.consumption_per_year / 12
                self.consumption_per_day = self.consumption_per_year / 365
        else:
            self.consumption_per_day = 0
            self.consumption_per_month = 0
            self.consumption_per_year = 0
            self.sales_count = 0
        if min(self.seller_ids.mapped('delay') or [0.0])>0.0:
            delay = min(self.seller_ids.mapped('delay')) + (self.company_id.po_lead if self.company_id else self.env.user.company_id.po_lead)
        else:
            delay = self.produce_delay + (self.company_id.manufacturing_lead if self.company_id else self.env.user.company_id.manufacturing_lead)
        self.virtual_available_delay = delay
        self.orderpoint_computed =  self.consumption_per_day * delay
        self.virtual_available_netto = self.virtual_available - self.incoming_qty
        self.virtual_available_days = self.virtual_available_netto / (self.consumption_per_day or 1.0)

        if self.is_out_of_stock:
            self.instock_percent = 0
        elif self.env.ref('stock.route_warehouse0_mto') in self.route_ids: # Make To Order are always in stock
            self.instock_percent = 100
        elif self.type == 'consu': # Consumables are always in stock
            self.instock_percent = 100
        else:
            self.instock_percent = self.sudo().virtual_available / (self.orderpoint_computed or 1.0) * 100
        self.last_sales_count = fields.Datetime.now()
        # update memcached_time to tell memcached to recache page.
        self.memcached_time = fields.Datetime.now()

    def _get_sales_count(self):
        pass

    sales_count = fields.Integer('# Sales', compute='_get_sales_count', store=True, readonly=True, default=0)  # Initially defined in sale-module
    consumption_per_day = fields.Float(string='Consumption per Day', default=0, help="Number of items that is consumed per day")
    consumption_per_month = fields.Float(string='Consumption per Month', default=0, help="Number of items that is consumed per month")
    consumption_per_year = fields.Float(string='Consumption per Year', default=0, help="Number of items that is consumed per year")
    orderpoint_computed = fields.Float('Orderpoint', default=0, help="Delay * Consumption per day, delay is sellers delay or produce delay")
    virtual_available_days = fields.Float('Virtual Available Days', default=0, help="Number of days that Forcast Quantity will last with this Consumtion per day")
    virtual_available_delay = fields.Float('Delay', default=0, help="Number of days before refill of stock")
    virtual_available_netto = fields.Float('Virtual available netto', default=0, help="virtual available minus incoming")
    instock_percent = fields.Integer('Instock Percent', default=0 ,help="Forcast Quantity / Computed Order point * 100")
    is_out_of_stock = fields.Boolean(string='Is out of stock', help='Check this box to ensure not to sell this product due to stock outage (instock_percent = 0)')

    #~ sale_order_lines = fields.One2many(comodel_name='sale.order.line', inverse_name="product_id")  # performance hog, do we need it?

    def calc_orderpoint(self):
        self._consumption_per_day()


class stock_warehouse_orderpoint(models.Model):
    _inherit = "stock.warehouse.orderpoint"

    orderpoint_computed = fields.Float(related="product_id.orderpoint_computed")

