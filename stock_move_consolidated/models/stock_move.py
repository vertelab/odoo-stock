from odoo import models, api, fields, _


class StockMove(models.Model):
    _inherit = 'stock.move.line'

    @api.model
    def _get_move_line_action(self):
        """ Returns an action to open quant view.
        Depending of the context (user have right to be inventory mode or not),
        the list view will be editable or readonly.

        :param domain: List for the domain, empty by default.
        :param extend: If True, enables form, graph and pivot views. False by default.
        """
        ctx = dict(self.env.context or {})
        action = {
            'name': _('Stock Move'),
            'view_type': 'tree',
            'view_mode': 'list,form',
            'res_model': 'stock.move.line',
            'type': 'ir.actions.act_window',
            'context': ctx,
            'domain': [],
            'help': """
                    <p class="o_view_nocontent_empty_folder">No Stock Move</p>
                    <p>This analysis gives you an overview of the current stock
                    move of your products.</p>
                    """
        }

        action.update({
            'view_mode': 'tree,form,kanban,pivot',
            'views': [
                (False, 'list'),
                (False, 'form'),
                (False, 'kanban'),
                (False, 'pivot')
            ],
        })
        return action

    # @api.model
    # def action_view_quants(self):
    #     self = self.with_context(search_default_internal_loc=1)
    #     if not self.user_has_groups('stock.group_stock_multi_locations'):
    #         company_user = self.env.company
    #         warehouse = self.env['stock.warehouse'].search([('company_id', '=', company_user.id)], limit=1)
    #         if warehouse:
    #             self = self.with_context(default_location_id=warehouse.lot_stock_id.id)
    #
    #     # If user have rights to write on quant, we set quants in inventory mode.
    #     if self.user_has_groups('stock.group_stock_manager'):
    #         self = self.with_context(inventory_mode=True)
    #     return self._get_quants_action(extend=True)

    #
    # def action_view_stock_moves(self):
    #     self.ensure_one()
    #     action = self.env["ir.actions.actions"]._for_xml_id("stock.stock_move_line_action")
    #     action['domain'] = [
    #         ('product_id', '=', self.product_id.id),
    #         '|',
    #         ('location_id', '=', self.location_id.id),
    #         ('location_dest_id', '=', self.location_id.id),
    #         ('lot_id', '=', self.lot_id.id),
    #         '|',
    #         ('package_id', '=', self.package_id.id),
    #         ('result_package_id', '=', self.package_id.id),
    #     ]
    #     return action
