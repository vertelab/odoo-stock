odoo.define('stock_barcode_alternative.OperationEditorWidget', function(require) {
    "use strict";

    var config = require('web.config');
    var core = require('web.core');
    var mixins = require('web.mixins');
    var session = require('web.session');
    var Widget = require('web.Widget');

    var OperationEditorWidget = Widget.extend({
        template: 'AlternativeOperationEditorWidgets',

        init: function(parent, options){
            this._super.apply(this, arguments);
            var self = this;
            // this.data contains pure data (JSONifiable stuff like {}, [], strings, integers, floats etc) describing this packop, destined for storage.
            // We reuse the provided object to keep all the data up to date on PickingEditorWidget (the same object is in that structure, so all changes are automatically mirrored there).
            // Any instantiated widgets or similar objects should be stored on this, not in data.
            this.data = options.row;
            this.id = this.data.id;
        },
        renderElement: function(){
            var self = this;
            this.setElement(self.getParent().$('tr.abc-packop').attr('data-id', this.id));
            // this.setElement(self.getParent().$('tr.abc-packop[data-id="' + this.id + '"]'));
            this._super();
            console.log(this);
            this.$('i.abc-op-qty-plus').click(function(){self.increase()});
            this.$('i.abc-op-qty-minus').click(function(){self.decrease()});
            this.$('i.abc-op-maximize-qty').click(function(){self.maximize_qty()});
            //
            this.$('input.js_qty').change(function(){self.set_qty(parseFloat(this.value))});
            _.each(this.getChildren(), function(child){child.renderElement()});
        },
        start: function(){
            this._super.apply(this, arguments);
            var self = this;
        },
        get_picking_widget: function() {
            return this.getParent().get_picking_widget();
        },
        set_package: function(){
            // Not finished and unused.
            var old_parent = this.getParent();
            var old_package = null; //TODO
            this.setParent();
        },
        maximize_qty: function(){
            // Add the remaining planned quantity to this line
            this.set_qty(this.data.quantity_done + this.data.qty_remaining);
        },
        increase: function(reorder){
            this.set_qty(this.data.quantity_done + 1, reorder);
        },
        decrease: function(reorder){
            this.set_qty(this.data.quantity_done - 1, reorder);
        },
        get_classes: function(){
            var self = this;
            // Return the classes decorating this row in the UI
            var classes = 'abc-packop';

            let ui = this.get_picking_widget().getParent();
            if(ui.products){
                _.each(ui.products, function(product){
                    if(product.id === self.data.product_id.id){
                        if(product){
                            self.data['quantity_done'] = self.data['quantity'];
                            console.log('QTY', self.data['quantity_done'])
                            self.data.qty_remaining = 0;
                            classes += ' hidden';
                        }
                    }

                })
            }

            if (this.data.qty_remaining < 0) {
                classes += ' qty-over';
            } else if (this.data.qty_remaining === 0) {
                classes += ' finished';
            } else if (this.data.quantity_done > 0) {
                classes += ' unfinished';
            }


            if (this.newly_scanned) {
                // This is the most recently scanned line. Mark it as such for CSS.
                classes += ' abc_newly_scanned';
                this.newly_scanned = false;
            }
            return classes;
        },
        set_qty: function(qty, reorder){
            // Update quantity for this row.
            // qty: the new quantity
            // reorder: boolean. set to true to reorder te rows

            if (qty === NaN) {
                qty = 0.0;
            } else if (qty < 0.0) {
                qty = 0.0;
            }
            if (qty === this.data.quantity_done) {
                // Nothing has changed.
                return;
            }
            this.data.quantity_done = qty;
            var picking = this.get_picking_widget()
            picking.update_remaining(this.data.product_id.id);
            var parent = this.getParent();
            var picking = this.get_picking_widget();
            if (this.data.quantity_done === 0.0){
                if (this.id < 0) {
                    // Not original row. Should this matter? We don't
                    // reuse the same picking wizard anyway. Lets keep it this way for now.
                    // TODO: Delete row
                    parent.remove_row(this); // Remove from package
                    picking.delete_row(this); // Delete from data
                    this.destroy(); //funkar detta?
                    //parent.renderElement()
                }
            } else if (this.data.qty_remaining < 0 ){
                picking.getParent().error_beep.play();
            }
            // Save changes to storage
            picking.save('rows');
            this.newly_scanned = true;
            if (reorder){
                parent.reorder_rows(this.id);
            }
            picking.toggle_ui_elements();
        },
        get_product: function(){
            // Return complete product data for this row
            let self = this;
            let ui = this.get_picking_widget().getParent();
            return _.filter(ui.products, function(product){

                return product.id === self.data.product_id.id;
            })[0];
        },
    });

    return {
        OperationEditorWidget: OperationEditorWidget
    }

});
