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
from datetime import datetime, timedelta, date
import pytz
import logging
_logger = logging.getLogger(__name__)

#~ 20,00       sales_count
#~ 1,981039     so_line_ids
#~ 1,022867     sale_order_lines
#~ 0,390086     code

class product_template(models.Model):
    _inherit = 'product.template'

    @api.one
    def _consumption_per_day(self):
        _logger.warn('Computing _consumption_per_day for product.template %s, %s' % (self.id, self.name))
        self.product_variant_ids._consumption_per_day()
        locations = self.env.ref('stock.picking_type_out').default_location_dest_id
        locations |= self.env.ref('point_of_sale.picking_type_posout').default_location_dest_id
        locations |= self.env.ref('stock.location_production')
        stocks_year = self.env['stock.move'].search_read(
            [('product_id', 'in', self.product_variant_ids.mapped('id')),
            ('date', '>', fields.Date.to_string(date.today() - timedelta(days=365))),
            ('location_dest_id', 'in', locations.mapped('id'))],
            ['product_uom_qty', 'date'], order='date asc')
        stocks_month = self.env['stock.move'].search_read(
            [('product_id', '=', self.product_variant_ids.mapped('id')),
            ('date', '>', fields.Date.to_string(date.today() - timedelta(days=31))),
            ('location_dest_id', 'in', locations.mapped('id'))],
            ['product_uom_qty', 'date'], order='date asc')
        if len(stocks_year) > 0:
            stock_nbr_days_year = (date.today() - fields.Date.from_string(stocks_year[0]['date'])).days
            year_count = sum([r['product_uom_qty'] for r in stocks_year])
            self.sales_count = year_count
            self.consumption_per_year = year_count / stock_nbr_days_year * 365
            if len(stocks_month) > 0:
                stock_nbr_days_month = (date.today() - fields.Date.from_string(stocks_month[0]['date'])).days
                month_count = sum([r['product_uom_qty'] for r in stocks_month])
                self.consumption_per_month = month_count / stock_nbr_days_month * 30.5
                self.consumption_per_day = month_count / stock_nbr_days_month
            else:
                self.consumption_per_month = self.consumption_per_year / 30.5
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
        self.orderpoint_computed = self.consumption_per_day * delay
        self.virtual_available_days = self.virtual_available / (self.consumption_per_day or 1.0)
        if self.is_out_of_stock:
            self.instock_percent = 0
        elif self.env.ref('stock.route_warehouse0_mto') in self.route_ids: # Make To Order are always in stock
            self.instock_percent = 100
        elif self.type == 'consu': # Consumables are always in stock
            self.instock_percent = 100
        else:
            self.instock_percent = self.sudo().virtual_available_days / (self.virtual_available_delay or 1.0) * 100
        self.last_sales_count = fields.Datetime.now()

    def _get_sales_count(self):
        pass

    def _sales_count(self, cr, uid, ids, field_name, arg, context=None):
        pass

    sales_count = fields.Integer('# Sales', compute='_get_sales_count', store=True, readonly=True, default=0)  # Initially defined in sale-module
    consumption_per_day = fields.Float('Consumption per Day', default=0)
    consumption_per_month = fields.Float(string='Consumption per Month', default=0,help="Number of items that is consumed per month")
    consumption_per_year = fields.Float(string='Consumption per Year', default=0,help="Number of items that is consumed per year")
    orderpoint_computed = fields.Float('Orderpoint', default=0)
    virtual_available_days = fields.Float('Virtual Available Days', default=0)
    instock_percent = fields.Integer('Instock Percent', default=0)
    last_sales_count = fields.Datetime('Last Sales Compute', help="The last point in time when # Sales, Consumption per Day, Orderpoint, Virtual Available Days, and Instock Percent were computed.")
    virtual_available_delay = fields.Float('Delay', default=0,help="Number of days before refill of stock")
    is_out_of_stock = fields.Boolean(string='Is out of stock',help='Check this box to ensure not to sell this product due to stock outage (instock_percent = 0)')

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
            limit = timedelta(minutes=float(self.env['ir.config_parameter'].get_param('calc_orderpoint.time_limit', '4')))
            _logger.warn('Starting compute_consumption_per_day.')
            products = self.env['product.template'].search(
                ['|', ('product_variant_ids.sale_ok', '=', True),
                    ('sale_ok', '=', True),
                    ('last_sales_count', '=', False)],
                limit=int(self.env['ir.config_parameter'].get_param(
                    'calc_orderpoint.product_limit', '30')))
            if not products:
                products = self.env['product.template'].search(
                    ['|', ('product_variant_ids.sale_ok', '=', True),
                        ('sale_ok', '=', True)],
                    order='last_sales_count asc',
                    limit=int(self.env['ir.config_parameter'].get_param(
                        'calc_orderpoint.product_limit', '30')))
            _logger.warn('Computing compute_consumption_per_day for the following products: %s' % products)
            for product in products:
                product._consumption_per_day()
                dt = fields.Datetime.now()
                product.write({'last_sales_count': fields.Datetime.now()})
                if (datetime.now() - start) > limit:
                    break
            _logger.warn('Finished compute_consumption_per_day.')

    @api.one
    def calc_orderpoint(self):
        self._consumption_per_day()

class product_product(models.Model):
    _inherit = 'product.product'

    @api.one
    def _consumption_per_day(self):
        _logger.warn('Computing _consumption_per_day for product.product %s, %s' % (self.id, self.name))
        locations = self.env.ref('stock.picking_type_out').default_location_dest_id
        locations |= self.env.ref('point_of_sale.picking_type_posout').default_location_dest_id
        locations |= self.env.ref('stock.location_production')
        stocks_year = self.env['stock.move'].search_read(
            [('product_id', '=', self.id),
            ('date', '>', fields.Date.to_string(date.today() - timedelta(days=365))),
            ('location_dest_id', 'in', locations.mapped('id'))],
            ['product_uom_qty', 'date'], order='date asc')
        stocks_month = self.env['stock.move'].search_read(
            [('product_id', '=', self.id),
            ('date', '>', fields.Date.to_string(date.today() - timedelta(days=31))),
            ('location_dest_id', 'in', locations.mapped('id'))],
            ['product_uom_qty', 'date'], order='date asc')
        if len(stocks_year) > 0:
            stock_nbr_days_year = (date.today() - fields.Date.from_string(stocks_year[0]['date'])).days
            year_count = sum([r['product_uom_qty'] for r in stocks_year])
            self.sales_count = year_count
            self.consumption_per_year = year_count / stock_nbr_days_year * 365
            if len(stocks_month) > 0:
                stock_nbr_days_month = (date.today() - fields.Date.from_string(stocks_month[0]['date'])).days
                month_count = sum([r['product_uom_qty'] for r in stocks_month])
                self.consumption_per_month = month_count / stock_nbr_days_month * 30.5
                self.consumption_per_day = month_count / stock_nbr_days_month
            else:
                self.consumption_per_month = self.consumption_per_year / 30.5
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
        self.virtual_available_days = self.virtual_available / (self.consumption_per_day or 1.0)

        if self.is_out_of_stock:
            self.instock_percent = 0
        elif self.env.ref('stock.route_warehouse0_mto') in self.route_ids: # Make To Order are always in stock
            self.instock_percent = 100
        elif self.type == 'consu': # Consumables are always in stock
            self.instock_percent = 100
        else:
            self.instock_percent = self.sudo().virtual_available / (self.orderpoint_computed or 1.0) * 100
        self.last_sales_count = fields.Datetime.now()


    def _get_sales_count(self):
        pass

    sales_count = fields.Integer('# Sales', compute='_get_sales_count', store=True, readonly=True, default=0)  # Initially defined in sale-module
    consumption_per_day = fields.Float(string='Consumption per Day', default=0,help="Number of items that is consumed per day")
    consumption_per_month = fields.Float(string='Consumption per Month', default=0,help="Number of items that is consumed per month")
    consumption_per_year = fields.Float(string='Consumption per Year', default=0,help="Number of items that is consumed per year")
    orderpoint_computed = fields.Float('Orderpoint', default=0,help="Delay * Consumption per day, delay is sellers delay or produce delay")
    virtual_available_days = fields.Float('Virtual Available Days', default=0,help="Number of days that Forcast Quantity will last with this Consumtion per day")
    virtual_available_delay = fields.Float('Delay', default=0,help="Number of days before refill of stock")
    instock_percent = fields.Integer('Instock Percent', default=0,help="Forcast Quantity / Computed Order point * 100")
    is_out_of_stock = fields.Boolean(string='Is out of stock',help='Check this box to ensure not to sell this product due to stock outage (instock_percent = 0)')


    #~ sale_order_lines = fields.One2many(comodel_name='sale.order.line', inverse_name="product_id")  # performance hog, do we need it?

    @api.one
    def calc_orderpoint(self):
        self._consumption_per_day()


class stock_warehouse_orderpoint(models.Model):
    _inherit = "stock.warehouse.orderpoint"

    orderpoint_computed = fields.Float(related="product_id.orderpoint_computed")

