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

from odoo import models, fields, api, _

import logging
_logger = logging.getLogger(__name__)


class stock_picking(models.Model):
    _inherit = "stock.picking"

    qc_id = fields.Many2one(string='Controlled by', comodel_name='hr.employee')
    employee_id = fields.Many2one(string='Employee', comodel_name='hr.employee')
    employee_ids = fields.Many2many(string="Pickers", comodel_name="hr.employee", compute='_employee_ids',
                                    search='_search_employee_ids')
    box_label = fields.Char(string="Box Label")

    def _employee_ids(self):
        self.employee_ids = [(6, 0, self.move_lines.mapped('employee_id.id'))]

    @api.model
    def _search_employee_ids(self, operator, value):
        _logger.warn('%s %s' % (operator, value))
        return [('move_lines.employee_id', operator, value)]

    def print_picking_with_location(self):
        if len(self[0].employee_ids) > 0:
            return self.env['report'].get_action(self, 'stock_multiple_picker.picking_operations_document')
        else:
            return {'name': 'Set Picking Employee', 'res_model': 'stock.picking.multiple', 'view_model': 'form',
                    'view_mode': 'form', 'target': 'new', 'type': 'ir.actions.act_window'}
        
    def print_picking_with_location2(self):
        if len(self[0].employee_ids) > 0:
            return self.env['report'].get_action(self, 'stock_multiple_picker.picking_operations_group_document')
        else:
            return {'name': 'Set Picking Employee', 'res_model': 'stock.picking.multiple', 'view_model': 'form',
                   'view_mode': 'form', 'target': 'new', 'type': 'ir.actions.act_window'}

    def enumerate_picking_boxes(self):
        box_labels = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S',
                      'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
        i = 0
        for picking in self:
            picking.box_label = box_labels[i]
            i += 1


class stock_move(models.Model):
    _inherit = "stock.move"

    employee_id = fields.Many2one(string='Picking employee', comodel_name='hr.employee')

    def batch_report_get_lines(self):
        res = []
        qty = 0
        last_move = None
        for i, move in enumerate(self):
            next_move = i + 1 < len(self) and self[i + 1]
            if next_move and (move.product_id == next_move.product_id) and \
                    (move.picking_id.box_label == next_move.picking_id.box_label) and \
                    (move.quant_source_location == next_move.quant_source_location):
                qty += move.product_uom_qty
            else:
                qty += move.product_uom_qty
                same_location = False
                if last_move and last_move.quant_source_location == move.quant_source_location:
                    same_location = True
                res.append((move, int(qty), same_location))
                last_move = move
                qty = 0.0
        return res
