# -*- coding: utf-8 -*-

from odoo import models, fields, api

import logging
_logger = logging.getLogger(__name__)
# ~ Känns jätte dumt att det behöver finnas två stycken min_num_of_packages. En i template.product och en i product.product. 
# ~ Men så är det gjort med t,ex volume. usr/share/core-odoo/addons/product/models/product.py och sftp://odoo14/usr/share/core-odoo/addons/product/models/product_template.py
# ~ Gjort så här så att jag kan visa ett fält för templaten och för varianterna av en produkt.

class BufferPickLogicProduct(models.Model):
    _inherit = "product.product"
    min_num_of_packages= fields.Integer('Buffert Picking threshold', 
    help="Det här är summan produkter som måste beställas för att buffert plock ska köras, Alltså att det plockas i första hand bara från locations som är markerade som \"buffer location\". Sedan byts dessa varor ut från locations med ädre produkter ifall dessa varor finns.")

# ~ class BufferPickLogicTemplate(models.Model):
    # ~ _inherit = "product.template"
    # ~ min_num_of_packages_template = fields.Integer('Buffert Picking threshold', 
    # ~ help="Det här är summan produkter som måste beställas för att buffert plock ska köras, Alltså att det plockas i första hand bara från locations som är markerade som \"buffer location\". Sedan byts dessa varor ut från locations med ädre produkter ifall dessa varor finns.")
    
class Location(models.Model):
    _inherit = "stock.location"
    BufferLocation = fields.Boolean(string="Is a Buffer Locaction", default=False)
    
# ~ [{'id': 2079, 'name': 'Solkräm', 'sequence': 10, 'priority': '0', 'create_date': datetime.datetime(2021, 6, 2, 11, 23, 11, 903306), 'date': datetime.datetime(2021, 6, 2, 11, 23, 11), 'date_deadline': datetime.datetime(2021, 6, 2, 11, 23, 11), 'company_id': (1, 'MARIA ÅKERBERG AB'), 'product_id': (93, 'Solkräm'), 'description_picking': 'Solkräm', 'product_qty': 1.0, 'product_uom_qty': 1.0, 'product_uom': (1, 'Units'), 'product_uom_category_id': (1, 'Unit'), 'product_tmpl_id': (81, 'Solkräm'), 'location_id': (8, 'WH/Stock'), 'location_dest_id': (5, 'Partner Locations/Customers'), 'partner_id': (10, 'Deco Addict'), 'move_dest_ids': [], 'move_orig_ids': [], 'picking_id': (840, 'WH/P/00214'), 'picking_partner_id': (10, 'Deco Addict'), 'note': False, 'state': 'confirmed', 'price_unit': 0.0, 'backorder_id': False, 'origin': 'S00226', 'procure_method': 'make_to_stock', 'scrapped': False, 'scrap_ids': [], 'group_id': (472, 'S00226'), 'rule_id': (5, 'WH: Stock → Customers (MTO)'), 'propagate_cancel': False, 'delay_alert_date': False, 'picking_type_id': (2, 'Lager: Orderplock'), 'inventory_id': False, 'move_line_ids': [], 'move_line_nosuggest_ids': [], 'origin_returned_move_id': False, 'returned_move_ids': [], 'reserved_availability': 0.0, 'availability': 1.0, 'restrict_partner_id': False, 'route_ids': [], 'warehouse_id': (1, 'Lager'), 'has_tracking': 'none', 'quantity_done': 0.0, 'show_operations': True, 'show_details_visible': False, 'show_reserved_availability': True, 'picking_code': 'outgoing', 'product_type': 'product', 'additional': False, 'is_locked': True, 'is_initial_demand_editable': False, 'is_quantity_done_editable': False, 'reference': 'WH/P/00214', 'has_move_lines': False, 'package_level_id': False, 'picking_type_entire_packs': True, 'display_assign_serial': False, 'next_serial': False, 'next_serial_count': 0, 'orderpoint_id': False, 'forecast_availability': 1.0, 'forecast_expected_date': False, 'lot_ids': [], 'created_production_id': False, 'production_id': False, 'raw_material_production_id': False, 'unbuild_id': False, 'consume_unbuild_id': False, 'allowed_operation_ids': [], 'operation_id': False, 'workorder_id': False, 'bom_line_id': False, 'byproduct_id': False, 'unit_factor': 1.0, 'is_done': False, 'order_finished_lot_ids': [], 'should_consume_qty': 0.0, 'use_expiration_date': False, 'to_refund': False, 'account_move_ids': [], 'stock_valuation_layer_ids': [], 'purchase_line_id': False, 'created_purchase_line_id': False, 'sale_line_id': (285, 'S00226 - Solkräm'), 'weight': 0.0, 'display_name': 'S00226/Stock>Customers', 'create_uid': (1, 'OdooBot'), 'write_uid': (1, 'OdooBot'), 'write_date': datetime.datetime(2021, 6, 2, 11, 23, 11, 903306), '__last_update': datetime.datetime(2021, 6, 2, 11, 23, 11, 903306)}] 

class StockMove(models.Model):
    _inherit = "stock.move"
    
    def _action_assign(self):
        for move in self.filtered(lambda m: m.state in ['confirmed', 'waiting', 'partially_available']):
            _logger.warning(f"jakmar inherit {move.read()}")
            quantity = move.product_qty
            _logger.warning(f"jakmar inherit product{quantity}")
            package = move.product_id.packaging_ids
            _logger.warning(f"jakmar inherit package{package}")
            buffer_threshold = move.product_id.min_num_of_packages
            _logger.warning(f"jakmar inherit min_num{buffer_threshold}")
            package_quantity = package[0].qty
            _logger.warning(f"jakmar inherit package_quant {package_quantity}")
            if quantity >= package_quantity * buffer_threshold:
                _logger.warning(f"jakmar inherit buffer picking logic = true")
        super(StockMove,self)._action_assign()
            # ~ quantity = product
            # ~ package = move.product_id.packaging_ids
            # ~ package_quantity
            # ~ buffer_thersold 

            # ~ _logger.warning(f"jakmar {product1.read()}")
            # ~ _logger.warning(f"jakmar {self.product_id.packaging_ids}")
    
     
