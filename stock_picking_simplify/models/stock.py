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
from odoo import models, fields, api, _

import logging
_logger = logging.getLogger(__name__)

class StockPicking(models.Model):
    _inherit = 'stock.picking'
    
    @api.one
    def action_set_qty_done(self):
        if self.state in ('assigned', 'partially_available'):
            self.pack_operation_product_ids._action_set_qty_done(True)

class StockPackOperation(models.Model):
    _inherit = 'stock.pack.operation'
    
    @api.one
    def action_set_qty_done(self):
        self._action_set_qty_done()
    
    @api.one
    def _action_set_qty_done(self, confirm_only=False):
        if self.state in ('assigned', 'partially_available') and not self.result_package_id:
            if self.qty_done < self.product_qty:
                self.qty_done = self.product_qty
            elif not confirm_only and self.qty_done == self.product_qty:
                self.qty_done = 0
