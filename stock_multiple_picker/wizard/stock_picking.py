# -*- coding: utf-8 -*-
##############################################################################
#
# OpenERP, Open Source Management Solution, third party addon
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

import openerp.exceptions
from openerp.exceptions import except_orm, Warning, RedirectWarning,MissingError
from openerp import models, fields, api, _

import logging
_logger = logging.getLogger(__name__)


class stock_picking_wizard(models.TransientModel):
    _name = 'stock.picking.multiple'
    _description = 'Set Picking Employees'
    
    def _default_employee_id(self):
        hr = self.env['hr.employee'].search([('user_id', '=', self.env.uid if self.env.uid else '')])
        return [(6,0,[hr[0].id])] if len(hr) > 0 else None
    
    def _default_picking_id(self):
        picking_id = self._context.get('active_id')
        if not picking_id:
            picking_id = self._context.get('active_ids') and self._context.get('active_ids')[0]
        return picking_id

    def _default_picking_ids(self):
        picking_ids = self._context.get('active_ids')
        return picking_ids

    employee_ids = fields.Many2many(comodel_name='hr.employee', string='Picking Employee', default=_default_employee_id, required=False)
    picking_ids = fields.Many2many(comodel_name='stock.picking', string='Stock Picking', default=_default_picking_ids, required=True)
    force = fields.Boolean('Replace Current Picking Employee')
    no_print = fields.Boolean(string="No Print", help="This is for not print out")

    @api.multi
    def set_picking_employee(self):

        if self.force or not self.picking_ids.mapped('employee_id'):
            for picking in self.picking_ids:
                if len(self.employee_ids) > 0:
                    picking.employee_id = self.employee_ids[0]
                    picking.employee_ids = self.employee_ids
                else:
                    picking.employee_id = None
                    picking.employee_ids = None
            last_move = None
            picker_count = len(self.employee_ids)
            i = 0
            for move in self.picking_ids.mapped('move_lines').sorted(lambda m: m.product_id):
                if last_move and last_move.product_id == move.product_id:
                    move.employee_id = last_move.employee_id
                else:
                    if len(self.employee_ids) > 0:
                        move.employee_id = self.employee_ids[i]
                        i += 1
                        if i == picker_count:
                            i = 0
                    else:
                        move.employee_id = None
                last_move = move
            if not self.no_print:
                self.env['report'].print_document(self.picking_ids, 'stock_multiple_picker.picking_operations_document')
            #self.env['report'].print_document(invoice, default_report)
            return {'type': 'ir.actions.act_window_close'}
            # return self.env['report'].get_action(self.picking_ids, 'stock_multiple_picker.picking_operations_document')
        else:
            raise Warning(_('Picking Employee is already set.'))

            
    @api.multi
    def batch_picking(self):

        """§
        We use stock_moves as our "docs" variable in the xml. For sorting reasons.
        With picking_id we reach the parent (stock.picking).

        """

        if self.force or not self.picking_ids.mapped('employee_id'):
            self.picking_ids.enumerate_picking_boxes()
            stock_moves = self.env['stock.move'].search([('picking_id', 'in', self.picking_ids.ids)])
            self.set_picking_employee()

            return self.env['report'].get_action(stock_moves, 'stock_multiple_picker.picking_operations_group_document')
        else:
            raise Warning(_('Picking Employee is already set.'))
