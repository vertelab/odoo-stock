# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution, third party addon
#    Copyright (C) 2019- Vertel AB (<http://vertel.se>).
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
from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp.addons.web import http
from openerp.http import request, Response
import simplejson
import logging
_logger = logging.getLogger(__name__)

class stock_picking_type(models.Model):
    _inherit = "stock.picking.type"
    @api.multi
    def open_quickmove_interface(self):
        final_url = "/stock/quickmove/pickingtype/%s#focus=quickmove_location_src_id"%self.id
        return {'type': 'ir.actions.act_url', 'url': final_url, 'target': 'self'}

