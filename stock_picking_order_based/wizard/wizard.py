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
from odoo.exceptions import Warning
import logging
_logger = logging.getLogger(__name__)


class StockPickingOrderBasedWizard(models.TransientModel):
    _name = 'stock.picking.order.based.wizard'

    source_location_id = fields.Many2one(comodel_name='stock.location', string='Source Location Zone', required=True)
    dest_location_id = fields.Many2one(comodel_name='stock.location', string='Destination Location Zone', required=True)
    period_start = fields.Date(string='Period Start', required=True)
    period_stop = fields.Date(string='Period Stop', required=True)

    @api.multi
    def make_picking(self):
        picking_type = self.env['stock.picking.type'].search([('default_location_src_id', '=', self.source_location_id.id), ('default_location_dest_id', '=', self.dest_location_id.id)])
        if len(picking_type) == 0:
            raise Warning(_('Sorry, picking type from "%s" to "%s" is not defined.' %(self.source_location_id.name, self.dest_location_id.name)))
        orders = self.env['sale.order'].search([('confirmation_date', '>=', self.period_start + ' 00:00:00'), ('confirmation_date', '<=', self.period_stop + ' 23:59:59'), ('state', '=', 'sale')])
        move_lines_dic = {
            'name': _('Move: %s -> %s' %(self.source_location_id.name, self.dest_location_id.name)),
            'location_id': self.source_location_id.id,
            'location_dest_id': self.dest_location_id.id,
            'move_type': 'one',
            'picking_type_id': picking_type[0].id,
        }
        picking = self.env['stock.picking'].create(move_lines_dic)
        products = []
        for product in orders.mapped('order_line').mapped('product_id'):
            self.env['stock.move'].create({'product_id': product.id, 'name': product.partner_ref, 'product_uom_qty': sum(orders.mapped('order_line').with_context(pro_id=product).filtered(lambda l: l.product_id == l._context.get('pro_id')).mapped('product_uom_qty')), 'product_uom': product.uom_id.id, 'location_id': self.source_location_id.id, 'location_dest_id': self.dest_location_id.id, 'picking_id': picking.id})
        picking.action_confirm()
        picking.action_assign() # TODO: is this action necessary?
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('stock.view_picking_form').id,
            'res_id': picking.id,
            'target': 'current',
            'context': {},
        }
