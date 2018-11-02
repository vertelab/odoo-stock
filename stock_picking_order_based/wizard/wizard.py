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
from odoo import models, fields, api, _

import logging
_logger = logging.getLogger(__name__)


class StockPickingOrderBasedWizard(models.TransientModel):
    _name = 'stock.picking.order.based.wizard'

    source_location_id = fields.Many2one(comodel_name='stock.location', string='Source Location Zone')
    dest_location_id = fields.Many2one(comodel_name='stock.location', string='Destination Location Zone')
    period_start = fields.Date(string='Period Start')
    period_stop = fields.Date(string='Period Stop')

    @api.model
    def make_picking(self):
        pass
