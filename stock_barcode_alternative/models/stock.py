# -*- coding: utf-8 -*-
##############################################################################
#
#  Odoo, Open Source Enterprise Resource Management Solution, third party addon
#  Copyright (C) 2019- Vertel AB (<http://vertel.se>).
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import api, fields, models,_
from openerp import http
from openerp.http import request
from openerp.exceptions import except_orm, Warning, RedirectWarning
# ~ from openerp.api import Environment
from openerp.tools import safe_eval as eval
from timeit import default_timer as timer
import traceback
import base64

import logging
_logger = logging.getLogger(__name__)

class BarcodeController(http.Controller):

    @http.route(['/barcode2/web/'], type='http', auth='user')
    def a(self, debug=False, **k):
        if not request.session.uid:
            return http.local_redirect('/web/login?redirect=/barcode2/web')

        return request.render('stock_barcode_alternative.barcode_index')

class stock_picking(models.Model):
    _inherit = 'stock.picking'
    
    # ~ abc_wizard_id = fields.Many2one(comodel_name='stock.transfer_details', string='Move Wizard', ondelete='set null')
    
    @api.model
    def abc_make_records(self, records, fields=None):
        """Build a record description for return to the JS interface."""
        fields = fields or ['id']
        # ~ model = records._name
        result = []
        field_types = {}
        def field_type(name):
            """Check the type of a field."""
            if name not in field_types:
                _logger.warn('\n\n%s\n%s' % (name, records.fields_get([name], attributes=['type'])))
                field_types[name] = records.fields_get([name], attributes=['type'])[name]['type']
            return field_types.get(name)
        for record in records:
            rec ={'_name': record._name, 'id': record.id}
            for field in fields:
                child_fields = None
                # Relational field
                if type(field) == tuple:
                    child_fields = field[1] or ['display_name']
                    field = field[0]
                value = getattr(record, field)
                if child_fields:
                    value = self.abc_make_records(value, child_fields)
                    if field_type(field) == 'many2one':
                        value = value and value[0] or None
                rec[field] = value
            result.append(rec)
        return result
    
    # ~ @api.multi
    # ~ def abc_do_enter_transfer_details(self):
        # ~ """Reuse the same wizard to handle package data and stuff.
        # ~ Try to make do without this first.
        # ~ """
        # ~ self.ensure_one()
        # ~ if not self.abc_wizard_id:
            # ~ context ={
                # ~ 'active_model': self._name,
                # ~ 'active_ids': [self.id],
                # ~ 'active_id': self.id
            # ~ }
            # ~ self.abc_wizard_id = self.env['stock.transfer_details'].with_context(**context).create({'picking_id': self.id})
        # ~ return self.abc_wizard_id.wizard_view()
    
    @api.multi
    def abc_load_picking(self):
        """Create a JSON description of a picking and its products for the Javascript GUI."""
        _logger.warn(self)
        self.ensure_one()
        picking = self.abc_make_records(
            self,
            [
                'name',
                'state',
                # ~ ('abc_wizard_id', []),
                ('partner_id', ['display_name']),
            ]
        )[0]
        if self.state == 'assigned':
            action = self.do_enter_transfer_details()
            wizard = self.env['stock.transfer_details'].browse(action['res_id'])
            operations = self.abc_make_records(
                wizard.item_ids,
                [
                    ('product_id', ['display_name']),
                    ('product_uom_id', ['display_name']),
                    'quantity',
                    ('package_id', []),
                    ('packop_id', []),
                    ('result_package_id', ['display_name']),
                    ('sourceloc_id', ['display_name']),
                    ('destinationloc_id', ['display_name']),
                    ('lot_id', ['display_name']),
                ]
            )
            products = self.abc_make_records(
                wizard.item_ids.mapped('product_id'),
                [
                    'display_name',
                    'default_code',
                    'ean13',
                ]
            )
        else:
            operations = []
            products = []
        # TODO: Find packages
        packages = []
        res = {'picking': picking, 'operations': operations, 'products': products, 'packages': packages}
        _logger.warn(res)
        return res
    
    @api.multi
    def abc_do_transfer(self, lines, packages, **data):
        """Complete the picking operation."""
        self.ensure_one()
        # Attempt to find the wizard used to create the data
        # TODO: Don't rely on the old wizard. Match the lines through packop_id.
        _logger.warn(lines)
        wizard = self.env['stock.transfer_details'].search([('item_ids', 'in', [l['id'] for l in lines])])
        if not wizard:
            raise Warning('The wizard has been deleted. Please restart the picking process. This will be fixed in future versions.')
        for item in wizard.item_ids:
            line = filter(lambda l: l['id'] == item.id, lines)[0]
            item.quantity = line['qty_done']
        wizard.do_detailed_transfer()
        return {'result': 'success'}
    
    @api.multi
    def abc_open_picking(self):
        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': '/barcode2/web#picking_id=%s' % self.id,
        }
    
    @api.model
    def abc_scan(self, code):
        product = self.env['product.product'].search(['|', ('ean13', '=', code), ('default_code', '=', code)], limit=1)
        if product:
            return {
                'type': 'product.product',
                'product': self.abc_make_records(
                    product,
                    ['display_name', 'default_code', 'ean13'])}
        picking = self.env['stock.picking'].search_read([('name', '=', code)], ['id'])
        if picking:
            return {
                'type': 'stock.picking',
                'picking': picking[0]
            }
        return {'type': 'no hit'}
