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

class stock_history_report(models.Model):
    _name = "stock_history.report"
    _description = "Stock History Statistics"
    _auto = False
    _rec_name = 'date'
    _order = 'date desc'

    quant_id = fields.Many2one(comodel_name='stock.quant', string='Stock Quant', readonly=True)
    date = fields.Datetime(string='Date Created', readonly=True)
    product_id = fields.Many2one(comodel_name='product.product',string='Product', readonly=True)
    quantity = fields.Float(string='Product Quantity', readonly=True)
    location_id = fields.Many2one(comodel_name='stock.location', string='Location', readonly=True)
    quant_location_id = fields.Many2one(comodel_name='stock.location', string='Quant Location', readonly=True)
    company_id = fields.Many2one(comodel_name='res.company', string='Company', readonly=True)
    product_categ_id = fields.Many2one(comodel_name='product.category',string='Category of Product', readonly=True)
    nbr_lines = fields.Integer(string='# of Lines', readonly=True)
    source = fields.Char(string='Source', readonly=True)
    product_inventory_value = fields.Float(string='Inventory Value (FIFO)', readonly=True)
    cost_price = fields.Float(string='Inventory Value (cost price)', readonly=True)
    #~ replacement_value = fields.Float(string='Inventory Value (replacement)', readonly=True)
    move_id = fields.Many2one(comodel_name='stock.move', string='Stock Move', readonly=True)
    price_unit_on_quant = fields.Float(string='Value', readonly=True)
    #~ standard_price = fields.Float(string='Cost Price', readonly=True)
    #~ max_price = fields.Float(string='Max price', readonly=True)

    def init(self, cr):
        # self._table = sale_report

        #~ max(price_unit_on_quant) as max_price,
        #~ sum(max_price * quantity) as replacement_value,

        tools.drop_view_if_exists(cr, self._table)
        cr.execute("""
            CREATE OR REPLACE VIEW stock_history_report AS (
              SELECT MIN(id) as id,
                date,
                move_id,
                quant_id,
                location_id,
                quant_location_id,
                company_id,
                product_id,
                product_categ_id,
                SUM(quantity) as quantity,
                count(*) as nbr_lines,
                COALESCE(SUM(price_unit_on_quant * quantity) / NULLIF(SUM(quantity), 0), 0) as price_unit_on_quant,
                sum(standard_price * quantity) as cost_price,
                sum(price_unit_on_quant * quantity) as product_inventory_value,

                source
                FROM
                ((SELECT
                    stock_move.id AS id,
                    stock_move.id AS move_id,
                    dest_location.id AS location_id,
                    quant_location.id AS quant_location_id,
                    dest_location.company_id AS company_id,
                    stock_move.product_id AS product_id,
                    product_template.categ_id AS product_categ_id,
                    quant.qty AS quantity,
                    quant.id AS quant_id,
                    stock_move.date AS date,
                    quant.cost as price_unit_on_quant,
                    product_product.standard_price as standard_price,
                    stock_move.origin AS source
                FROM
                    stock_move
                JOIN
                    stock_quant_move_rel on stock_quant_move_rel.move_id = stock_move.id
                JOIN
                    stock_quant as quant on stock_quant_move_rel.quant_id = quant.id
                JOIN
                    stock_location dest_location ON stock_move.location_dest_id = dest_location.id
                JOIN
                    stock_location source_location ON stock_move.location_id = source_location.id
                JOIN
                    stock_location quant_location ON quant.location_id = quant_location.id
                JOIN
                    product_product ON product_product.id = stock_move.product_id
                JOIN
                    product_template ON product_template.id = product_product.product_tmpl_id
                WHERE quant.qty>0 AND stock_move.state = 'done' AND dest_location.usage in ('internal', 'transit')
                  AND (
                    not (source_location.company_id is null and dest_location.company_id is null) or
                    source_location.company_id != dest_location.company_id or
                    source_location.usage not in ('internal', 'transit'))
                group by stock_move.id,
                    dest_location.id,
                    quant_location.id,
                    quant.id,
                    dest_location.company_id,
                    stock_move.product_id,
                    product_template.categ_id,
                    quant.qty,
                    stock_move.date,
                    quant.cost,
                    product_product.standard_price,
                    source_location.id
                ) UNION ALL
                (SELECT
                    (-1) * stock_move.id AS id,
                    quant.id AS quant_id,
                    stock_move.id AS move_id,
                    source_location.id AS location_id,
                    quant_location.id AS quant_location_id,
                    source_location.company_id AS company_id,
                    stock_move.product_id AS product_id,
                    product_template.categ_id AS product_categ_id,
                    - quant.qty AS quantity,
                    stock_move.date AS date,
                    quant.cost as price_unit_on_quant,
                    product_product.standard_price as standard_price,
                    stock_move.origin AS source
                FROM
                    stock_move
                JOIN
                    stock_quant_move_rel on stock_quant_move_rel.move_id = stock_move.id
                JOIN
                    stock_quant as quant on stock_quant_move_rel.quant_id = quant.id
                JOIN
                    stock_location source_location ON stock_move.location_id = source_location.id
                JOIN
                    stock_location dest_location ON stock_move.location_dest_id = dest_location.id
                JOIN
                    stock_location quant_location ON quant.location_id = quant_location.id
                JOIN
                    product_product ON product_product.id = stock_move.product_id
                JOIN
                    product_template ON product_template.id = product_product.product_tmpl_id
                WHERE quant.qty>0 AND stock_move.state = 'done' AND source_location.usage in ('internal', 'transit')
                 AND (
                    not (dest_location.company_id is null and source_location.company_id is null) or
                    dest_location.company_id != source_location.company_id or
                    dest_location.usage not in ('internal', 'transit'))
                group by stock_move.id,
                    dest_location.id,
                    quant_location.id,
                    quant.id,
                    dest_location.company_id,
                    stock_move.product_id,
                    product_template.categ_id,
                    quant.qty,
                    stock_move.date,
                    quant.cost,
                    product_product.standard_price,
                    source_location.id
                ))
                AS foo
                GROUP BY move_id, location_id, quant_location_id, company_id, product_id, product_categ_id, date, price_unit_on_quant, quant_id, source
            )""")
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
