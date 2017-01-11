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

import openerp.exceptions
from openerp.exceptions import except_orm, Warning, RedirectWarning,MissingError
from openerp import models, fields, api, _

import logging
_logger = logging.getLogger(__name__)


class stock_picking(models.Model):
    _inherit = "stock.picking"
    
    prepicked = fields.Boolean('Prepicked', compute='_get_prepicked', store=True)
    
    @api.one
    @api.depends('move_lines', 'state', 'move_lines.prepicked', 'move_lines.product_uom_qty')
    def _get_prepicked(self):
        if self.state != 'assigned':
            self.prepicked = False
            return
        for line in self.move_lines:
            if line.prepicked != line.product_uom_qty:
                self.prepicked = False
                return
        self.prepicked = True

class stock_move(models.Model):
    _inherit = "stock.move"
    
    prepicked = fields.Float('To be picked')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
