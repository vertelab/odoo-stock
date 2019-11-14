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
        }
    });
    
    module.OperationEditorWidget = instance.web.Widget.extend({
        template: 'AlternativeOperationEditorWidget',
        init: function(parent, options){
            this._super(parent, options);
            console.log('OperationEditorWidget.init');
            console.log(options);
            var self = this;
            this.data = options.row;
            this.id = this.data.id;
        },
        renderElement: function(){
            var self = this;
            this.setElement(self.getParent().$('tr.js_packop[data-id="' + this.id + '"]'));
            this._super();
            this.$('i.fa-plus').click(function(){self.increase()});
            this.$('i.fa-minus').click(function(){self.decrease()});
            // 
            this.$('input.js_qty').change(function(){console.log('onchange'); console.log(this);self.set_qty(parseFloat(this.value))});
            _.each(this.getChildren(), function(child){child.renderElement()});
        },
        start: function(){
            this._super();
            var self = this;
        },
        get_picking_widget: function() {
            return this.getParent().get_picking_widget();
        },
        set_package: function(package){
            var old_parent = this.getParent();
            var old_package = null; //TODO
            this.setParent();
        },
        increase: function(){
            this.set_qty(this.data.qty_done + 1);
        },
        decrease: function(){
            this.set_qty(this.data.qty_done - 1);
        },
        get_classes: function(){
            // Return the classes decorating this row
            var classes = 'js_packop';
            if (this.data.qty_remaining < 0) {
                classes += ' danger';
            } else if (this.data.qty_remaining == 0) {
                classes += ' success';
            } else if (this.data.qty_done > 0) {
                classes += ' unfinished';
            }
            if (this.blink) {
                // This is the most recently scanned line. Blink and reset.
                classes += ' blink_me';
                this.blink = false;
            }
            return classes;
        },
        set_qty: function(qty){
            // Update quantity for this row.
            if (qty === NaN) {
                qty = 0.0;
            } else if (qty < 0.0) {
                qty = 0.0;
            }
            if (qty == this.data.qty_done) {
                // Nothing has changed.
                return;
            }
            this.data.qty_done = qty;
            var picking = this.get_picking_widget()
            picking.update_remaining(this.data.product_id.id);
            var parent = this.getParent();
            var picking = this.get_picking_widget();
            if (this.data.qty_done == 0.0){
                if (this.id < 0) {
                    // Not original row. Should this matter? We don't
                    // reuse the same picking wizard anyway. Lets keep it this way for now.
                    // TODO: Delete row
                    parent.remove_row(this.id); // Remove from package
                    picking.delete_row(this.id); // Delete from data
                    this.destroy(); //funkar detta?
                    //parent.renderElement()
                }
            } else if (this.data.qty_remaining < 0){
                picking.getParent().error_beep.play();
            }
            // Save changes to storage
            picking.save('rows');
            this.blink = true;
        }
    });
    
    module.PackageEditorWidget = instance.web.Widget.extend({
        template: 'AlternativePackageEditorWidget',
        init: function(parent, options){
            this._super(parent, options);
            console.log('PackageEditorWidget.init');
            console.log(options);
            console.log(parent.rows);
            var self = this;
            this.data = options.package;
            this.id = this.data.id;
            var rows = _.filter(parent.rows, function(e, pos, l){
                return self.data.operation_ids.indexOf(e.id) > -1;
            });
            this.rows = [];
            _.each(rows, function(row){
                var row_widget = new module.OperationEditorWidget(self, {row: row});
                self.rows.push(row_widget);
            });
            
        },
        renderElement: function(){
            console.log('PackageEditorWidget.renderElement');
            var self = this;
            this.setElement(self.getParent().$('tbody.js_packop_package[data-package-id="' + this.id + '"]'));
            this._super();
            _.each(this.getChildren(), function(child){child.renderElement()});
            
        },
        start: function(){
            this._super();
            var self = this;
            console.log('PackageEditorWidget.start');
        },
        get_picking_widget: function() {
            return this.getParent();
        },
        remove_row: function(id){
            // Remove a row from this package.
            this.rows.filter(function(e){return e.id != id});
            // Save changes to package data
            this.get_picking_widget().save('package_data')
        },
        increase: function(product_id){
            // Increase quantity of the row containing the given product_id.
            // Called from the scanner.
            console.log('PackageEditorWidget(' + this.id + ').increase: ' + product_id);
            var self = this;
            var row = _.filter(this.rows, function(e, pos, l){
                return e.data.product_id.id == product_id;
            });
            if (row.length > 0) {
                row = row[0];
                row.increase();
            } else {
                // Find and split original row onto this package.
            }
            
            
            //~ console.log(row);
            //~ if (row.length > 0){
                //~ row = row[0];
                //~ ++ row.qty_done;
                //~ this.renderElement();
            //~ } else{
                //~ console.log(this.rows)
            //~ }
        },
        selected: function(){
            return this.id == this.get_picking_widget().current_package;
        }
    });
    
    module.PickingEditorWidget = instance.web.Widget.extend({
        template: 'AlternativePickingEditorWidget',
        init: function(parent, options){
            this._super(parent, options);
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
            console.log('PickingEditorWidget.renderElement');
            var self = this;
            this._super();
            this.$('button.js_do_transfer').click(this.do_transfer);
            _.each(this.getChildren(), function(child){child.renderElement()});
        },
        start: function(){
            this._super();
            var self = this;
        },
        load_rows: function(){
            // New plan: save these rows independently of the loaded data in packops.
            // packops = always current backend data.
            // this.rows = our UI data and the current state of the picking operation.
            // Save and load on page reload. Got to connect the data to picking_id when saving.
            var self = this;
            var parent = this.getParent();
            //~ this.rows = [];
            var rows = this.storage.getItem('rows_' + parent.picking_id);
            // Could probably be good with a deeper copy of the rows...
            // Or we save the deep copying for the get_package_rows and handle all the ui fluff there.
            // This would mirror all changes back to the parent for easy storage.
            if (! rows) {
                //~ var rows = this.storage.getItem('packops');
                var rows = JSON.parse(JSON.stringify(this.getParent().packops));
                _.each(rows, function(row){
                    row.qty_done = 0.0;
                    row.ui_state = ''; // 'unfinished', 'danger' 'success'
                    row.qty_remaining = row.quantity;
                    if (! row.package_id){
                        row.package_id = {id: null};
                    };
                });
                this.rows = rows;
                this.save('rows');
            };
            this.rows = rows;
            console.log('PickingEditorWidget.rows');
            console.log(this.rows);
            var package_data = this.storage.getItem('package_data_' + parent.picking_id);
            if (! package_data) {
                package_data = JSON.parse(JSON.stringify(parent.packages));
                package_data.push({id: null, display_name: 'No Package'})
                _.each(package_data, function(package){
                    package.operation_ids = [];
                    _.each(self.rows, function(row) {
                        if (row.package_id.id == package.id){
                            package.operation_ids.push(row.id);
                        }
                    });
                });
                this.package_data = package_data;
                this.save('package_data');
            }
            this.package_data = package_data;
            this.packages = [];
            _.each(this.package_data, function(package){
                self.packages.push(new module.PackageEditorWidget(self, {package: package}));
            });
            this.current_package = this.storage.getItem('current_package_' + this.getParent().picking_id);
            this.renderElement();
        },
        get_current_package: function(){
            // Return the current package.
            var self = this;
            return _.filter(this.packages, function(e, pos, l){
                return e.id == self.current_package;})[0];
        },
        set_current_package: function(id){
            var old_package = this.get_current_package();
            this.current_package = id;
            this.save('current_package');
            old_package.renderElement();
            this.get_current_package().renderElement();
        },
        save: function(fields){
            // Save the data in storage.
            var self = this;
            if (fields === null){
                fields = ['current_package', 'rows', 'package_data', 'picking_goals'];
            }
            if (! Array.isArray(fields)){
                fields = [fields];
            };
            _.each(fields, function(field){
                self.storage.setItem(field + '_' + self.getParent().picking_id, self[field]);
            })
        },
        update_remaining: function(product_id){
            // Update the todo on all lines
            var operations = [];
            var total = 0.0;
            // Build list of affected operations (widgets) and total scanned qty
            _.each(this.packages, function(package){
                _.each(package.rows, function(row){
                    if (row.data.product_id.id == product_id) {
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
        set_current_package: function(package) {
            this.current_package = package;
            this.save('current_package');
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
        delete_row: function(id){
            // Delete a row.
            this.rows.filter(function(e){
                return e.id != id});
            this.save('rows');
        },
        split_row: function(id, package_id){
            //Split one of the products from the given row and put it in the specified package.
            // Give new row a negative id.
        },
        create_package: function(){
            // Create a new package
        },
        set_row_qty: function(row_id, qty, diff) {
            // Set the qty_done of a row.
            // Use qty to set quantity, diff to change it from current.
            var self = this;
            var row = _.filter(this.rows, function(e, pos, l){
                return e.id == row_id;
            });
            if (diff !== undefined) {
                qty = row.qty_done + diff;
            }
            // Don't go below 0.
            if (qty < 0) {
                qty = 0;
            }
            diff = qty - row.qty_done;
            
            if (diff === undefined) {
                diff = qty - row.qty_done;
            } else {
                qty = row.qty_done + diff;
            }
            row.qty_done = qty;
            
        },
        get_backend_url: function (){
            if (this.getParent().picking) {
                return '/web#id=' + this.id + '&view_type=form&model=stock.picking';
            }
            return '/web#page=0&amp;limit=80&amp;view_type=list&amp;model=stock.picking&amp;active_id=2';
        },
        update_picking_goals: function(product_id, qty){
            // Deprecated?
            if (this.picking_goals[product_id] === undefined) {
                this.picking_goals[product_id] = 0.0;
            }
            this.picking_goals[product_id] -= qty;
            this.save('picking_goals');
            var rows = _.filter(this.rows, function(e, pos, l){
                return e.product_id.id == product_id;
            });
            _.each(rows, function(row){});//youarehere
            return this.picking_goals[product_id];
        },
        delete_picking: function(){
            var self = this;
            _.each(['package_data_', 'rows_'], function(key){ self.storage.removeItem(key + self.id)})
        },
        do_transfer: function(){
            // Complete the picking process.
            var self = this;
            console.log(this.id);
            new instance.web.Model('stock.picking')
                .call('abc_do_transfer', [this.id, this.rows, this.package_data]).then(
                    function(result){
                        if (result.result == 'success'){
                            window.alert('Picking completed');
                            self.delete_picking();
                        }
                    }
                );
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
            this.error_beep = new Audio('/stock_barcode_alternative/static/src/sound/negativebeep.wav');
            this.barcode_scanner = new module.BarcodeScanner();
            this.products = this.storage.getItem('products') || [];
            this.picking = {};
            this.packages = [];
            this.packops = [];
            this.picking_goals = {};
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
                //self.picking_editor.load_rows();
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
            var picking_goals = {};
            _.each(packops, function(op) {
                console.log(op);
                if (picking_goals[op.product_id.id] === undefined) {
                    picking_goals[op.product_id.id] = op.quantity;
                } else  {
                    picking_goals[op.product_id.id] += op.quantity;
                }
            });
            this.picking_goals = picking_goals;
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
            // Skip storage. We'll probably end up wanting to load from backend on every page load.
            force_reload = true;
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
                this.picking_editor.get_current_package().increase(product[0].id)
            } else {
                // Contact backend to get result.
                // May be a product, picking, etc.
                console.log('no product found! products:');
                console.log(this.products);
                this.error_beep.play();
            }
            
        },
    });
    
    openerp.web.client_actions.add('stock.ui.alt', 'instance.stock_barcode_alternative.BarcodeInterface');
    
    module.BarcodeScanner = instance.web.Class.extend({
        init: function(parent, options){
            this.timeout = 200; // The timeout to determine if we're scanning or typing
            this.last_parse = null; // The time of the last parsed character
            this.clear();
        },
        connect: function(callback){
            console.log('Connecting scanner to:');
            console.log(this);
            this.disconnect();
            var self = this;
            this.handler = function(e){
                console.log('BarcodeScanner.handler: ' + String.fromCharCode(e.which));
                // Check timeout
                var now = new Date();
                if (this.last_parse && ((now - this.last_parse) > this.timeout)){
                    this.clear(now);
                } else {
                    this.last_parse = now;
                }
                if (self.isEndChar(e)) {
                    var code = self.code;
                    self.clear(now);
                    if(code.length >= 3){
                        callback(code);
                    }
                } else {
                    self.add(String.fromCharCode(e.which));
                }
            };

            $('body').on('keypress', this.handler);

        },
        disconnect: function(){
            this.clear();
            if (this.handler !== undefined){
                $('body').off('keypress', this.handler);
            }
        },
        add: function(char) {
            this.code += char;
        },
        clear: function(now) {
            this.code = "";
            this.last_parse = now;
        },
        isEndChar: function(e) {
            // We could check shift key and other stuff here if we want to get fancy.
            if(e.which === 13){
                return true;
            }
            return false;
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
        setItem: function(key, value, timestamp){
        //~ setItem: function(key, value, timestamp){
            console.log(key + ' ' + value);
            //~ if (timestamp) {
                //~ value._save_date = new Date().toTimeString();
            //~ }
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
        }
    });
}

openerp.stock_barcode_alternative = function(openerp) {
    openerp.stock_barcode_alternative = openerp.stock_barcode_alternative || {};
    openerp_picking_alt_widgets(openerp);
}
