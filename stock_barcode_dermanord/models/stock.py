from odoo import api, fields, models, _
from odoo import http
from odoo.http import request
from odoo.tools import safe_eval as eval
import traceback

from odoo.modules.registry import Registry

import logging
_logger = logging.getLogger(__name__)

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.model
    def abc_scan(self, code):
        """Perform scan on the supplied barcode."""
        
        resp = super.abc_scan(code)
        if(resp['type'] == 'no-hit'):
            products = self.env['product.product'].search(['|', ('ean13', '=', code), ('default_code', '=', code)])
            if products:
                return {
                    'type': 'product.product',
                    'product': self.abc_make_records(products)}
        return resp
