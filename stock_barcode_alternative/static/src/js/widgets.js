function openerp_picking_alt_widgets(instance){

    var module = instance.stock_barcode_alternative;
    var _t     = instance.web._t;
    var QWeb   = instance.web.qweb;

    // This widget makes sure that the scaling is disabled on mobile devices.
    // Widgets that want to display fullscreen on mobile phone need to extend this
    // widget.

    module.MobileWidget = instance.web.Widget.extend({
        start: function(){
            if(!$('#oe-mobilewidget-viewport').length){
                $('head').append('<meta id="oe-mobilewidget-viewport" name="viewport" content="initial-scale=1.0; maximum-scale=1.0; user-scalable=0;">');
            }
            return this._super();
        },
        destroy: function(){
            $('#oe-mobilewidget-viewport').remove();
            return this._super();
        },
    });
    
    
    module.PickingEditorWidget = instance.web.Widget.extend({
        template: 'AlternativePickingEditorWidget',
        init: function(parent, options){
            this._super(parent, options);
            var self = this;
            this.rows = [];
            this.search_filter = "";
            this.current_package = null;
            // This expression adds the Contains selector to jQuery. Not sure if we need it.
            jQuery.expr[":"].Contains = jQuery.expr.createPseudo(function(arg) {
                return function( elem ) {
                    return jQuery(elem).text().toUpperCase().indexOf(arg.toUpperCase()) >= 0;
                };
            });
        },
        renderElement: function(){
            var self = this;
            this._super();
        },
        storage: function(){
            return this.getParent().storage;
        },
        load_rows: function(){
            // New plan: save these rows independently of the loaded data in packops.
            // packops = backend data.
            // this.rows = our UI data and the current state of the picking operation.
            // Save and load on page reload. Got to connect the data to picking_id when saving.
            var parent = this.getParent();
            //~ this.rows = [];
            var rows = this.storage().getItem('packops');
            var self = this;
            // Could probably be good with a deeper copy of the rows...
            // Or we save the deep copying for the get_package_rows and handle all the ui fluff there.
            // This would mirror all changes back to the parent for easy storage.
            _.each(rows, function(row){
                row.product_id = _.filter(parent.products, function(e, pos, l){return e.id == row.product_id.id})[0];
            });
            this.rows = rows;
        },
        get_packop_product: function(packop_id){
            var parent = this.getParent();
            var row = _.filter(this.rows, function(e, pos, l) {e.id === packop_id})[0];
            return _.filter(parent.products, function(e, pos, l) {e.id === row.product_id.id})[0]
        },
        get_packages: function(){
            // Return list of packages.
            return [{id:null, display_name: 'No package'}]
        },
        get_package_rows: function(package_id){
            // Return all rows for a given package. Package can be
            // null (returns all unpackaged rows).
            //~ var rows = [];
            // TODO: copy this.rows and add ui fluff and stuff like that.
            var filter_function;
            if (package_id) {
                filter_function = function(e, pos, l){ return e.package_id && e.package_id.id == package_id || false;}
            } else {
                filter_function = function(e, pos, l){ return ! e.package_id;}
            }
            return _.filter(this.rows, filter_function);
        },
        split_row: function(id, package_id){
            //Split one of the products from the given row and put it in the specified package.
            // Give new row a negative id.
        },
        create_package: function(){
            // Create a new package
        },
        increase: function(product_id){
            // Increase row containing the given product_id.
            console.log('increase: ' + product_id);
            console.log(product_id + 10);
            var self = this;
            var row = _.filter(this.rows, function(e, pos, l){
                return e.product_id.id == product_id;
            });
            console.log(row);
            if (row.length > 0){
                row = row[0];
                ++ row.qty_done;
                this.renderElement();
            } else{console.log(this.rows)}
        }
    });

    module.BarcodeInterface = module.MobileWidget.extend({
        template: 'AlternativeBarcodeInterface',
        init: function(parent,params){
            console.log('init!');
            this._super(parent,params);
            var self = this;
            // Load parameters from query string
            var init_params = $.bbq.getState();
            console.log(init_params);
            this.picking_type_id = init_params.picking_type_id ? init_params.picking_type_id:undefined;
            this.picking_id = init_params.picking_id ? parseInt(init_params.picking_id):undefined;
            this.storage = new module.Storage();
            this.barcode_scanner = new module.BarcodeScanner();
            this.products = this.storage.getItem('products') || [];
            this.picking = {};
            this.packages = [];
            this.packops = [];
            // TODO: Remove force reload
            this.loaded = this.load(true);
        },
        start: function(){
            this._super();
            var self = this;
            
            instance.webclient.set_content_full_screen(true);
            
            this.barcode_scanner.connect(function(ean){
                self.scan(ean);
            });

            //~ this.$('.js_pick_quit').click(function(){ self.quit(); });
            //~ this.$('.js_pick_prev').click(function(){ self.picking_prev(); });
            //~ this.$('.js_pick_next').click(function(){ self.picking_next(); });
            //~ this.$('.js_pick_menu').click(function(){ self.menu(); });
            this.$('.js_force_reload').click(function(){ self.load(true); });
            this.$('.js_clear_storage').click(function(){ self.storage.clear(); });
            //~ this.$('.js_reload_op').click(function(){ self.reload_pack_operation();});

            $.when(this.loaded).done(function(result){
                console.log(self);
                self.set_picking(result.picking);
                self.set_packages(result.packages);
                self.set_packops(result.operations);
                console.log(result.operations);
                self.add_products(result.products);
                
                self.picking_editor = new module.PickingEditorWidget(self);
                self.picking_editor.load_rows();
                self.picking_editor.replace(self.$('.oe_placeholder_picking_editor'));
                console.log(self.picking_editor);

                //~ if( self.picking.id === self.pickings[0]){
                    //~ self.$('.js_pick_prev').addClass('disabled');
                //~ }else{
                    //~ self.$('.js_pick_prev').removeClass('disabled');
                //~ }

                //~ if( self.picking.id === self.pickings[self.pickings.length-1] ){
                    //~ self.$('.js_pick_next').addClass('disabled');
                //~ }else{
                    //~ self.$('.js_pick_next').removeClass('disabled');
                //~ }
                //~ if (self.picking.recompute_pack_op){
                    //~ self.$('.oe_reload_op').removeClass('hidden');
                //~ }
                //~ else {
                    //~ self.$('.oe_reload_op').addClass('hidden');
                //~ }
                //~ if (!self.show_pack){
                    //~ self.$('.js_pick_pack').addClass('hidden');
                //~ }
                //~ if (!self.show_lot){
                    //~ self.$('.js_create_lot').addClass('hidden');
                //~ }

            }).fail(function(error) {console.log(error);});

        },
        set_picking: function(picking) {
            this.picking = picking;
            this.save('picking');
        },
        set_products: function(products) {
            this.products = products;
            this.save('products');
        },
        set_packops: function(packops) {
            console.log(packops);
            this.packops = packops;
            this.save('packops');
        },
        set_packages: function(packages) {
            this.packages = packages;
            this.save('packages');
        },
        add_products: function(products){
            // Add new products to the list
            var new_products = [];
            // Filter out the current products that aren't in the new list and save them.
            _.filter(
                this.products,
                function(e, pos, l){
                    return _.filter(products, function(e2, pos2, l2){
                            return e2.id == e.id;
                    }).length == 0;
                }
            )
            _.each(products, function(product){new_products.push(product);})
            this.products = new_products;
            this.save('products');
        },
        quit: function(){
            this.destroy();
            return new instance.web.Model("ir.model.data").get_func("search_read")([['name', '=', 'action_picking_type_form']], ['res_id']).pipe(function(res) {
                    window.location = '/web#action=' + res[0]['res_id'];
                });
        },
        destroy: function(){
            this._super();
            // this.disconnect_numpad();
            this.barcode_scanner.disconnect();
            instance.webclient.set_content_full_screen(false);
        },
        load: function(force_reload){
            // Load picking data. If force_reload isn't set to true, check
            // storage first. If not found in storage, load from backend.
            var self = this;
            console.log('load');
            console.log(this.picking_id);
            if (! force_reload) {
                var picking = this.storage.getItem('picking');
                var operations = this.storage.getItem('operations');
                var products = this.storage.getItem('products');
                console.log(picking);
                if (picking && picking.id == this.picking_id){
                    // The picking is already loaded in the storage.
                    console.log('loading picking data from storage');
                    var answer = $.Deferred();
                    answer.resolve({picking: picking, operations: operations, products: products});
                    return answer;
                }
            }
            console.log('loading picking data from server');
            return new instance.web.Model('stock.picking')
                .call('abc_load_picking', [[this.picking_id]]);
        },
        save: function(fields){
            // Save the data in storage.
            var self = this;
            if (fields === null){
                fields = ['products', 'picking', 'packops', 'packages'];
            }
            if (! Array.isArray(fields)){
                fields = [fields];
            };
            _.each(fields, function(field){self.storage.setItem(field, self[field]);})
        },
        clear_products: function(){
            // Clear product data from storage.
            this.products = []
            this.storage.setItem('products', this.products);
        },
        clear_storage: function(){
            this.storage.clear();
        },
        scan: function(code){
            // Perform a scan.
            console.log('Scanned: ' + code);
            var product = _.filter(
                this.products,
                function(e, pos, l){
                    return e.ean13 == code || e.default_code == code;
                })
            console.log(product);
            if (product.length > 0){
                // Matched a known product.
                var product_id = product[0].id;
                var packop = _.filter(this.packops, function(e, pos, l){
                    return e.product_id.id == product_id;
                });
                if (packop.length > 0){
                    packop = packop[0];
                    ++ packop.qty_done;
                    this.save('packops');
                };
                this.picking_editor.increase(product_id)
            } else {
                // Contact backend to get result.
                // May be a product, picking, etc.
                console.log('no product found! products:');
                console.log(this.products);
            }
            
        },
    });
    
    openerp.web.client_actions.add('stock.ui.alt', 'instance.stock_barcode_alternative.BarcodeInterface');
    
    module.BarcodeScanner = instance.web.Class.extend({
        init: function(parent, options){
            this.timeouts = [];
            this.clear();
        },
        connect: function(callback){
            console.log('Connecting scanner to:');
            console.log(this);
            this.clear();
            var self = this;
            this.handler = function(e){
                console.log('BarcodeScanner.handler');
                console.log(this);
                console.log(self);
                if (self.isEndChar(e)) {
                    if(self.code.length >= 3){
                        callback(self.code);
                    }
                    self.clear();
                } else {
                    self.add(String.fromCharCode(e.which));
                    self.setTimeout();
                }
            };

            $('body').on('keypress', this.handler);

        },
        disconnect: function(){
            this.clear();
            $('body').off('keypress', this.handler);
        },
        add: function(char) {
            this.code += char;
        },
        clear: function() {
            this.clearTimeouts();
            this.code = "";
        },
        clearTimeouts: function() {
            while (this.timeouts.length > 0) {
                clearTimeout(this.timeouts.pop());
            }
        },
        isEndChar: function(e) {
            // We could check shift key and other stuff here if we want to get fancy.
            if(e.which === 13){
                return true;
            }
            return false;
        },
        setTimeout: function() {
            this.clearTimeouts();
            this.timeouts.push(setTimeout(this.clear, 200));
        }
    });

    // Storage interface.
    // For now, we use sessionStorage.
    // sessionStorage is unique for every tab.
    // localStorage is unique for every browser profile. It will keep
    // between sessions. This is probably more problematic than helpful
    // for us.
    module.Storage = instance.web.Class.extend({
        init: function(parent, options){
            
        },
        getItem: function(key){
            console.log(key);
            return JSON.parse(sessionStorage.getItem(key));
        },
        setItem: function(key, value){
            console.log(key + ' ' + value);
            if (value === undefined) {
                value = null;
            }
            sessionStorage.setItem(key, JSON.stringify(value));
        },
        clear: function(){
            sessionStorage.clear();
        },
        removeItem: function(key){
            sessionStorage.removeItem(key);
        },
        loadRecord: function(model, id){
            key = name + '(' + id + ')';
            return this.getItem(key);
        },
        saveRecord: function(record){
            key = record._name + '(' + record.id + ')';
            this.setItem(key, record);
        }
    });
}

openerp.stock_barcode_alternative = function(openerp) {
    openerp.stock_barcode_alternative = openerp.stock_barcode_alternative || {};
    openerp_picking_alt_widgets(openerp);
}
