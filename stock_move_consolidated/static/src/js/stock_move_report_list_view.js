odoo.define('stock_move_consolidated.ConsolidatedStockMoveListView', function (require) {
    "use strict";

    var ListView = require('web.ListView');
    var ConsolidatedStockMoveListController = require('stock_move_consolidated.ConsolidatedStockMoveListController');
    var viewRegistry = require('web.view_registry');

    var ConsolidatedStockMoveListView = ListView.extend({
        config: _.extend({}, ListView.prototype.config, {
            Controller: ConsolidatedStockMoveListController,
        }),
    });

    viewRegistry.add('stock_move_line_report_list', ConsolidatedStockMoveListView);

    return ConsolidatedStockMoveListView;

});
