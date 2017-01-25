# -*- coding: utf-8 -*-
##############################################################################
#
# OpenERP, Open Source Management Solution, third party addon
# Copyright (C) 2017- Vertel AB (<http://vertel.se>).
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
from openerp import http
from openerp.http import request

import logging
_logger = logging.getLogger(__name__)


class stock_picking(models.Model):
    _inherit = "stock.picking"

    prepicked = fields.Boolean('Prepicked', compute='_get_prepicked', store=True)

    @api.one
    @api.depends('move_lines', 'state', 'move_lines.prepicked', 'move_lines.product_uom_qty')
    def _get_prepicked(self):
        if self.state != 'assigned':
            self.prepicked = False
            return
        for line in self.move_lines:
            if line.prepicked != line.product_uom_qty:
                self.prepicked = False
                return
        self.prepicked = True

    @api.model
    def process_barcode_from_prepicking(self, picking_id, barcode_str):
        '''This function is called each time there barcode scanner reads an input'''
        lot_obj = self.env['stock.production.lot']
        package_obj = self.env['stock.quant.package']
        product_obj = self.env['product.product']
        stock_move_obj = self.env['stock.move']
        stock_location_obj = self.env['stock.location']
        answer = {'filter_loc': False, 'move_id': False}
        #check if the barcode correspond to a location
        matching_location_ids = stock_location_obj.search([('loc_barcode', '=', barcode_str)])
        if matching_location_ids:
            #if we have a location, return immediatly with the location name
            answer['filter_loc'] = stock_location_obj._name_get(matching_location_ids[0])
            answer['filter_loc_id'] = matching_location_ids[0].id
            return answer
        #check if the barcode correspond to a product
        matching_product_ids = product_obj.search(['|', ('ean13', '=', barcode_str), ('default_code', '=', barcode_str)])
        if matching_product_ids:
            mv_id = stock_move_obj._search_and_increment(picking_id, [('product_id', '=', matching_product_ids[0].id)], increment=True)
            answer['move_id'] = mv_id
            return answer
        #check if the barcode correspond to a lot
        matching_lot_ids = lot_obj.search([('name', '=', barcode_str)])
        if matching_lot_ids:
            mv_id = stock_move_obj._search_and_increment(picking_id, [('product_id', '=', matching_lot_ids[0].product_id.id), ('lot_id', '=', matching_lot_ids[0].id)], increment=True)
            answer['move_id'] = mv_id
            return answer
        #check if the barcode correspond to a package
        matching_package_ids = package_obj.search([('name', '=', barcode_str)])
        if matching_package_ids:
            mv_id = stock_move_obj._search_and_increment(picking_id, [('product_id', '=', matching_package_ids[0].quant_ids.mapped('product_id').id)], increment=True)
            answer['move_id'] = mv_id
            return answer
        return answer

    @api.model
    def process_barcode_from_ui(self, picking_id, barcode_str, visible_op_ids, prepicking=False):
        '''This function is called each time there barcode scanner reads an input'''
        if prepicking:
            answer = {'filter_loc': False, 'operation_id': False}
            products = self.env['product.product'].search_read(['|', ('ean13', '=', barcode_str), ('default_code', '=', barcode_str)], ['id'])
            if products:
                op_id = self.env['stock.pack.operation']._search_and_increment_prepick(picking_id, [('product_id', '=', [p['id'] for p in products][0])], filter_visible=True, visible_op_ids=visible_op_ids, increment=True)
                answer['operation_id'] = op_id
                return answer
        return super(stock_picking, self).process_barcode_from_ui(picking_id, barcode_str, visible_op_ids)

    @api.model
    def process_product_id_from_ui(self, picking_id, product_id, op_id, increment=True, prepicking=False):
        if prepicking:
            return self.env['stock.pack.operation']._search_and_increment_prepick(picking_id, [('product_id', '=', product_id), ('id', '=', op_id)], increment=increment)
        return self.env['stock.pack.operation']._search_and_increment(picking_id, [('product_id', '=', product_id), ('id', '=', op_id)], increment=increment)

    @api.v7
    def get_next_picking_for_ui(self, cr, uid, context=None):
        """ returns the next pickings to process. Used in the barcode scanner UI"""
        if context is None:
            context = {}
        prepick = context.get('prepick')
        employee_obj = self.pool.get('hr.employee')
        picker = employee_obj.search(cr, uid, [('user_id', '=', uid)], context=context)
        domain = [('state', 'in', ('assigned', 'partially_available'))]
        if prepick and picker:
            domain.append(('move_lines.employee_id', '=', picker[0]))
        if context.get('default_picking_type_id'):
            domain.append(('picking_type_id', '=', context['default_picking_type_id']))
        return self.pool.get('stock.picking').search(cr, uid, domain, context=context)

class stock_move(models.Model):
    _inherit = "stock.move"

    prepicked = fields.Float(string='To be picked', default=0.0)

    @api.model
    def _search_and_increment(self, picking_id, domain, increment=True):
        move_ids = self.search([('picking_id', '=', picking_id)] + domain)
        if len(move_ids) > 0:
            pp_qty = move_ids[0].prepicked
            if increment:
                pp_qty += 1.0
            else:
                pp_qty -= 1.0 if pp_qty >= 1.0 else 0.0
            move_ids[0].prepicked = pp_qty
        return move_ids[0].id if len(move_ids) > 0 else None

    @api.model
    def move_line_increment(self, move_id, increase):
        move = self.browse(int(move_id))
        full = False
        if move:
            pp_qty = move.prepicked
            if increase == 'True':
                if pp_qty < move.product_uom_qty:
                    pp_qty += 1.0
                    if pp_qty < move.product_uom_qty:
                        full = False
                    else:
                        full = True
                else:
                    full = True
            if increase == 'False':
                if pp_qty > 0.0:
                    pp_qty -= 1.0
                full = False
            move.prepicked = pp_qty
        return full

    @api.model
    def move_line_set(self, move_id, qty):
        move = self.browse(int(move_id))
        if move:
            move.prepicked = qty

class stock_pack_operation(models.Model):
    _inherit = "stock.pack.operation"

    waiting_to_be_packed = fields.Boolean('Waiting to be Packed', default=False)
    prepicked = fields.Float('Picked')

    @api.model
    def _search_and_increment_prepick(self, picking_id, domain, filter_visible=False, visible_op_ids=False, increment=True):
        '''Search for an operation with given 'domain' in a picking, if it exists increment the prepicked (+1) otherwise create it

        :param domain: list of tuple directly reusable as a domain
        context can receive a key 'current_package_id' with the package to consider for this operation
        returns True
        '''
        _logger.warn('picking_id: %s\ndomain: %s\nfilter_visible: %s\nvisible_op_ids: %s\nincrement: %s' % (picking_id, domain, filter_visible, visible_op_ids, increment))
        existing_operations = self.search([('picking_id', '=', picking_id)] + domain)
        todo_operations = self.browse([])
        if existing_operations:
            if filter_visible:
                todo_operations = [r for r in existing_operations if r.id in visible_op_ids]
            else:
                todo_operations = [r for r in existing_operations]
        if todo_operations:
            #existing operation found for the given domain and picking => increment its quantity
            op = todo_operations[0]
            operation_id = op.id
            if increment:
                op.prepicked += 1
            else:
                op.prepicked -= 1 if op.prepicked >= 1 else 0
                #~ if op.prepicked == 0 and op.product_qty == 0:
                    #~ #we have a line with 0 qty set, so delete it
                    #~ op.unlink()
                    #~ return False
        else:
            #no existing operation found for the given domain and picking => create a new one
            picking = self.env["stock.picking"].browse(picking_id)
            values = {
                'picking_id': picking_id,
                'product_qty': 0,
                'location_id': picking.location_id.id,
                'location_dest_id': picking.location_dest_id.id,
                'qty_done': 0,
                'prepicked': 1,
                }
            for key in domain:
                var_name, dummy, value = key
                uom_id = False
                if var_name == 'product_id':
                    values.update({'product_id': self.env['product.product'].browse(value).uom_id.id})
                else:
                    values.update({var_name: value})
            operation_id = self.create(values)
        return operation_id

    def action_waiting(self, cr, uid, ids, context=None):
        ''' Used by barcode interface to say that pack_operation has been moved from src location
            to destination location, if qty_done is less than product_qty than we have to split the
            operation in two to process the one with the qty moved
        '''
        waiting_ids = []
        move_obj = self.pool.get("stock.move")
        for pack_op in self.browse(cr, uid, ids, context=None):
            if pack_op.product_id and pack_op.location_id and pack_op.location_dest_id:
                move_obj.check_tracking_product(cr, uid, pack_op.product_id, pack_op.lot_id.id, pack_op.location_id, pack_op.location_dest_id, context=context)
            op = pack_op.id
            if pack_op.qty_done < pack_op.product_qty:
                # we split the operation in two
                op = self.copy(cr, uid, pack_op.id, {'product_qty': pack_op.qty_done, 'picked_qty_done': pack_op.qty_done}, context=context)
                self.write(cr, uid, [pack_op.id], {'product_qty': pack_op.product_qty - pack_op.qty_done, 'picked_qty_done': 0}, context=context)
            waiting_ids.append(op)
        self.write(cr, uid, waiting_ids, {'waiting_to_be_packed': 'true'}, context=context)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
