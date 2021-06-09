odoo.define('stock_barcode_alternative.PackageEditorWidget', function(require) {
    "use strict";

    var session = require('web.session');
    var Widget = require('web.Widget');
    var OperationEditorWidget = require("stock_barcode_alternative.OperationEditorWidget").OperationEditorWidget;

    var PackageEditorWidget = Widget.extend({
        template: 'AlternativePackageEditorWidget',

        init: function(parent, options){
            this._super.apply(this, arguments);
            var self = this;
            // this.data contains pure data ({}, [], strings, integers, floats etc) describing this package, destined for storage.
            // We reuse the provided object to keep all the data up to date on PickingEditorWidget (the same object is in that structure, so all changes are automatically mirrored there).
            // Any instantiated widgets or similar objects should be stored on this, not in data.
            this.data = options.package;
            this.id = this.data.id;
            // Filter out the packops belonging to this package.
            var rows = _.filter(parent.rows, function(e, pos, l){
                return self.data.operation_ids.indexOf(e.id) > -1;
            });
            this.rows = [];
            // // Instantiate a widget for each packop.

            _.each(rows, function(row){
                var row_widget = new OperationEditorWidget(self, {row: row});
                self.rows.push(row_widget);
            });
            // self.reorder_rows();
            self.reorder_rows(this.data.operation_ids);

        },
        renderElement: function(){
            var self = this;
            this.setElement(self.getParent().$('tbody.abc-packop-package[data-package-id="' + this.id + '"]'));
            this._super();
            _.each(this.getChildren(), function(child){child.renderElement()});
        },
        start: function(){
            this._super.apply(this, arguments);
            var self = this;
            //~ console.log('PackageEditorWidget.start');
        },
        get_picking_widget: function() {
            return this.getParent();
        },
        reorder_rows: function(packop_id){
            // Reorder the rows. Put packop_id first if specified.
            this.rows.sort(function(el1, el2){
                if (el1.id === packop_id) {
                    return -1;
                } else if (el2.id === packop_id) {
                    return 1;
                }
                // Calculate row weights for sorting. -1 (red), 1 (yellow), or 2 (green)
                let weight1 = el1.data.qty_remaining === 0 ? 2 : el1.data.qty_remaining / Math.abs(el1.data.qty_remaining);
                let weight2 = el2.data.qty_remaining === 0 ? 2 : el2.data.qty_remaining / Math.abs(el2.data.qty_remaining);
                if (weight1 < weight2){
                    return -1;
                } else if (weight1 > weight2){
                    return 1;
                }
                return 0;
            });
            let operation_ids = [];
            _.each(this.rows, function(row){
                operation_ids.push(row.id);
            })
            this.data.operation_ids = operation_ids;
            this.renderElement();
        },
        remove_row: function(row){
            // Remove a row from this package.
            let i = this.rows.indexOf(row);
            if (i >= 0) {
                this.rows.splice(i, 1);
            }
            i = this.data.operation_ids.indexOf(row.id);
            if (i >= 0) {
                this.data.operation_ids.splice(i, 1);
            }
            // Save changes to package data
            this.get_picking_widget().save('package_data')
        },
        increase: function(product_id, limit_qty=false){
            // Increase quantity of the row containing the given product_id.
            // limit_qty: set to true to avoid increasing over expected qty.
            // Called from the scanner.
            //~ console.log('PackageEditorWidget(' + this.id + ').increase: ' + product_id, this);
            var self = this;
            var rows = _.filter(this.rows, function(e, pos, l){
                return e.data.product_id.id === product_id;
            });
            if (rows.length > 0) {
                var done = false;
                var row;
                _.each(rows, function(r){
                    if (done){return}
                    if (r.data.qty_remaining > 0){
                        // row is not done, so we will use it
                        row = r;
                        done = true;
                    } else if (!row && !limit_qty){
                        // row is done. remember it in case all rows are done.
                        row = r;
                    }
                });
                if (row){
                    row.increase(true);
                    return true;
                }
            } else {
                // Find and split/move original row onto this package.
                // TODO: Handle existing rows on other packages.

                // Create a new row.
                let picking_editor = self.getParent();
                let row_data = {
                        'id': picking_editor.new_row_id(),
                        'result_package_id': self.id,
                        'package_id': {'id': self.id},
                        'packop_id': null,
                        'lot_id': null,
                        'product_id': product_id,
                        'is_offer': product_id['is_offer'],
                        'quantity': 0.0,
                        'qty_done': 1.0,
                        'qty_remaining': -1.0
                    };
                //~ console.log('Lukas2', row_data)

                return this._rpc({
                    model: 'stock.picking',
                    method: 'abc_create_row',
                    args: [[], this.picking_id],
                    context: session.user_context
                }).then(function (result) {
                    picking_editor.rows.unshift(result);
                    self.data.operation_ids.unshift(result.id)
                    picking_editor.save('rows');
                    picking_editor.save('package_data');
                    var row_widget = new OperationEditorWidget(self, {row: result});
                    self.rows.push(row_widget);
                    self.renderElement();
                });

                // new instance.web.Model('stock.picking')
                //     .call('abc_create_row', [picking_editor.id, row_data])
                //     .then(function(result){
                //         picking_editor.rows.unshift(result);
                //         self.data.operation_ids.unshift(result.id)
                //         picking_editor.save('rows');
                //         picking_editor.save('package_data');
                //         var row_widget = new module.OperationEditorWidget(self, {row: result});
                //         self.rows.push(row_widget);
                //         self.renderElement();
                //     });
                //~ console.log('Lukas2', row_data)
                // return true;
            }
            return false;
        },
        selected: function(){
            return this.id === this.get_picking_widget().current_package;
        },
        get_weight: function(){
            // Calculate the weight of this package
            // TODO: Add support for different UoMs. Waht UoM is qty_done in?
            // TODO: Add support for packaging weight.
            let weight = 0.0;
            let self = this;
            //~ console.log(this);
            _.each(this.rows, function(row){
                let product = row.get_product();
                //~ console.log('Haze weight', product)
                weight += row.data.qty_done * product.weight;
            })
            return weight;
        }
    });

    return {
        PackageEditorWidget: PackageEditorWidget
    }

});
