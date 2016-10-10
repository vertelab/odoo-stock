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

class stock_picking_report(models.Model):
    _name = "stock_picking.report"
    _description = "Stock Picking Statistics"
    _auto = False
    _rec_name = 'date'



    date = fields.Datetime(string='Date Created', readonly=True)
    date_done = fields.Datetime(string='Date Done', readonly=True)
    product_id = fields.Many2one(comodel_name='product.product',string='Product', readonly=True)
    product_uom = fields.Many2one(comodel_name='product.uom', string='Unit of Measure', readonly=True)
    product_uom_qty = fields.Float(string='# of Qty', readonly=True)

    group_id = fields.Many2one(comodel_name='procurement.group', string='Procurement Group', readonly=True)
    picking_type_id = fields.Many2one(comodel_name='stock.picking.type', string='Picking Type', readonly=True)
    move_type = fields.Selection([('direct', 'Partial'), ('one', 'All at once')],string="Move Type", readonly=True)
    location_id = fields.Many2one(comodel_name='stock.location', string='Location', readonly=True)
    location_dest_id = fields.Many2one(comodel_name='stock.location', string='Destination', readonly=True)
        
    partner_id = fields.Many2one(comodel_name='res.partner', string='Partner', readonly=True)
    company_id = fields.Many2one(comodel_name='res.company', string='Company', readonly=True)
    delay = fields.Float(string='Commitment Delay', digits=(16,2), readonly=True)
    leadtime = fields.Float(string='Leadtime', digits=(16,2), readonly=True)
    categ_id = fields.Many2one(comodel_name='product.category',string='Category of Product', readonly=True)
    nbr_lines = fields.Integer(string='# of Lines', readonly=True)
    nbr_sku = fields.Integer(string='# of SKU', readonly=True)
    state = fields.Selection([
            ('cancel', 'Cancelled'),
            ('draft', 'Draft'),
            ('confirmed', 'Confirmed'),
            ('exception', 'Exception'),
            ('done', 'Done')], 'Order Status', readonly=True)
    
    _order = 'date desc'

    def _select(self):
        select_str = """
             SELECT min(l.id) as id,
                    l.product_id as product_id,
                    s.group_id as group_id,
                    t.uom_id as product_uom,
                    sum(l.product_qty / u.factor * u2.factor) as product_uom_qty,
                    sum(l.qty_done) as nbr_sku,
                    count(*) as nbr_lines,
                    s.date as date,
                    s.date_done as date_done,
                    s.partner_id as partner_id,
                    s.company_id as company_id,
                    extract(epoch from avg(date_trunc('day',s.date_done)-date_trunc('day',s.min_date)))/(24*60*60)::decimal(16,2) as delay,
                    extract(epoch from avg(date_trunc('day',s.date_done)-date_trunc('day',s.date)))/(24*60*60)::decimal(16,2) as leadtime,
                    s.state,
                    t.categ_id as categ_id,
                    l.location_id as location_id,
                    l.location_dest_id as location_dest_id,
                    s.picking_type_id as picking_type_id,
                    s.move_type as move_type
        """
        return select_str

    def _from(self):
        from_str = """
                stock_pack_operation l
                      join stock_picking s on (l.picking_id=s.id)
                        left join product_product p on (l.product_id=p.id)
                            left join product_template t on (p.product_tmpl_id=t.id)
                    left join product_uom u on (u.id=l.product_uom_id)
                    left join product_uom u2 on (u2.id=t.uom_id)
                    left join stock_picking_type pt on (s.picking_type_id = pt.id)
                    left join stock_location location on (l.location_id = location.id)
                    left join stock_location dest on (l.location_dest_id = dest.id)
                    left join procurement_group on (s.group_id = procurement_group.id)
        """
        return from_str

    def _group_by(self):
        group_by_str = """
            GROUP BY l.product_id,
                    l.picking_id,
                    s.group_id,
                    t.uom_id,
                    t.categ_id,
                    s.date,
                    s.date_done,
                    s.partner_id,
                    s.company_id,
                    l.location_id,
                    l.location_dest_id,
                    s.state,
                    s.picking_type_id,
                    s.move_type,
                    t.categ_id
        """
        return group_by_str

    def init(self, cr):
        # self._table = sale_report
        tools.drop_view_if_exists(cr, self._table)
        cr.execute("""CREATE or REPLACE VIEW %s as (
            %s
            FROM ( %s )
            %s
            )""" % (self._table, self._select(), self._from(), self._group_by()))

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: