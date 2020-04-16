function openerp_picking_alt_widgets_unifaun(instance){
    console.log('openerp_picking_alt_widgets_unifaun');
    var module = instance.stock_barcode_alternative;
    var _t     = instance.web._t;
    var QWeb   = instance.web.qweb;
    
    module.OperationEditorWidget = instance.stock_barcode_alternative.OperationEditorWidget.extend({
        
    });
    
    module.PackageEditorWidget = instance.stock_barcode_alternative.PackageEditorWidget.extend({
        
    });
    
    module.PickingEditorWidget = instance.stock_barcode_alternative.PickingEditorWidget.extend({
        init: function(parent, options){
            this._super(parent, options);
            let unifaun_order = null;
            let unifaun_group = false;
            if (parent.picking){
                unifaun_order = parent.picking.unifaun_id;
            }
            if (unifaun_order && unifaun_order.picking_ids && unifaun_order.picking_ids.length > 1) {
                unifaun_group = true;
                // Message not shown for some reason
                //~ let msg = _t("This picking is a part of the Unifaun Group ") + unifaun_order.name + " (";
                //~ let first = true;
                //~ _.each(unifaun_order.picking_ids, function(picking){
                    //~ if (! first){
                        //~ msg += ", ";
                        //~ first = false;
                    //~ }
                    //~ msg += picking.name;
                //~ });
                //~ parent.log_message(msg + ").", 'info');
            }
            if (this.unifaun_no_order === null){
                if (unifaun_group){
                    this.unifaun_no_order = true;
                } else {
                    this.unifaun_no_order = false;
                }
            }
            if (this.unifaun_parcel_count === null){
                this.unifaun_parcel_count = 0;
            }
            if (this.unifaun_parcel_weight === null){
                this.unifaun_parcel_weight = 0.0;
            }
        },
        renderElement: function(){
            console.log('PickingEditorWidget.renderElement');
            var self = this;
            this._super();
            this.$('#abc_dn_unifaun_active').change(function(){self.unifaun_update_packages()});
            this.$('#abc_dn_unifaun_nr_packages').change(function(){self.unifaun_update_packages()});
            this.$('#abc_dn_unifaun_weight').change(function(){self.unifaun_update_packages()});
        },
        get_saved_fields: function(){
            var fields = this._super();
            return fields.concat(['unifaun_no_order', 'unifaun_parcel_count', 'unifaun_parcel_weight'])
        },
        unifaun_update_packages: function(){
            // Update Unifaun data when changes are made in GUI.
            var suppress = this.$('#abc_dn_unifaun_active').prop('checked');
            if (suppress) {
                var parcel_count = 0;
                var parcel_weight = 0.0;
            } else {
                var parcel_count = parseInt(this.$('#abc_dn_unifaun_nr_packages').val()) || 0;
                var parcel_weight = parseFloat(this.$('#abc_dn_unifaun_weight').val()) || 0.0;
            }
            if (suppress !== this.unifaun_no_order) {
                this.unifaun_no_order = suppress;
                this.save('unifaun_no_order');
            }
            if (parcel_count !== this.unifaun_parcel_count) {
                this.unifaun_parcel_count = parcel_count;
                this.save('unifaun_parcel_count');
            }
            if (parcel_weight !== this.unifaun_parcel_weight) {
                this.unifaun_parcel_weight = parcel_weight;
                this.save('unifaun_parcel_weight');
            }
            this.renderElement();
        },
        get_extra_transfer_data: function(){
            var self = this;
            var data = this._super();
            _.each(['unifaun_no_order', 'unifaun_parcel_count', 'unifaun_parcel_weight'], function(field){
                data[field] = self[field];
            });
            return data;
        },
        do_transfer: function(){
            if (! this.getParent().picking.is_unifaun || this.unifaun_no_order || (this.unifaun_parcel_count > 0 && this.unifaun_parcel_weight > 0)) {
                return this._super();
            };
            this.getParent().log_message("You must set # of packages and weight to complete a Unifaun order.", 'warning');
        },
        toggle_ui_elements: function(){
            // Update UI when changes are made to Unifaun data.
            var el_weight = this.$('#dn_wrapping_weight_calculated');
            el_weight.text(this.get_weight().toFixed(3));
            return this._super();
        },
        transfer_button_disabled: function(){
            // Check if transfer button should be disabled.
            var suppress = this.$('#abc_dn_unifaun_active').prop('checked');
            var parcel_count = parseInt(this.$('#abc_dn_unifaun_nr_packages').val()) || 0;
            var parcel_weight = parseFloat(this.$('#abc_dn_unifaun_weight').val()) || 0.0;
            if (!(! this.getParent().picking.is_unifaun || this.unifaun_no_order || (this.unifaun_parcel_count > 0 && this.unifaun_parcel_weight > 0))){
                return true;
            }
            return this._super();
        },
        rest_order_button_disabled: function(tb_disabled){
            // Check if transfer button should be disabled.
            var suppress = this.$('#abc_dn_unifaun_active').prop('checked');
            var parcel_count = parseInt(this.$('#abc_dn_unifaun_nr_packages').val()) || 0;
            var parcel_weight = parseFloat(this.$('#abc_dn_unifaun_weight').val()) || 0.0;
            if (!(! this.getParent().picking.is_unifaun || this.unifaun_no_order || (this.unifaun_parcel_count > 0 && this.unifaun_parcel_weight > 0))){
                return true;
            }
            return this._super(tb_disabled);
        }
    });
}

openerp.stock_barcode_alternative_original_unifaun = openerp.stock_barcode_alternative;
openerp.stock_barcode_alternative = function(openerp) {
    openerp.stock_barcode_alternative_original_unifaun(openerp);
    openerp_picking_alt_widgets_unifaun(openerp);
}
