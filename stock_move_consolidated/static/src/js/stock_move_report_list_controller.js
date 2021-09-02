odoo.define('stock_move_consolidated.ConsolidatedStockMoveListController', function (require) {
    "use strict";

    var ListController = require('web.ListController');
    var core = require('web.core');
    var qweb = core.qweb;

    var ConsolidatedStockMoveListController = ListController.include({
        renderButtons: function ($node) {
            this._super.apply(this, arguments);

            if (this.modelName === "stock.move") {
                var $buttonToDate = $(qweb.render('ConsolidatedStockMove.Buttons'));
                $buttonToDate.on('click', this._onOpenWizard.bind(this));
                this.$buttons.prepend($buttonToDate);
            }
        },

        _onOpenWizard: function () {
            var state = this.model.get(this.handle, {raw: true});
            var stateContext = state.getContext();
            var context = {
                active_model: this.modelName,
            };
            if (stateContext.default_product_id) {
                context.product_id = stateContext.default_product_id;
            } else if (stateContext.product_tmpl_id) {
                context.product_tmpl_id = stateContext.product_tmpl_id;
            }
            this.do_action({
                res_model: 'stock.move.consolidation',
                views: [[false, 'form']],
                target: 'new',
                type: 'ir.actions.act_window',
                context: context,
            });
        },
    });

    return ConsolidatedStockMoveListController;
});
