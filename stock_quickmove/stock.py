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
from openerp.http import request
import logging
_logger = logging.getLogger(__name__)


class StockSquickMove(http.Controller):

    @http.route(['/stock/quickmove'], type='http', auth='user', website=True)
    def stock_quickmove(self, **post):
        if request.httprequest.method == 'POST':
            _logger.warn(post)
        return request.website.render('stock_quickmove.webapp', {'picking_type': post.get('picking_type' or '')})

    @http.route(['/stock/quickmove_barcode'], type='json', auth='user', website=True)
    def quickmove_barcode(self, barcode='', location_src_scanned=False, **kw):
        # search EAN13
        _logger.warn(request.env.context)
        product_ids = request.env['product.product'].search([('ean13', '=', barcode)])
        if len(product_ids) > 0:
            products = []
            for p in product_ids:
                products.append([p.id, '%s %s' %(p.name, ','.join([a.name for a in p.attribute_value_ids]))])
            return {'type': 'product', 'product_ids': products}
        else:
            if not location_src_scanned:
                # search sorce location
                src_location_ids = request.env['stock.location'].search([('name', '=', barcode)])
                if len(src_location_ids) > 0:
                    src_location_id = src_location_ids[0]
                    product_ids = request.env['product.product'].search([('stock_location_id', '=', src_location_id.id)])
                    products = []
                    for p in product_ids:
                        products.append([p.id, '%s %s' %(p.name, ','.join([a.name for a in p.attribute_value_ids]))])
                    return {'type': 'src_location', 'product_ids': products, 'location': {'id': src_location_id.id, 'name': src_location_id.display_name}}
            else:
                # search destination location
                dest_location_ids = request.env['stock.location'].search([('name', '=', barcode)])
                if len(dest_location_ids) > 0:
                    dest_location_id = dest_location_ids[0]
                    return {'type': 'dest_location', 'location': {'id': dest_location_id.id, 'name': dest_location_id.display_name}}
