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
from openerp import models, fields, api, _

import logging
_logger = logging.getLogger(__name__)

JOURNAL_TYPE_MAP = {
    ('outgoing', 'customer'): ['sale'],
    ('outgoing', 'supplier'): ['purchase_refund'],
    ('outgoing', 'transit'): ['sale', 'purchase_refund'],
    ('incoming', 'supplier'): ['purchase'],
    ('incoming', 'customer'): ['sale_refund'],
    ('incoming', 'transit'): ['purchase', 'sale_refund'],
}

class stock_pack_operation(models.Model):
    _inherit = 'stock.pack.operation'

    @api.one
    def action_drop_down(self):
        super(stock_pack_operation, self).action_drop_down()
        if self.picking_id.sale_id.order_policy == 'picking':
            if self.picking_id.state == 'done' or self.picking_id.invoice_state == '2binvoiced':
                return self.create_invoice_from_barcode_ui()
            elif self.picking_id.invoice_state == 'invoiced':
                return [self.env['account.invoice'].search([('picking_id', '=', self.picking_id.id)])[0].id]

    @api.one
    def create_invoice_from_barcode_ui(self):
        '''
            Create invoice from Barcode interface
        '''
        res = self.picking_id.action_invoice_create(
              journal_id = self._get_journal(),
              group = True,
              type = {'sale':'out_invoice', 'purchase':'in_invoice', 'sale_refund':'out_refund', 'purchase_refund':'in_refund'}.get(self._get_journal_type(), 'out_invoice'))
        return res

    @api.model
    def _get_journal(self):
        journals = self.env['account.journal'].search([('type', '=', self._get_journal_type())])
        return journals[0].id if journals else False

    @api.model
    def _get_journal_type(self):
        type = self.picking_id.picking_type_id.code
        usage = self.picking_id.move_lines[0].location_id.usage if type == 'incoming' else self.picking_id.move_lines[0].location_dest_id.usage
        return JOURNAL_TYPE_MAP.get((type, usage), ['sale'])[0]


#~ class account_invoice(models.Model):
    #~ _inherit = 'account.invoice'

    #~ @api.model
    #~ def do_print_invoice(self, inv_id):
        #~ '''This function prints the invoice created in barcode ui'''
        #~ return self.env['report'].get_action(self.browse([int(i) for i in inv_id]), 'account.report_invoice')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
