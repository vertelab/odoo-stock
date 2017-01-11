# -*- coding: utf-8 -*-
##############################################################################
#
# OpenERP, Open Source Management Solution, third party addon
# Copyright (C) 2016- Vertel AB (<http://vertel.se>).
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
from openerp import http
from openerp.http import request

import logging
_logger = logging.getLogger(__name__)


#~ class stock_picking(models.Model):
    #~ _inherit = "stock.picking"

    #~ qc_id = fields.Many2one(string='Controlled by', comodel_name='hr.employee')

    #~ @api.one
    #~ def _employee_ids(self):
        #~ self.employee_ids = [(6,0,self.move_lines.mapped('employee_id.id'))]
    #~ employee_ids = fields.Many2many(string="Pickers",comodel_name="hr.employee", compute='_employee_ids')


#~ class stock_move(models.Model):
    #~ _inherit = "stock.move"

    #~ employee_id = fields.Many2one(string='Picking employee', comodel_name='hr.employee')


class PrepickingController(http.Controller):

    @http.route(['/prepicking/web/'], type='http', auth='user', website=True)
    def prepicking(self, debug=False, **post):
        if not request.session.uid:
            return http.local_redirect('/web/login?redirect=/prepicking/web')

        return request.render('stock_prepicking.prepicking_index')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
