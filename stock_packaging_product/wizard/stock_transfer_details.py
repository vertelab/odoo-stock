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
    
class stock_transfer_details(models.TransientModel):
    _inherit = 'stock.transfer_details'
    
    @api.model
    def _get_products_from_package(self, package, packages, products):
        if package not in packages:
            packages |= package
            if package.ul_id and package.ul_id.product_id:
                products[package.ul_id.product_id] = products.get(package.ul_id.product_id, 0) + 1
            if package.parent_id:
                products, packages = self._get_products_from_package(package.parent_id, packages, products)
        return products, packages
            
    
    @api.one
    def do_detailed_transfer(self):
        if self.picking_id.state not in ['assigned', 'partially_available']:
            raise Warning(_('You cannot transfer a picking in state \'%s\'.') % self.picking_id.state)
        products = {}
        packages = self.env['stock.quant.package'].browse()
        for item in self.item_ids:
            if item.result_package_id:
                products, packages = self._get_products_from_package(item.result_package_id, packages, products)
        if products:
            moves = self.env['stock.move'].browse()
            for product in products:
                move = self.env['stock.move'].create({
                    'picking_id': self.picking_id.id,
                    'product_id': product.id,
                    'product_uom_qty': products[product],
                    'group_id': self.picking_id.group_id.id,
                    'state': 'assigned',
                    'invoice_state': 'none',
                    'name': product.name,
                    'location_id': self.picking_id.picking_type_id.default_location_src_id and self.picking_id.picking_type_id.default_location_src_id.id or False,
                    'location_dest_id': self.picking_id.picking_type_id.default_location_dest_id and self.picking_id.picking_type_id.default_location_dest_id.id or False,
                    'product_uom': product.uom_id.id,
                    
                })
                move.action_done()
        super(stock_transfer_details, self).do_detailed_transfer()
        return True
    

