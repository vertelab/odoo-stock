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
from openerp import models, fields, api, _

import logging
_logger = logging.getLogger(__name__)


class product_product(models.Model):
    _inherit="product.product"
    picking_comment = fields.Text(String='Comment', help="Add instructions for picking")


    # picking_comment = fields.Text(String='Comment', help="Add instructions for picking")
    def picking_comment(self):
	    product = self.env['product.template'].search_read(fields=['name', 'dv_ribbon','is_offer_product_reseller', 'is_offer_product_consumer','dv_image_src', 'product_variant_count'])
	    pricelist = self.env['product.pricelist'].sudo().browse(pricelist)
	    
	    if (product['is_offer_product_reseller'] and pricelist.for_reseller == True) or (product['is_offer_product_consumer'] and pricelist.for_reseller == False): 
	    	picking_comment_offer = fields.Text(String='Comment', help="Add instructions for picking")


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
