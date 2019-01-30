# -*- coding: utf-8 -*-
##############################################################################
#
# Odoo, Open Source Management Solution, third party addon
# Copyright (C) 2016- Vertel AB (<http://vertel.se>).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import tools
import openerp.addons.decimal_precision as dp
import pytz
import dateutil.relativedelta
import datetime
from datetime import datetime, timedelta

import openerp.exceptions
from openerp import models, fields, api, _

import logging
_logger = logging.getLogger(__name__)

"""

Vi behöver kunna mäta hur vi presterar vad gäller plockning och emballering. Och vi vill mäta tiden det tar att plocka en order resp emballera den samma.

Så här tänker vi loggningen:

Plocktid:

När man sätter plockare på en order så sätts en tidsstäpel med datum och tid. När plockningen är klar skall plockaren markera order som plockad. Detta skall sätta en tidstämpel när detta inträffar. På så sätt kan vi sedan redovisa per order hur lång plocktid vi haft. Denna information vill vi sedan bygga en rapport för under Rapporter i BI.

Emballeringstid:

När det på en order sätts kontrollerad av så sätts en tidsstämpel (nu börjar emballeringstiden). När användaren klickar på skapa faktura på ordern/plockningen så skall en tidstämpel sättas för detta. Tiden för emballering är från att kontrollerat av sätts till dess att man klickar på skapa faktura. Denna information vill vi sedan bygga en rapport för under Rapporter i BI.

Rapport i BI:

Vi vill kunna se:

Tid per plocking. Snittid per plockare, dag, månad, år.

Tid per emballering. Snittid per kontrollerare, dag, månad, år.

Tid per order. Snittid vi lägger per order. Tiden för en order är från tidsstämpeln när vi sätter plockar till tidstämpeln då skapa faktura sker. Snitt tid per dag, månad, år.

picking_time
wrap_time

Plockning per rad?

"""
from datetime import datetime, timedelta

class stock_picking(models.Model):
    _inherit = 'stock.picking'

    picking_starts = fields.Datetime(string="Picking Starts")
    picking_stops = fields.Datetime(string="Picking Stops")
    wraping_starts = fields.Datetime(string="Wraping Starts",compute="_wraping_starts",stored=True)
    wraping_stops = fields.Datetime(string="Wraping Stops")

    @api.one
    @api.depends('qc_id',)
    def _wraping_starts(self):
        self.wraping_starts = fields.Datetime.now()

    @api.one
    def stop_picking(self):
        self.picking_stops = fields.Datetime.now()

    @api.model
    def get_wrapping_time_date(self, date):
        wrap_tot = 0.0
        wrap_nbr = 0
        for picking in self.env['stock.picking'].search([('date', '>=', '%s 00:00:00' %date), ('date', '<=', '%s 23:59:59' %date)]):
            wrap_tot = picking.wraping_stops.from_string() - picking.wraping_starts.from_string()
            wrap_nbr += 1
        return wrap_tot / wrap_nbr if wrap_nbr > 0 else 1

    @api.model
    def get_wrapping_time_lastweek(self):
        today = fields.Date.today()
        days = []
        times = []
        for day in range(-1,-8,-1):
            this_day = fields.Date.from_string(today) + timedelta(days=day)
            if this_day.weekday() in range(0,5):
                days.append(this_day.strftime('%A'))
                times.append(self.get_wrapping_time_date(fields.Date.to_string(this_day)))
        days.reverse()
        times.reverse()
        return days, times

    @api.model
    def get_picking_time_date(self, date):
        pick_tot = 0.0
        pick_nbr = 0
        for picking in self.env['stock.picking'].search([('date', '>=', '%s 00:00:00' %date), ('date', '<=', '%s 23:59:59' %date)]):
            pick_tot = picking.picking_stops.from_string() - picking.picking_starts.from_string()
            pick_nbr += 1
        return pick_tot / pick_nbr if pick_nbr > 0 else 1

    @api.model
    def get_picking_time_lastweek(self):
        today = fields.Date.today()
        days = []
        times = []
        for day in range(-1,-8,-1):
            this_day = fields.Date.from_string(today) + timedelta(days=day)
            if this_day.weekday() in range(0,5):
                days.append(this_day.strftime('%A'))
                times.append(self.get_picking_time_date(fields.Date.to_string(this_day)))
        days.reverse()
        times.reverse()
        return days, times

    @api.model
    def get_order_time_date(self, date):
        pick_tot = 0.0
        pick_nbr = 0
        for picking in self.env['stock.picking'].search([('date', '>=', '%s 00:00:00' %date), ('date', '<=', '%s 23:59:59' %date)]):
            pick_tot = picking.wrapping_stops.from_string() - picking.picking_starts.from_string()
            pick_nbr += 1
        return pick_tot / pick_nbr if pick_nbr > 0 else 1

    @api.model
    def get_order_time_lastweek(self):
        today = fields.Date.today()
        days = []
        times = []
        for day in range(-1,-8,-1):
            this_day = fields.Date.from_string(today) + timedelta(days=day)
            if this_day.weekday() in range(0,5):
                days.append(this_day.strftime('%A'))
                times.append(self.get_order_time_date(fields.Date.to_string(this_day)))
        days.reverse()
        times.reverse()
        return days, times

class stock_picking_wizard(models.TransientModel):
    _inherit = 'stock.picking.multiple'

    @api.multi
    def set_picking_employee(self):
        super(stock_picking_wizard, self).set_picking_employee()
        self.picking_id.picking_starts = fields.Datetime.now()

class stock_invoice_onshipping(models.TransientModel):
    _inherit = 'stock.invoice.onshipping'

    @api.multi
    def open_invoice():
        self.wraping_stops = fields.Datetime.now()
        return super(stock_invoice_onshipping, self).open_invoice()


class stock_picking_report(models.Model):
    _inherit = "stock_picking.report"

    employee_id =  fields.Many2one("hr.employee", "Picking Employee", readonly=True)
    legacy_employee_id =  fields.Many2one("hr.employee", "Picking Employee (legacy)", readonly=True)
    qc_id =  fields.Many2one("hr.employee", "Controlled by", readonly=True)

    picking_time = fields.Float(string='Picking Time', digits=(16,2), readonly=True)
    wraping_time = fields.Float(string='Warping Time', digits=(16,2), readonly=True)
    order_time = fields.Float(string='Order Time', digits=(16,2), readonly=True)

    def _select(self):
        return  super(stock_picking_report, self)._select() + """
                    , sp.employee_id as legacy_employee_id, move.employee_id as employee_id, sp.qc_id as qc_id
                    , extract(epoch from avg(date_trunc('day',sp.picking_stops)-date_trunc('day',sp.picking_starts)))/(24*60*60)::decimal(16,2) as picking_time
                    , extract(epoch from avg(date_trunc('day',sp.wraping_stops)-date_trunc('day',sp.wraping_starts)))/(24*60*60)::decimal(16,2) as wraping_time
                    , extract(epoch from avg(date_trunc('day',sp.wraping_stops)-date_trunc('day',sp.picking_starts)))/(24*60*60)::decimal(16,2) as order_time"""


    def _group_by(self):
        return super(stock_picking_report, self)._group_by() + ", sp.employee_id, move.employee_id, sp.qc_id"

    def _from(self):
        return super(stock_picking_report, self)._from() + """left join hr_employee on (sp.employee_id = hr_employee.id)
        left join hr_employee qc on (sp.qc_id = qc.id)
        left join stock_move move on (sp.id = move.picking_id)
        """


    def _read_group_process_groupby(self, gb, query, context):
        """
            Helper method to collect important information about groupbys: raw
            field name, type, time information, qualified name, ...
        """
        split = gb.split(':')
        field_type = self._fields[split[0]].type
        gb_function = split[1] if len(split) == 2 else None
        temporal = field_type in ('date', 'datetime')
        tz_convert = field_type == 'datetime' and context.get('tz') in pytz.all_timezones
        qualified_field = self._inherits_join_calc(self._table, split[0], query)
        if temporal:
            display_formats = {
                # Careful with week/year formats:
                #  - yyyy (lower) must always be used, *except* for week+year formats
                #  - YYYY (upper) must always be used for week+year format
                #         e.g. 2006-01-01 is W52 2005 in some locales (de_DE),
                #                         and W1 2006 for others
                #
                # Mixing both formats, e.g. 'MMM YYYY' would yield wrong results,
                # such as 2006-01-01 being formatted as "January 2005" in some locales.
                # Cfr: http://babel.pocoo.org/docs/dates/#date-fields
                'hour': 'HH dd MMM yyyy', # yyyy = normal year
                'day': 'dd MMM yyyy', # yyyy = normal year
                'week': "'W'w YYYY",  # w YYYY = ISO week-year
                'month': 'MMMM yyyy',
                'quarter': 'QQQ yyyy',
                'year': 'yyyy',
            }
            time_intervals = {
                'hour': dateutil.relativedelta.relativedelta(hours=1),
                'day': dateutil.relativedelta.relativedelta(days=1),
                'week': datetime.timedelta(days=7),
                'month': dateutil.relativedelta.relativedelta(months=1),
                'quarter': dateutil.relativedelta.relativedelta(months=3),
                'year': dateutil.relativedelta.relativedelta(years=1)
            }
            if tz_convert:
                qualified_field = "timezone('%s', timezone('UTC',%s))" % (context.get('tz', 'UTC'), qualified_field)
            qualified_field = "date_trunc('%s', %s)" % (gb_function or 'month', qualified_field)
        if field_type == 'boolean':
            qualified_field = "coalesce(%s,false)" % qualified_field
        return {
            'field': split[0],
            'groupby': gb,
            'type': field_type,
            'display_format': display_formats[gb_function or 'month'] if temporal else None,
            'interval': time_intervals[gb_function or 'month'] if temporal else None,
            'tz_convert': tz_convert,
            'qualified_field': qualified_field
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
