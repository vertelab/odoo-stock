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


class PrepickingController(http.Controller):

    @http.route(['/prepicking/<model("stock.picking"):picking>/picking'], type='http', auth="user", website=True)
    def prepicking(self, picking=None, **post):
        #~ if not request.session.uid:
            #~ return http.local_redirect('/web/login?redirect=/prepicking/web')
        #~ pickings = request.env['stock.picking'].search([('employee_ids', 'in', request.env['hr.employee'].search([('user_id', '=', request.env.user.id)]))])
        return request.render('stock_prepicking.prepicking_index', {'pickings': [picking]})

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

    def process_barcode_from_prepicking(self, cr, uid, picking_id, barcode_str):
        '''This function is called each time there barcode scanner reads an input'''
        lot_obj = self.pool.get('stock.production.lot')
        package_obj = self.pool.get('stock.quant.package')
        product_obj = self.pool.get('product.product')
        stock_move_obj = self.pool.get('stock.move')
        stock_location_obj = self.pool.get('stock.location')
        answer = {'filter_loc': False, 'move_id': False}
        #check if the barcode correspond to a location
        matching_location_ids = stock_location_obj.search(cr, uid, [('loc_barcode', '=', barcode_str)])
        if matching_location_ids:
            #if we have a location, return immediatly with the location name
            location = stock_location_obj.browse(cr, uid, matching_location_ids[0])
            answer['filter_loc'] = stock_location_obj._name_get(cr, uid, location)
            answer['filter_loc_id'] = matching_location_ids[0]
            return answer
        #check if the barcode correspond to a product
        matching_product_ids = product_obj.search(cr, uid, ['|', ('ean13', '=', barcode_str), ('default_code', '=', barcode_str)])
        if matching_product_ids:
            op_id = stock_move_obj._search_and_increment(cr, uid, picking_id, [('product_id', '=', matching_product_ids[0])], increment=True)
            answer['move_id'] = op_id
            return answer
        #check if the barcode correspond to a lot
        matching_lot_ids = lot_obj.search(cr, uid, [('name', '=', barcode_str)])
        if matching_lot_ids:
            lot = lot_obj.browse(cr, uid, matching_lot_ids[0])
            op_id = stock_move_obj._search_and_increment(cr, uid, picking_id, [('product_id', '=', lot.product_id.id), ('lot_id', '=', lot.id)], increment=True)
            answer['move_id'] = op_id
            return answer
        #check if the barcode correspond to a package
        matching_package_ids = package_obj.search(cr, uid, [('name', '=', barcode_str)])
        if matching_package_ids:
            package = package_obj.browse(cr, uid, matching_package_ids[0])
            op_id = stock_move_obj._search_and_increment(cr, uid, picking_id, [('product_id', '=', package.quant_ids.mapped('product_id').id)], increment=True)
            answer['move_id'] = op_id
            return answer
        return answer

class stock_move(models.Model):
    _inherit = "stock.move"

    prepicked = fields.Float(string='To be picked')

    def _search_and_increment(self, cr, uid, picking_id, domain, increment=True):
        move_id = None
        existing_move_ids = self.search(cr, uid, [('picking_id', '=', picking_id)] + domain)
        if len(existing_move_ids) > 0:
            move_id = self.browse(cr, uid, existing_move_ids[0])
            pp_qty = move_id.prepicked
            if increment:
                pp_qty += 1.0
            else:
                pp_qty -= 1.0 if pp_qty >= 1.0 else 0.0
            self.write(cr, uid, move_id.id, {'prepicked': pp_qty})
        return move_id.id if move_id else None

    def move_line_increment(self, cr, uid, move_id, increase):
        move = self.browse(cr, uid, int(move_id))
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
            self.write(cr, uid, move.id, {'prepicked': pp_qty})
        return full

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
