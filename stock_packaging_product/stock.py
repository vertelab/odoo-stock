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

import logging
_logger = logging.getLogger(__name__)

class stock_package(models.Model):
    
    _inherit = "stock.quant.package"
    
    parent_id = fields.Many2one('stock.quant.package', 'Parent Package', help="The package containing this item", ondelete='restrict', readonly=False)

class product_ul(models.Model):
    _inherit = 'product.ul'
    
    product_id = fields.Many2one('product.product', 'Packaging Product')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
