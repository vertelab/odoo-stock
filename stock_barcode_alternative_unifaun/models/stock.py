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

class StockPicking(models.Model):
    _inherit = 'stock.picking'
    
    @api.model
    def abc_get_model_fields(self, record):
        res = super(StockPicking, self).abc_get_model_fields(record)
        if record._name == 'stock.picking':
            res += ['is_unifaun', 'unifaun_parcel_count', 'unifaun_parcel_weight']
        return res
    
    @api.model
    def abc_transfer_steps(self):
        steps = super(StockPicking, self).abc_transfer_steps()
        steps.append((30, 'abc_unifaun'))
        steps.append((10, 'abc_unifaun_parcel_data'))
        return steps
    
    @api.multi
    def abc_unifaun_parcel_data(self, lines, packages, data, params, res):
        """"""
        if self.carrier_id.is_unifaun and not data.get('unifaun_no_order'):
            self.write({
                'unifaun_parcel_count': data.get('unifaun_parcel_count', 0),
                'unifaun_parcel_weight': data.get('unifaun_parcel_weight', 0),
            })
    
    @api.multi
    def abc_unifaun(self, lines, packages, data, params, res):
        """Order shipping through Unifaun."""
        # ~ # Print Stock Delivery Slip
        # ~ res.update(self.action_barcode_ui_print_delivery_slip())
        
        if self.carrier_id.is_unifaun and not data.get('unifaun_no_order'):
            res['results']['unifaun'] = 'failure'
            try:
                self.order_stored_shipment()
                if self.unifaun_status_ids:
                    # TODO: Translation, error details
                    res['warnings'].append((_(u"Det finns felmeddelanden i svaret från Unifaun.\n\n1) Kontrollera meddelandena och rätta ordern\n2)Beställ om transport (Order Transport-knappen)\n3) Verifiera att problemen är lösta\n4) Bekräfta transporten\n5) Skriv ut etiketten"), 'TODO: List details from Unifaun here'))
                else:
                    self.confirm_stored_shipment()
                    # ~ res.update(self.action_barcode_ui_print_unifaun_label())
                    res['results']['unifaun'] =  'success'
            except Exception as e:
                res['warnings'].append((
                    u'Något gick fel i Unifaun-kopplingen!',
                    '%s\n\nTraceback:\n%s' % (e.message, traceback.format_exc())))
