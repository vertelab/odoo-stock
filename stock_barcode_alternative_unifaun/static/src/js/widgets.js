odoo.define('stock_barcode_alternative.Unifaun', function(require) {
    "use strict";

    var publicWidget = require("web.public.widget");
    var BarcodeInterface = require('stock_barcode_alternative.BarcodeInterface');
    var PickingEditorWidget = require('stock_barcode_alternative.PickingEditorWidget');
    // console.log('openerp_picking_alt_widgets_unifaun');
    // console.log(PickingEditorWidget);
    // console.log(BarcodeInterface);
    var xml_files = BarcodeInterface.prototype.xmlDependencies.concat(['/stock_barcode_alternative_unifaun/static/src/xml/picking.xml'])
    BarcodeInterface.include({
        xmlDependencies: xml_files
    });
    
class Package {
                constructor(weight, name, id){
                this.id = id
                this.name = name;
                this.weight = weight;
                }
            }
    
    PickingEditorWidget.include({
        init: function(parent, options){
            this.manual_packages = []
            this.display_manual_packages = []
            var pack = new Package(0, `Package ${this.manual_packages.length + 1}`, this.manual_packages.length);
            this.manual_packages.push(pack)
            this.display_manual_packages = this.manual_packages
            this._super(parent, options);
            let unifaun_order = null;
            let unifaun_group = false;
            this.unifaun_parcel_count = 1;
            if (parent){
                unifaun_order = parent.unifaun_id;
            }
            if (unifaun_order && unifaun_order.picking_ids && unifaun_order.picking_ids.length > 1) {
                unifaun_group = true;
            }
            if (this.unifaun_no_order == null){
                if (unifaun_group){
                    this.unifaun_no_order = true;
                } else {
                    this.unifaun_no_order = false;
                }
            }
            if (this.unifaun_parcel_count == null){
                this.unifaun_parcel_count = 0;
            }
            if (this.unifaun_parcel_weight == null){
                this.unifaun_parcel_weight = 0.0;
            }
            
            
        },
        renderElement: function(){
            var self = this;
            this._super();
            this.$('i.package-qty-minus').click(() => {
                // Uses the following: https://developer.mozilla.org/en-US/docs/Web/API/HTMLInputElement/stepDown
                let package_qty = this.$("#abc_dn_unifaun_nr_packages")[0];
                package_qty.stepDown()
                self.unifaun_update_packages()
            })
            this.$('i.package-qty-plus').click(() => {  
                // Uses the following: https://developer.mozilla.org/en-US/docs/Web/API/HTMLInputElement/stepUp   
                let package_qty =  this.$("#abc_dn_unifaun_nr_packages")[0];
                package_qty.stepUp()
                self.unifaun_update_packages()
            })
            this.$('i.total-weight-minus').click(() => {     
                let package_weight = this.$("#abc_dn_unifaun_weight")[0];
                package_weight.stepDown()
                self.unifaun_update_packages()
            })
            this.$('i.total-weight-plus').click(() => {     
                let package_weight = this.$("#abc_dn_unifaun_weight")[0];
                package_weight.stepUp()
                self.unifaun_update_packages()
            })
            this.$('i.unique-package-weight-minus').click((c) => {
                let targetbutton = c.target.attributes['button-id'].value
                this.$('.unifaun_package_weight_input').each((i, n) => {
                    if (targetbutton == n.attributes['list-id'].value) {
                        n.stepDown()
                        self.unifaun_update_packages()
                    }
                })
            })
            this.$('i.unique-package-weight-plus').click((c) => {     
                let targetbutton = c.target.attributes['button-id'].value
                this.$('.unifaun_package_weight_input').each((i, n) => {
                    if (targetbutton == n.attributes['list-id'].value) {
                        n.stepUp()
                        self.unifaun_update_packages()
                    }
                })
            })

            this.$('#abc_dn_unifaun_active').change(function(){self.unifaun_update_packages()});
            this.$('#abc_dn_unifaun_nr_packages').change(function(){self.unifaun_update_packages()});
            this.$('#abc_dn_unifaun_weight').change(function(){self.unifaun_update_packages()});
            this.$('.unifaun_package_weight_input').change(function(){self.unifaun_update_packages()});
        },

        get_saved_fields: function() {
            var fields = this._super();
            return fields.concat(['unifaun_no_order', 'unifaun_parcel_count', 'unifaun_parcel_weight'])
        },

        unifaun_update_packages: function() {    
            
            let self = this
            
            // Update Unifaun data when changes are made in GUI.
            var suppress = this.$('#abc_dn_unifaun_active').prop('checked');
            if (suppress) {
                var parcel_count = 0;
                var parcel_weight = 0.0;
            } else {
                var parcel_count = parseInt(this.$('#abc_dn_unifaun_nr_packages').val()) || 0;
                var parcel_weight = parseFloat(this.$('#abc_dn_unifaun_weight').val()) || 0.0;
                var package_weights = []
                this.$('.unifaun_package_weight_input').each(function(){
                    package_weights.push($(this).val());
                    })

            }
            for (var key = 0; key < package_weights.length; key++) {
                self.manual_packages[key].weight = package_weights[key]
                self.save('manual_packages')
            }
            if (parcel_count > this.manual_packages.length) {
                    for (var i = 0; i < parcel_count - package_weights.length; i++) {
                        var pack = new Package(0, `Package ${this.manual_packages.length + 1}`, this.manual_packages.length);
                        this.manual_packages.push(pack)
                    }
                    this.display_manual_packages = this.manual_packages
                    this.save('manual_packages')
                    this.save('display_manual_packages')
                }
            else if (parcel_count < this.manual_packages.length) {
                this.display_manual_packages = this.manual_packages.slice(0, parcel_count)
                this.save('display_manual_packages')
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
            if (! this.getParent().is_unifaun || this.unifaun_no_order || (this.unifaun_parcel_count > 0 && this.unifaun_parcel_weight > 0)) {
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
            if (!(! this.getParent().is_unifaun || this.unifaun_no_order || (this.unifaun_parcel_count > 0 && this.unifaun_parcel_weight > 0))){
                return true;
            }
            return this._super();
        },
        rest_order_button_disabled: function(tb_disabled){
            // Check if transfer button should be disabled.
            var suppress = this.$('#abc_dn_unifaun_active').prop('checked');
            var parcel_count = parseInt(this.$('#abc_dn_unifaun_nr_packages').val()) || 0;
            var parcel_weight = parseFloat(this.$('#abc_dn_unifaun_weight').val()) || 0.0;
            if (!(! this.getParent().is_unifaun || this.unifaun_no_order || (this.unifaun_parcel_count > 0 && this.unifaun_parcel_weight > 0))){
                return true;
            }
            return this._super(tb_disabled);
        }
    });
});
