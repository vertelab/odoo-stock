# -*- coding: utf-8 -*-

from odoo import models, fields, api
# ~ from odoo.addons.stock.models.stock import StockQuant as OriginalStockQuant

class StockQuant(models.Model):
    _inherit = 'stock.quant'
    def _get_removal_strategy_order(self, removal_strategy):
        if removal_strategy == 'fipo':
            return "(SELECT stock_location.priority FROM stock_location WHERE stock_location.id = stock_quant.location_id)"
        return super(StockQuant, self)._get_removal_strategy_order(removal_strategy)
    
    
class Location(models.Model):
    _inherit = "stock.location"
    priority = fields.Integer(string = "Picking Priority", help = "Set picking priority of location. Lower values gets picked first. Null gets picked last")

