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

class stock_picking(models.Model):
    _inherit = 'stock.picking'
    
    nbr_lines = fields.Integer('# lines', compute='_get_nbr_lines', store=True)
    @api.one
    @api.depends('pack_operation_ids','carrier_tracking_ref')
    def _get_nbr_lines(self):
        self.nbr_lines = len(self.pack_operation_ids)

class stock_picking_report(models.Model):
    _name = "stock_picking.report"
    _description = "Stock Picking Statistics"
    _auto = False
    _rec_name = 'date'



    date = fields.Datetime(string='Date Created', readonly=True)
    date_done = fields.Datetime(string='Date Done', readonly=True)
    #~ product_id = fields.Many2one(comodel_name='product.product',string='Product', readonly=True)
    #~ product_uom = fields.Many2one(comodel_name='product.uom', string='Unit of Measure', readonly=True)
    #~ product_uom_qty = fields.Float(string='# of Qty', readonly=True)

    group_id = fields.Many2one(comodel_name='procurement.group', string='Procurement Group', readonly=True)
    picking_id = fields.Many2one(comodel_name='stock.picking', string='Picking', readonly=True)
    picking_type_id = fields.Many2one(comodel_name='stock.picking.type', string='Picking Type', readonly=True)
    move_type = fields.Selection([('direct', 'Partial'), ('one', 'All at once')],string="Move Type", readonly=True)
    #~ location_id = fields.Many2one(comodel_name='stock.location', string='Location', readonly=True)
    #~ location_dest_id = fields.Many2one(comodel_name='stock.location', string='Destination', readonly=True)
        
    partner_id = fields.Many2one(comodel_name='res.partner', string='Partner', readonly=True)
    company_id = fields.Many2one(comodel_name='res.company', string='Company', readonly=True)
    delay = fields.Float(string='Commitment Delay', digits=(16,2), readonly=True)
    leadtime = fields.Float(string='Leadtime', digits=(16,2), readonly=True)
    #~ categ_id = fields.Many2one(comodel_name='product.category',string='Category of Product', readonly=True)
    nbr_lines = fields.Integer(string='# of Lines', readonly=True)
    nbr_group = fields.Integer(string='# of Group', readonly=True)
    nbr_pickings = fields.Integer(string='# of Pickings', readonly=True)
        
    state = fields.Selection([
                ('draft', 'Draft'),
                ('cancel', 'Cancelled'),
                ('waiting', 'Waiting Another Operation'),
                ('confirmed', 'Waiting Availability'),
                ('partially_available', 'Partially Available'),
                ('assigned', 'Ready to Transfer'),
                ('done', 'Transferred')], readonly=True)
    
    _order = 'date desc'

#~ (select count(*) from stock_pack_operation where picking_id = sp.id) as nbr_lines,

    def _select(self):
        select_str = """
             SELECT min(sp.id) as id,
                    sp.id as picking_id,
                    sp.group_id as group_id,
                    count(distinct sp.group_id) as nbr_group,
                    count(distinct sp.id) as nbr_pickings,
                    sp.nbr_lines as nbr_lines,
                    sp.date as date,
                    sp.date_done as date_done,
                    sp.partner_id as partner_id,
                    sp.company_id as company_id,
                    extract(epoch from avg(date_trunc('day',sp.date_done)-date_trunc('day',sp.min_date)))/(24*60*60)::decimal(16,2) as delay,
                    extract(epoch from avg(date_trunc('day',sp.date_done)-date_trunc('day',sp.date)))/(24*60*60)::decimal(16,2) as leadtime,
                    

                    
                    sp.state,
                    sp.picking_type_id as picking_type_id,
                    sp.move_type as move_type
        """
        return select_str

    def _from(self):
        from_str = """
                stock_picking sp
                    left join stock_picking_type pt on (sp.picking_type_id = pt.id)
                    left join procurement_group on (sp.group_id = procurement_group.id)
        """
        return from_str

    def _group_by(self):
        group_by_str = """
            GROUP BY 
                    sp.group_id,
                    sp.date,
                    sp.date_done,
                    sp.partner_id,
                    sp.company_id,
                    sp.state,
                    sp.picking_type_id,
                    sp.move_type,
                    sp.id
        """
        return group_by_str

    def init(self, cr):
        # self._table = sale_report
        #~ raise Warning("""CREATE or REPLACE VIEW %s as (
            #~ %s
            #~ FROM ( %s )
            #~ %s
            #~ )""" % (self._table, self._select(), self._from(), self._group_by()))
        tools.drop_view_if_exists(cr, self._table)
        cr.execute("""CREATE or REPLACE VIEW %s as (
            %s
            FROM ( %s )
            %s
            )""" % (self._table, self._select(), self._from(), self._group_by()))

class wizard_picking_analysis(models.TransientModel):
    _name = 'wizard.picking.analysis'
    _description = 'Wizard that opens the stock picking analysis table'

    choose_date = fields.Boolean(string='Choose a Particular Date', default=False)
    date_start = fields.Datetime(string='Date Start', required=True, default=fields.Datetime.now)
    date_stop = fields.Datetime(string='Date Stop', required=True, default=fields.Datetime.now)

    @api.v7
    def open_table(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        data = self.read(cr, uid, ids, context=context)[0]
        ctx = context.copy()
        if data['choose_date']:
            ctx['history_date'] = data['date_stop']
            ctx['search_default_group_by_product'] = True
            ctx['search_default_group_by_location'] = True
        return {
            'domain': "[('date', '<=', '%s'), ('date', '>=', '%s')]" %(data['date_stop'], data['date_start']) if data['choose_date'] else "[]",
            'name': _('Stock Picking transaktions At Date'),
            'view_type': 'form',
            'view_mode': 'graph',
            'res_model': 'stock_picking.report',
            'type': 'ir.actions.act_window',
            'context': ctx,
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
