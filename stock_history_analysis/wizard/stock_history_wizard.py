# -*- coding: utf-8 -*-
##############################################################################
#
# Odoo, Open Source Management Solution, third party addon
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

from openerp import tools
from openerp import models, fields, api, _
import logging
_logger = logging.getLogger(__name__)

class wizard_history_analysis(models.TransientModel):
    _name = 'wizard.history.analysis'
    _description = 'Wizard that opens the stock history analysis table'

    choose_date = fields.Boolean(string='Choose a Date interval', default=False)
    date_start = fields.Datetime(string='Date Start', required=True, default=fields.Datetime.now)
    date_stop = fields.Datetime(string='Date Stop', required=True, default=fields.Datetime.now)

    @api.v7
    def open_table(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        data = self.read(cr, uid, ids, context=context)[0]
        ctx = context.copy()
        _logger.warn(ctx)
        ctx['history_date'] = data['date_stop']
        ctx['search_default_group_by_product'] = True
        ctx['search_default_group_by_location'] = True
        return {
            'domain': "[('date', '<=', '%s'), ('date', '>=', '%s')]" %(data['date_stop'], data['date_start']) if self.choose_date else '[]',
            'name': _('Stock History Value At Date'),
            'view_type': 'form',
            'view_mode': 'graph',
            'res_model': 'stock_history.report',
            'type': 'ir.actions.act_window',
            'context': ctx,
        }


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
