odoo.define('stock_barcode_alternative.PickingEditorWidget', function(require) {
    "use strict";

    var publicWidget = require("web.public.widget");
    var Widget = require('web.Widget');
    var core = require('web.core');
    var PackageEditorWidget = require("stock_barcode_alternative.PackageEditorWidget").PackageEditorWidget;
    var session = require('web.session');

    publicWidget.registry.PickingEditorWidget = publicWidget.Widget.extend({
        template: 'AlternativePickingEditorWidget',

        init: function(parent, options){
            this._super.apply(this, arguments);
            var self = this;
            this.storage = parent.storage;
            this.id = parent.picking_id;
            // Copy picking goals from parent to track current status. Deprecated?
            this.picking_goals = {...parent.picking_goals};
            this.packages = [];
            this.rows = [];
            this.search_filter = "";
            this.current_package = null;
            // This expression adds the Contains selector to jQuery. Not sure if we need it.
            jQuery.expr[":"].Contains = jQuery.expr.createPseudo(function(arg) {
                return function( elem ) {
                    return jQuery(elem).text().toUpperCase().indexOf(arg.toUpperCase()) >= 0;
                };
            });
            this.load_rows();
        },
        renderElement: function(){
            var self = this;
            this._super();
            this.$('button.js_do_transfer').click(this.do_transfer);
            this.$('button.js_pick_done').click(this.do_transfer);
            this.toggle_ui_elements();
            _.each(this.getChildren(), function(child){child.renderElement()});
        },
        start: function(){
            this._super.apply(this, arguments);
            // var self = this;
        },
        load_rows: function(){
            // New plan: save these rows independently of the loaded data in packops.
            // packops = always current backend data.
            // this.rows = our UI data and the current state of the picking operation.
            // Save and load on page reload. Got to connect the data to picking_id when saving.
            var self = this;
            var parent = this.getParent();
            // var parent = JSON.stringify(parent);
            this.load_fields();
            // this.rows = [];
            if (! this.rows) {
                var rows = JSON.parse(JSON.stringify(this.getParent().packops));
                _.each(rows, function(row){
                    row.qty_done = 0.0;
                    row.qty_remaining = row.quantity;
                    if (! row.package_id){
                        row.package_id = {id: null};
                    }
                });
                this.rows = rows;
                this.save('rows');
            }
            if (! this.package_data) {
                var package_data = JSON.parse(JSON.stringify(parent.packages));
                package_data.push({id: null, display_name: 'No Package'})
                _.each(package_data, function(pack){
                    pack.operation_ids = [];
                    _.each(self.rows, function(row) {
                        if (row.package_id.id === pack.id){
                            pack.operation_ids.push(row.id);
                        }
                    });
                });
                this.package_data = package_data;
                this.save('package_data');
            }
            this.packages = [];
            _.each(this.package_data, function(pack){
                self.packages.push(new PackageEditorWidget(self, {package: pack}));
            });
            this.renderElement();
        },
        new_row_id: function(){
            // Returns the next available id for a new row. Always returns an id below 0.
            let id = -1;
            _.each(this.rows, function(row){
                if (row.id <= id){
                    id = row.id - 1;
                }
            });
            return id;
        },
        get_current_package: function(){
            // Return the current package.
            var self = this;
            return _.filter(this.packages, function(e, pos, l){
                return e.id === self.current_package;})[0];
        },
        set_current_package: function(id){
            // UNUSED. Package management not implemented yet.
            // Make this the current package (put all scanned objects into it).
            var old_package = this.get_current_package();
            this.current_package = id;
            this.save('current_package');
            old_package.renderElement();
            this.get_current_package().renderElement();
        },
        get_saved_fields: function(){
            return ['current_package', 'rows', 'package_data'];
        },
        load_fields: function(fields){
            var self = this;
            if (fields === undefined){
                fields = this.get_saved_fields();
            }
            if (! Array.isArray(fields)){
                fields = [fields];
            }
            _.each(fields, function(field){
                self[field] = JSON.parse(self.storage.getItem(field + '_' + self.getParent().picking_id));
            })
        },
        save: function(fields){
            // Save the data in storage.
            var self = this;
            if (fields === undefined){
                fields = this.get_saved_fields();
            }
            if (! Array.isArray(fields)){
                fields = [fields];
            }
            _.each(fields, function(field){
                self.storage.setItem(field + '_' + self.getParent().picking_id, JSON.stringify(self[field]));
            })
        },
        update_remaining: function(product_id){
            // Update the todo on all lines
            var operations = [];
            var total = 0.0;
            // Build list of affected operations (widgets) and total scanned qty
            _.each(this.packages, function(pack){
                _.each(pack.rows, function(row){
                    if (row.data.product_id.id === product_id) {
                        operations.push(row);
                        total += row.data.qty_done;
                    }
                })
            });
            var remaining = this.getParent().picking_goals[product_id] || 0.0;
            remaining -= total;
            _.each(operations, function(operation){
                operation.data.qty_remaining = remaining;
                operation.renderElement();
            });
        },
        get_package_rows: function(package_id){
            // Return all rows for a given package. Package can be
            // null (returns all unpackaged rows).
            //~ var rows = [];
            // TODO: copy this.rows and add ui fluff and stuff like that.
            var filter_function;
            if (package_id) {
                filter_function = function(e, pos, l){ return e.package_id && e.package_id.id === package_id || false;}
            } else {
                filter_function = function(e, pos, l){ return ! e.package_id;}
            }
            return _.filter(this.rows, filter_function);
        },
        delete_row: function(row){
            // Delete a row.
            let i = this.rows.indexOf(row);
            if (i >= 0) {
                this.rows.splice(i, 1);
                this.save('rows');
            }
        },
        split_row: function(id, package_id){
            // UNUSED. Package management not implemented yet.
            //Split one of the products from the given row and put it in the specified package.
            // Give new row a negative id.
        },
        create_package: function(){
            // UNUSED. Package management not implemented yet.
            // Create a new package
        },
        toggle_ui_elements: function(){
            // Enable/disable buttons etc.
            let tb_disabled = this.transfer_button_disabled();
            if (tb_disabled){
                this.$('.js_do_transfer').enable(false);
            } else {
                this.$('.js_do_transfer').enable(true);
            }
            if (this.rest_order_button_disabled(tb_disabled)){
                this.$('.js_pick_done').enable(false);
            } else {
                this.$('.js_pick_done').enable(true);
            }
        },
        transfer_button_disabled: function(){
            // Check if transfer button should be disabled.
            // Disable unless everything has been moved.
            let disabled = false;
            for (let i = 0; i < this.rows.length; i++) {
                if (this.rows[i].qty_remaining > 0){
                    disabled = true;
                    break;
                }
            }
            return disabled;
        },
        rest_order_button_disabled: function(tb_disabled){
            // Check if transfer button should be disabled.
            // Disable unless everything has been moved.
            if (!tb_disabled) {
                return true;
            }
            let disabled = true;
            let zero_done = true;
            for (let i = 0; i < this.rows.length; i++) {
                if (this.rows[i].qty_remaining > 0){
                    disabled = false;
                }
                if (this.rows[i].qty_done > 0){
                    zero_done = false;
                }
            }
            return zero_done ? true:disabled;
        },
        get_backend_url: function (){
            // Return the URL to go to this picking in /web
            // TODO: Add menu and action to the url.
            if (this.getParent().picking) {
                return '/web#id=' + this.id + '&view_type=form&model=stock.picking';
            }
            return '/web#page=0&amp;limit=80&amp;view_type=list&amp;model=stock.picking&amp;active_id=2';
        },
        delete_picking: function(){
            var self = this;
            _.each(self.get_saved_fields(), function(key){ self.storage.removeItem(key + '_' + self.id)})
        },
        get_extra_transfer_data: function(){
            return {context: JSON.parse(JSON.stringify(session.user_context))};
        },
        do_transfer: function(){
            // Complete the picking process.
            var self = this;
            return this._rpc({
                model: 'stock.picking',
                method: 'abc_do_transfer',
                args: [[this.id], this.rows, this.display_manual_packages],
                // args: [[this.id, this.rows, this.package_data], this.get_extra_transfer_data()],
                // context: this.get_extra_transfer_data()
            }).then(function (res) {
                self.transfer_done(res)
            });

            // new instance.web.Model('stock.picking')
            //     .call('abc_do_transfer', [this.id, this.rows, this.package_data], this.get_extra_transfer_data())
            //     .then(function(result){self.transfer_done(result)});
        },
        transfer_done: function(result){
            var self = this;

            _.each(result.messages, function(message) {
                self.getParent().log_message(message);
            });
            _.each(result.warnings, function(warning) {
                var details = warning[0] + '\n\n' + warning[1];
                self.getParent().log_message(warning[0], 'warning', details);
                window.alert(details);
            });
            if (result.results.transfer === 'success'){
                this.delete_picking();
                _.each(this.packages, function(pack){
                    pack.destroy();
                });
            }
        },
        has_product: function(product_id){
            // Check if the given product is on this picking
            return _.filter(this.rows, function(e, pos, l){
                return e.product_id.id === product_id;
            }).length > 0;
        },
        get_weight: function(){
            let weight = 0.0;
            _.each(this.packages, function(pack){
                weight += pack.get_weight();
            })
            return weight;
        }
    });


    return publicWidget.registry.PickingEditorWidget;

});
