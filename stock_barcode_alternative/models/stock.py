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
from time import sleep
from openerp.modules.registry import Registry

import logging
_logger = logging.getLogger(__name__)

# Increasing persistance time for packop wizards.
# TODO: Remove this when we implement better transfer method.
class StockTransferDetails(models.TransientModel):
    _inherit = 'stock.transfer_details'
    _transient_max_hours = 24

class StockTransferDetailsItems(models.TransientModel):
    _inherit = 'stock.transfer_details_items'
    _transient_max_hours = 24

class BarcodeController(http.Controller):

    @http.route(['/barcode2/web/'], type='http', auth='user')
    def abc_interface(self, debug=False, **k):
        if not request.session.uid:
            return http.local_redirect('/web/login?redirect=/barcode2/web')

        return request.render('stock_barcode_alternative.barcode_index')

class StockPicking(models.Model):
    _inherit = 'stock.picking'
    
    # ~ abc_wizard_id = fields.Many2one(comodel_name='stock.transfer_details', string='Move Wizard', ondelete='set null')
    
    @api.model
    def abc_make_records(self, records, fields=None):
        """Build a record description for return to the JS interface."""
        fields = fields or self.abc_get_model_fields(records)
        # ~ model = records._name
        result = []
        field_types = {}
        def field_type(name):
            """Check the type of a field."""
            if name not in field_types:
                #_logger.warn('\n\n%s\n%s' % (name, records.fields_get([name], attributes=['type'])))
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

    @api.model
    def abc_get_model_fields(self, record):
        """Return a list of the fields that should be loaded for this model."""
        if record._name == 'stock.picking':
            return [
                'name',
                'state',
                ('partner_id', ['display_name']),
            ]
        if record._name == 'stock.transfer_details_items':
            return [
                    ('product_id', ['display_name']),
                    ('product_uom_id', ['display_name', 'factor']),
                    'quantity',
                    ('package_id', []),
                    ('packop_id', []),
                    ('result_package_id', ['display_name']),
                    ('sourceloc_id', ['display_name']),
                    ('destinationloc_id', ['display_name']),
                    ('lot_id', ['display_name']),
                ]
        if record._name == 'product.product':
            return [
                    'display_name',
                    'default_code',
                    'ean13',
                    'weight',
                    ('uom_id', ['display_name', 'factor']),
                ]
        return ['id']
    
    @api.multi
    def abc_load_picking(self):
        """Create a JSON description of a picking and its products for the Javascript GUI."""
        _logger.warn(self)
        _logger.warn(self._context)
        self.ensure_one()
        picking = self.abc_make_records(self)[0]
        if self.state == 'assigned':
            action = self.do_enter_transfer_details()
            wizard = self.env['stock.transfer_details'].browse(action['res_id'])
            operations = self.abc_make_records(wizard.item_ids)
            products = self.abc_make_records(wizard.item_ids.mapped('product_id'))
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
        _logger.warn('\nabc_do_transfer\n\n%s\n\n%s\n\n%s' % (lines, packages, data))
        self.ensure_one()
        res = {'warnings': [], 'messages': [], 'results': {}}
        params = {}
        for step in [s[1] for s in sorted(self.abc_transfer_steps())]:
            # Perform all the necessary picking steps
            # lines     Line data from UI
            # packages  Package data from UI
            # data      Other data from UI
            # params    Parameters accumulated in the picking process. Inject data communicated between steps here.
            # res       The result returned to the UI.
            getattr(self, step)(lines, packages, data, params, res)
        return res
            
    @api.model
    def abc_transfer_steps(self):
        """Return all the steps (function names) to complete the picking process in the correct order."""
        return [
            (20, 'abc_transfer_wizard'),
            (40, 'abc_create_invoice'),
            (60, 'abc_confirm_invoice')]
    
    @api.multi
    def abc_transfer_wizard(self, lines, packages, data, params, res):
        # Attempt to find the wizard used to create the data
        # TODO: Don't rely on the old wizard. Match the lines through packop_id.
        _logger.warn(lines)
        res['results']['transfer'] = 'failure'
        wizard = self.env['stock.transfer_details'].search([('item_ids', 'in', [l['id'] for l in lines])])
        if not wizard:
            raise Warning('The wizard has been deleted. Please restart the picking process. This will be fixed in future versions.')
        for item in wizard.item_ids:
            line = filter(lambda l: l['id'] == item.id, lines)[0]
            item.quantity = line['qty_done']
        wizard.do_detailed_transfer()
        res['results']['transfer'] = 'success'
        params['wizard'] = wizard
    
    @api.multi
    def abc_create_invoice(self, lines, packages, data, params, res):
        res_invoice = {'id': None, 'name': ''}
        res['invoice'] = res_invoice
        # Check if this order is NOT to be invoiced (prepaid most likely)
        if self.invoice_state == 'none':
            res_invoice['no_invoice'] = True
            # TODO: Check where order policy comes from.
            if self.sale_id and self.sale_id.order_policy == 'prepaid':
                res_invoice['prepaid'] = True
            return
        
        # Check if this order is already invoiced. Unknown when this might happen.
        if self.invoice_state == 'invoiced':
            res_invoice['already_invoiced'] = True
            return
        # Create invoice
        try:
            context = {'active_id': self.id, 'active_ids': self._ids, 'active_model': self._name, 'default_invoice_date': fields.Date.today()}
            wizard = self.env['stock.invoice.onshipping'].with_context(context).create({})
            action = wizard.open_invoice()
            params['invoice'] = invoice = self.env['account.invoice'].browse(eval(action['domain'])[0][2][0])
            res_invoice['id'] = invoice.id
            res_invoice['name'] = invoice.name
            res['results']['invoice'] = 'created'
            invoice_menu = self.env.ref('account.menu_action_invoice_tree1')
            res_invoice['url'] = "/web#id=%s&view_type=form&model=account.invoice&menu_id=%s&action=%s" % (invoice.id, invoice_menu.id, invoice_menu.action.id)
            res['messages'].append(u'Created an <a taret="_blank" href="%s">invoice</a>.' % res_invoice['url'])
        except Exception as e:
            res['results']['invoice'] = 'failure'
            res['warnings'].append((
                _(u"Failed to create invoice!"),
                '%s\n\nTraceback:\n%s' % (e.message or 'Unknown Error', traceback.format_exc())))

    # ~ @api.model
    # ~ def abc_test_lock_invoice(self, invoice, lock_time=5):
        # ~ _logger.warn('\n\ninvoice locked!\n')
        # ~ invoice.signal_workflow('invoice_open')
        # ~ sleep(lock_time)
        # ~ raise Warning('invoice lock released!')
    
    @api.multi
    def abc_confirm_invoice(self, lines, packages, data, params, res):
        """Confirm invoice. Split into its own function to not lock the invoice sequence."""
        invoice = params.get('invoice')
        if invoice and invoice.state == 'draft':
            self.env.cr.commit()
            env = None
            try:
                # Ne cursor doesn't time out when requesting lock.
                # Could be bad I guess? Works for now.
                # TODO: Look into setting a more reasonable lock wait time.
                new_cr = Registry(self.env.cr.dbname).cursor()
                new_cr.autocommit(True)
                env = api.Environment(new_cr, self.env.uid, self.env.context)
                # Validate invoice
                invoice.signal_workflow('invoice_open')
                res['invoice']['name'] = invoice.number
                res['messages'].append(u"Created and confirmed invoice %s." % invoice.number)
                res['results']['invoice'] = 'confirmed'
                # Commit to unlock the invoice sequence
                env.cr.commit()
            except Exception as e:
                res['warnings'].append((
                    _(u"Failed to confirm invoice %s!") % (invoice and (invoice.number or invoice.name) or 'Unknown'),
                    '%s\n\nTraceback:\n%s' % (e.message or 'Unknown Error', traceback.format_exc())))
            finally:
                if env:
                    env.cr.close()
    
    @api.multi
    def abc_open_picking(self):
        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': '/barcode2/web#picking_id=%s' % self.id,
        }
    
    @api.model
    def abc_scan(self, code):
        """Perform scan on the supplied barcode."""
        products = self.env['product.product'].search(['|', ('ean13', '=', code), ('default_code', '=', code)])
        if products:
            return {
                'type': 'product.product',
                'product': self.abc_make_records(
                    products,
                    ['display_name', 'default_code', 'ean13'])}
        picking = self.env['stock.picking'].search_read([('name', '=', code)], ['id'])
        if picking:
            return {
                'type': 'stock.picking',
                'picking': picking[0]
            }
        return {'type': 'no hit'}

class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'
    
    @api.multi
    def abc_open_barcode_interface(self):
        return {
            'type': 'ir.actions.act_url',
            'target': 'self',
            'url': '/barcode2/web',
        }
