# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, fields, models
from odoo.osv import expression

from collections import OrderedDict


class StockQuantityHistory(models.TransientModel):
    _name = 'stock.move.consolidation'
    _description = 'Stock Move History'

    date_from = fields.Datetime('From', default=fields.Datetime.now)
    date_to = fields.Datetime('To', default=fields.Datetime.now)

    def stock_move_till_date(self):
        if self.env.context.get('active_ids'):
            move_ids = self.env['stock.move'].browse(self.env.context.get('active_ids'))
        else:
            move_ids = self.env['stock.move'].search([
                ('date', '>=', self.date_from), ('date', '<=', self.date_to), ('state', '=', 'done')
            ])

        print(move_ids)
        items = []
        for rec in move_ids:
            items.append({
                'product_id': rec.product_id.id,
                'location_id': rec.location_id.id,
                'location_dest_id': rec.location_dest_id.id,
                'product_uom_qty': rec.product_uom_qty,
                'product_uom': rec.product_uom.id,
            })

        move_dict = OrderedDict()
        for items in items:
            move_dict.setdefault(
                (
                    items['product_id'],
                    items['location_id'],
                    items['location_dest_id'],
                    items['product_uom'],
                ),
                []).append(items['product_uom_qty'])

        move_dict_items = [
            {
                'product_id': k[0],
                'location_id': k[1],
                'location_dest_id': k[2],
                'product_uom': k[3],
                'product_uom_qty': sum(v)
            }
            for k, v in move_dict.items()
        ]

        for move in move_dict_items:
            move['name'] = 'Stock Move from %s - %s' % (self.date_from, self.date_to)
            self.env['stock.move'].create(move)

