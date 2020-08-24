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
from openerp import models, fields, api, _
from datetime import datetime, timedelta, date
from openerp.tools import safe_eval as eval
import pytz
import traceback
from openerp.exceptions import Warning

import logging
_logger = logging.getLogger(__name__)

#~ 20,00       sales_count
#~ 1,981039     so_line_ids
#~ 1,022867     sale_order_lines
#~ 0,390086     code

class product_wizard(models.TransientModel):
    _name = 'product.batch_list'
    
    def compute_default_value(self):
        return self.env[self.env.context.get('active_model')].browse(self.env.context.get('active_id'))
        
    product_id = fields.Many2one(comodel_name = 'product.product', string = 'Product', default = compute_default_value)
    quant_ids = fields.One2many(comodel_name = 'product.batch_list_quant', string = 'Quants', inverse_name='batch_list_id')
    location_id = fields.Many2one(comodel_name='stock.location') # domain|context|ondelete="'set null', 'restrict', 'cascade'"|auto_join|delegate
    lot_id = fields.Many2one(comodel_name='stock.production.lot')

    @api.onchange('location_id')
    def onchange_location_id (self):
        # ~ raise Warning(self.env.context)
        domain = [('product_id', '=', self.product_id.id)]
        if self.location_id:
            domain.append(('location_id', 'child_of', self.location_id.id))
        if self.lot_id:
            domain.append(('lot_id', '=', self.lot_id.id))
        quants = self.env['stock.quant'].search(domain)
        quant_ids = []
        if self.quant_ids:
            self.quant_ids.append((5,))
        for quant in quants:
            quant_ids.append((0, 0, {'name':quant.name, 'qty':quant.qty, 'lot_id':quant.lot_id.id,'removal_date':quant.removal_date, 'quant_id': quant.id}))
        self.quant_ids = quant_ids
        self.product_id = self.env['product.product'].browse(self.env.context.get('active_id'))
        
    def choose_batch(self):
        for quant in self.quant_ids:
            quant.quant_id.sudo().write({'lot_id': quant.lot_id.id, 'qty': quant.qty})
    @api.multi
    def empty_location_id(self, *args):
        location = self.env['stock.location'].search([('name','=','Scrapped')])[0]
        
        _logger.warn("stock_batch location %s" %location)
        move=self.env['stock.move'].create({
            'name': _('SCRAP:') + self.product_id.display_name,
            'product_id': self.product_id.id,
            'product_uom': self.product_id.uom_id.id,
            'product_uom_qty': sum([q.qty for q in self.quant_ids.mapped('quant_id')]),
            'date': fields.Datetime.now(),
            'company_id': self.env.user.company_id.id,
            'state': 'confirmed',
            'location_id': self.location_id.id,
            'location_dest_id': location.id,
        })
        # ~ self.env['stock.quant'].quants_move([(q, q.qty) for q in self.quant_ids.mapped('quant_id')], None, location)
        move.action_done()
    
    
class product_batch_list_quant(models.TransientModel):
    _name = 'product.batch_list_quant'
    
    name = fields.Char(string='Name')
    batch_list_id = fields.Many2one(comodel_name='product.batch_list', ondelete='cascade', required=True)
    qty = fields.Float(string='Quantity')
    lot_id = fields.Many2one(comodel_name='stock.production.lot', string = 'Lot Id')
    removal_date = fields.Datetime(string='Date')
    quant_id = fields.Many2one(comodel_name='stock.quant') # domain|context|ondelete="'set null', 'restrict', 'cascade'"|auto_join|delegate
    

class product_product(models.Model):
    _inherit = 'product.product'
       
    def batch_wizard(self):
        return {    'name': 'product.quantity.batch',
                    'res_model': 'product.batch_list',
                    'src_model': 'product.product',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'target': 'new',
                    'view_id': self.env.ref('stock_batch_list.view_batch_list').id 
                }
