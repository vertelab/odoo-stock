from odoo import api, fields, models, _
from odoo import http
from odoo.http import request
from odoo.tools import safe_eval as eval
import traceback

from odoo.modules.registry import Registry

import logging
_logger = logging.getLogger(__name__)


class BarcodeController(http.Controller):

    @http.route(['/barcode2/web/'], type='http', auth='user')
    def abc_interface(self, debug=False, **k):
        if not request.session.uid:
            return http.local_redirect('/web/login?redirect=/barcode2/web')

        return request.render('stock_barcode_alternative.barcode_index')


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.model
    def abc_make_records(self, records, fields=None):
        """Build a record description for return to the JS interface."""
        fields = fields or self.abc_get_model_fields(records)
        result = []
        field_types = {}

        def field_type(name):
            """Check the type of a field."""
            if name not in field_types:
                field_types[name] = records.fields_get([name], attributes=['type'])[name]['type']
            return field_types.get(name)
        for record in records:
            rec = {'_name': record._name, 'id': record.id}
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
            _logger.debug('Lukas1: field %s %s' % (result, fields))
        return result

    @api.model
    def abc_get_model_fields(self, record):
        """Return a list of the fields that should be loaded for this model."""
        if record._name == 'stock.picking':
            return [
                'name',
                ('product_id', ['sale_ok']),
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
                    # ('sourceloc_id', ['display_name']),
                    ('destinationloc_id', ['display_name']),
                    ('lot_id', ['display_name']),
                ]
        if record._name == 'stock.move.line':
            return [
                    ('product_id', ['display_name']),
                    ('product_uom_id', ['display_name', 'factor']),
                    'product_uom_qty',
                    'product_qty',
                    'qty_done',
                    ('location_id', ['display_name']),
                    ('location_dest_id', ['display_name']),
                ]
        if record._name == 'stock.move':
            return [
                    ('product_id', ['display_name']),
                    ('product_uom', ['display_name', 'factor']),
                    'product_uom_qty',
                    'product_qty',
                    'reserved_availability',
                    'availability',
                    'quantity_done',
                    'forecast_availability',
                    ('location_id', ['display_name']),
                    ('location_dest_id', ['display_name']),
                ]
        if record._name == 'stock.quant.package':
            return [
                    'name',
                    ('location_id', ['display_name']),
                    ('packaging_id', ['display_name']),
                ]
        if record._name == 'product.product':
            return [
                    'display_name',
                    'default_code',
                    'barcode',
                    'sale_ok',
                    'weight',
                    ('uom_id', ['display_name', 'factor']),
                ]
        if record._name == 'stock.location':
            return [
                    'display_name',
                ]
        if record._name == 'product.uom':
            return [
                    'display_name',
                    'factor',
                ]
        if record._name == 'product.packaging':
            return [
                    'name',
                    'height',
                    'width',
                    'packaging_length',
                    'weight',
                    'max_weight',
                    'barcode'
                ]
        return ['id']

    def abc_load_picking(self, picking_id):
        """Create a JSON description of a picking and its products for the Javascript GUI."""
        # ~ _logger.warn(self)
        # ~ _logger.warn(self._context)
        stock_picking_id = self.env['stock.picking'].browse(picking_id)
        picking = self.abc_make_records(stock_picking_id)
        if stock_picking_id.state == 'assigned':
            operations = self.abc_make_records(stock_picking_id.move_line_ids)
            products = self.abc_make_records(stock_picking_id.move_line_ids.mapped("product_id"))
            _logger.warning(f"products victor: {products}")
        else:
            operations = []
            products = []
        # TODO: Find packages
        packages = []
        res = {'picking': picking, 'operations': operations, 'products': products, 'packages': packages}
        _logger.debug('Lukas3: field %s ' % products)
        # ~ _logger.warn(res)
        return res

    def abc_do_transfer(self, lines, packages, **data):
        """Complete the picking operation."""
        _logger.warning(f"victor self: {self}, lines: {lines}, packages: {packages}, data: {data}")
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

    def abc_create_row(self, row):
        """Provide default locations and other data """
        # Lifted from action_assign on stock.move
        product = self.env['product.product'].browse(row['product_id'])
        _logger.warning("Lukas5: %s" % product['sale_ok'])
        location = self.location_id
        main_domain = [('reservation_id', '=', False), ('qty', '>', 0)]
        quants = self.env['stock.quant'].quants_get_prefered_domain(
            location,
            product,
            row['quantity'] or 1.0,
            domain=main_domain,
            prefered_domain_list=[])
        # Find suggested location. Could be more than one given quantity > 0.
        # All that stuff remains to be solved.
        for quant in quants:
            if quant[0]:
                location = quant[0].location_id
        _logger.warning("Lukas6: %s" % self.abc_make_records(product, ['sale_ok']))
        row.update({
            '_name': 'stock.transfer_detailsitems',
            'product_id': self.abc_make_records(product, ['display_name'])[0],
            'sale_ok' : self.abc_make_records(product, ['sale_ok'])[0],
            'destinationloc_id': self.abc_make_records(self.location_dest_id)[0],
            # 'sourceloc_id': self.abc_make_records(location)[0],
            'product_uom_id': self.abc_make_records(product.uom_id)[0],
        })
        return row

    @api.model
    def abc_transfer_steps(self):
        """Return all the steps (function names) to complete the picking process in the correct order."""
        return [
            (20, 'abc_transfer_wizard'),
            (40, 'abc_create_invoice'),
            (60, 'abc_confirm_invoice')
        ]

    def abc_transfer_wizard(self, lines, packages, data, params, res):
        """Run the transfer wizard on the given lines."""
        
        _logger.warning(f"victor self: {self}, lines: {lines}, {data=}, {params=}, {res=}")
        for move in lines:
            _logger.warning(f" victor in data: {move['qty_done']}")
            _logger.warning(f" victor odoo data: {self.env['stock.move.line'].browse(move['id']).qty_done}")
            self.env["stock.move.line"].browse(move['id']).qty_done = move['qty_done']
            _logger.warning(f" victor odoo data: {self.env['stock.move.line'].browse(move['id']).qty_done}")
        action = self.button_validate()
        _logger.warning(f"victor validate: {action}")
        # Keep track of matched transfer items
        res['results']['transfer'] = 'success'
        params['wizard'] = action

    def abc_create_invoice(self, lines, packages, data, params, res):
        _logger.warning(f"victor: {self.sale_id._create_invoices()}")

    def abc_confirm_invoice(self, lines, packages, data, params, res):
        """Confirm invoice. Split into its own function to not lock the invoice sequence."""
        pass

    def abc_open_picking(self):
        _logger.warning("Lukas8: %s" % self)
        return {
            'type': 'ir.actions.act_url',
            'target': 'self',
            'url': '/barcode2/web#picking_id=%s' % self.id,
        }

    @api.model
    def abc_scan(self, code):
        """Perform scan on the supplied barcode."""
        products = self.env['product.product'].search(['|', ('barcode', '=', code), ('default_code', '=', code)])
        if products:
            return {
                'type': 'product.product',
                'product': self.abc_make_records(products)}
        # ~ picking = self.env['stock.picking'].search_read([('name', '=', code)], ['id'])
        # ~ if not picking:
            # ~ picking = self.env['stock.picking'].search_read([('name', '=', code.replace('-', '/'))], ['id'])
            #TODO: this is a hardcode thingy for testing, use the one above instead
        picking = self.env['stock.picking'].search_read([('name', '=', 'WH/OUT/00100')], ['id'])
        if picking:
            return {
                'type': 'stock.picking',
                'picking': picking[0]
            }
        package = self.env['product.packaging'].search([('barcode', '=', code)])
        return {
                'type': 'product.packaging',
                'package': self.abc_make_records(package)
            }
        return {'type': 'no hit'}

class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    def abc_open_barcode_interface(self):
        _logger.warning("Lukas10: %s" % self)
        return {
            'type': 'ir.actions.act_url',
            'target': 'self',
            'url': '/barcode2/web',
        }
