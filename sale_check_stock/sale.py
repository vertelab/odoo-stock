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
                is_available = line._check_routing(product, self.warehouse_id.id)
                
                #check if product is available, and if not: raise a warning, but do this only for products that aren't processed in MTO
                if not is_available:
                    uom_record = line.product_uom
                    compare_qty = float_compare(line.product_id.virtual_available, line.product_uom_qty, precision_rounding=uom_record.rounding)
                    if compare_qty == -1:
                        out_of_stock.append(_('%s: You plan to sell %.2f %s but you only have %.2f %s available!\nThe real stock is %.2f %s. (without reservations)') % \
                            (line.product_id.name_get()[0][1],
                            line.product_uom_qty, uom_record.name,
                            max(0,product.virtual_available), uom_record.name,
                            max(0,product.qty_available), uom_record.name))
                        
                                
        if out_of_stock:
            raise Warning(_('Missing stock:\n') + '\n'.join(out_of_stock))
            
