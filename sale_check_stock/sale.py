# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution, third party addon
#    Copyright (C) 2019- Vertel AB (<http://vertel.se>).
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
from openerp.tools import float_compare
from openerp.exceptions import Warning  
import logging
_logger = logging.getLogger(__name__)

class sale_order(models.Model):
    _inherit = 'sale.order'
    
    @api.multi
    def check_order_stock(self):
        out_of_stock = []
        
        for line in self.order_line:
            product = line.product_id
            if product.type == 'product':
                #determine if the product needs further check for stock availibility
                # is_available = line._check_routing(product, self.warehouse_id.id)
                
                if  product.virtual_available_days < 5 or product.consumption_per_day < line.product_uom_qty:
                    uom_record = line.product_uom
                    compare_qty = float_compare(line.product_id.virtual_available_netto, line.product_uom_qty, precision_rounding=uom_record.rounding)
                    if compare_qty == -1:
                        out_of_stock.append(_('%s: You plan to sell %.2f %s but you only have %.2f %s available!\nThe real stock is %.2f %s. (without reservations)') % \
                            (line.product_id.name_get()[0][1],
                            line.product_uom_qty, uom_record.name,
                            max(0,product.virtual_available_netto), uom_record.name,
                            max(0,product.qty_available), uom_record.name))
        
        if out_of_stock:
            raise Warning(_('Missing stock:\n') + '\n'.join(out_of_stock))

class sale_order_line(models.Model):
    _inherit = 'sale.order.line'

    @api.one
    @api.onchange('product_uom_qty')
    def check_product_uom_qty(self, product_id):
        if self.product_uom_qty:
            if self.product_id.type == 'product':
                if  self.product_id.virtual_available_days < 5 or self.product_id.consumption_per_day < self.product_uom_qty:
                    compare_qty = float_compare(self.product_id.virtual_available_netto, self.product_uom_qty, precision_rounding=self.product_uom.rounding)
                    if compare_qty == -1:
                        raise Warning(_('Missing stock:\n%s: You plan to sell %.2f %s but you only have %.2f %s available!\nThe real stock is %.2f %s. (without reservations)') % \
                            (self.product_id.name_get()[0][1],
                            self.product_uom_qty, self.product_uom.name,
                            max(0,self.product_id.virtual_available_netto), self.product_uom.name,
                            max(0,self.product_id.qty_available), self.product_uom.name))


