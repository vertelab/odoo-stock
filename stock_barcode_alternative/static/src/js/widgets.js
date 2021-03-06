function openerp_picking_alt_widgets(instance){
    //~ console.log('openerp_picking_alt_widgets');
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
            //~ console.log('OperationEditorWidget.init');
            //~ console.log(options);
            var self = this;
            // this.data contains pure data (JSONifiable stuff like {}, [], strings, integers, floats etc) describing this packop, destined for storage.
            // We reuse the provided object to keep all the data up to date on PickingEditorWidget (the same object is in that structure, so all changes are automatically mirrored there).
            // Any instantiated widgets or similar objects should be stored on this, not in data.
            this.data = options.row;
            this.id = this.data.id;
            //~ console.log("MyTag1.5: ",this.data)

        },
        renderElement: function(){
            var self = this;
            this.setElement(self.getParent().$('tr.abc-packop[data-id="' + this.id + '"]'));
            this._super();
            this.$('i.abc-op-qty-plus').click(function(){self.increase()});
            this.$('i.abc-op-qty-minus').click(function(){self.decrease()});
            this.$('i.abc-op-maximize-qty').click(function(){self.maximize_qty()});
            // 
            this.$('input.js_qty').change(function(){self.set_qty(parseFloat(this.value))});
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
            // Not finished and unused.
            var old_parent = this.getParent();
            var old_package = null; //TODO
            this.setParent();
        },
        maximize_qty: function(){
            // Add the remaining planned quantity to this line 
            this.set_qty(this.data.qty_done + this.data.qty_remaining);
        },
        increase: function(reorder){
            this.set_qty(this.data.qty_done + 1, reorder);
        },
        decrease: function(reorder){
            this.set_qty(this.data.qty_done - 1, reorder);
        },
        get_classes: function(){
            var self = this;
            // Return the classes decorating this row in the UI
            var classes = 'abc-packop';
            
            //~ console.log(this.data.product_id['is_offer']);
            //~ console.log('LukasQ', this.data.quantity);
            
            let ui = this.get_picking_widget().getParent();
            if(ui.products){
                _.each(ui.products, function(product){
                    console.log("Product: ", product)
                    if(product.id == self.data.product_id.id){
                        if(product.is_offer){
                            self.data['qty_done'] = self.data['quantity'];
                            console.log('QTY', self.data['qty_done'])
                            self.data.qty_remaining = 0;
                            classes += ' hidden';
                        }
                    }
                    
                })
                    
                
                //~ console.log("MyTag3: ", classes)
            };
            
            //~ console.log("MyTag4: ", classes)
        
            if (this.data.qty_remaining < 0) {
                classes += ' qty-over';
            } else if (this.data.qty_remaining == 0) {
                classes += ' finished';
            } else if (this.data.qty_done > 0) {
                classes += ' unfinished';
            } 
            
            
            if (this.newly_scanned) {
                // This is the most recently scanned line. Mark it as such for CSS.
                classes += ' abc_newly_scanned';
                this.newly_scanned = false;
                //~ console.log('Haze X')
            }
            //~ console.log('Haze 2', this.data.product.is_offer)
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
                
                return product.id == self.data.product_id.id;
            })[0];
        },
    });
    
    module.PackageEditorWidget = instance.web.Widget.extend({
        template: 'AlternativePackageEditorWidget',
        init: function(parent, options){
            this._super(parent, options);
            //~ console.log('PackageEditorWidget.init');
            //~ console.log("MyTag0",options);
            //~ console.log(parent.rows);
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
            // Instantiate a widget for each packop.
            _.each(rows, function(row){
                var row_widget = new module.OperationEditorWidget(self, {row: row});
                self.rows.push(row_widget);
            });
            self.reorder_rows();
            
        },
        renderElement: function(){
            //~ console.log('PackageEditorWidget.renderElement');
            var self = this;
            this.setElement(self.getParent().$('tbody.abc-packop-package[data-package-id="' + this.id + '"]'));
            this._super();
            _.each(this.getChildren(), function(child){child.renderElement()});
            
        },
        start: function(){
            this._super();
            var self = this;
            //~ console.log('PackageEditorWidget.start');
        },
        get_picking_widget: function() {
            return this.getParent();
        },
        reorder_rows: function(packop_id){
            // Reorder the rows. Put packop_id first if specified.
            this.rows.sort(function(el1, el2){
                //~ console.log(el1);
                if (el1.id== packop_id) {
                    return -1;
                } else if (el2.id == packop_id) {
                    return 1;
                }
                // Calculate row weights for sorting. -1 (red), 1 (yellow), or 2 (green)
                let weight1 = el1.data.qty_remaining == 0 ? 2 : el1.data.qty_remaining / Math.abs(el1.data.qty_remaining);
                let weight2 = el2.data.qty_remaining == 0 ? 2 : el2.data.qty_remaining / Math.abs(el2.data.qty_remaining);
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
                return e.data.product_id.id == product_id;
            });
            if (rows.length > 0) {
                var done = false;
                var row;
                _.each(rows, function(r){
                    if (done){return};
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
                new instance.web.Model('stock.picking')
                    .call('abc_create_row', [picking_editor.id, row_data])
                    .then(function(result){
                        picking_editor.rows.unshift(result);
                        self.data.operation_ids.unshift(result.id)
                        picking_editor.save('rows');
                        picking_editor.save('package_data');
                        var row_widget = new module.OperationEditorWidget(self, {row: result});
                        self.rows.push(row_widget);
                        self.renderElement();
                    });
                //~ console.log('Lukas2', row_data)
                return true;
            }
            return false;
        },
        selected: function(){
            return this.id == this.get_picking_widget().current_package;
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
            //~ console.log('PickingEditorWidget.renderElement');
            var self = this;
            this._super();
            this.$('button.js_do_transfer').click(this.do_transfer);
            this.$('button.js_pick_done').click(this.do_transfer);
            this.toggle_ui_elements();
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
            this.load_fields();
            if (! this.rows) {
                var rows = JSON.parse(JSON.stringify(this.getParent().packops));
                _.each(rows, function(row){
                    row.qty_done = 0.0;
                    row.qty_remaining = row.quantity;
                    if (! row.package_id){
                        row.package_id = {id: null};
                    };
                });
                this.rows = rows;
                this.save('rows');
            };
            //~ console.log('PickingEditorWidget.rows');
            //~ console.log(this.rows);
            if (! this.package_data) {
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
            this.packages = [];
            _.each(this.package_data, function(package){
                self.packages.push(new module.PackageEditorWidget(self, {package: package}));
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
                return e.id == self.current_package;})[0];
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
            //~ console.log('get_saved_fields');
            return ['current_package', 'rows', 'package_data'];
        },
        load_fields: function(fields){
            var self = this;
            if (fields === undefined){
                fields = this.get_saved_fields();
            }
            //~ console.log(fields);
            if (! Array.isArray(fields)){
                fields = [fields];
            };
            //~ console.log('load_fields');
            //~ console.log(fields);
            _.each(fields, function(field){
                self[field] = self.storage.getItem(field + '_' + self.getParent().picking_id);
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
            //~ console.log(this);
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
            return {context: JSON.parse(JSON.stringify(this.session.user_context))};
        },
        do_transfer: function(){
            // Complete the picking process.
            var self = this;
            new instance.web.Model('stock.picking')
                .call('abc_do_transfer', [this.id, this.rows, this.package_data], this.get_extra_transfer_data())
                .then(function(result){self.transfer_done(result)});
        },
        transfer_done: function(result){
            var self = this;
            //~ console.log('transfer_done');
            //~ console.log(result);
            
            _.each(result.messages, function(message) {
                self.getParent().log_message(message);
            });
            _.each(result.warnings, function(warning) {
                var details = warning[0] + '\n\n' + warning[1];
                self.getParent().log_message(warning[0], 'warning', details);
                window.alert(details);
            });
            if (result.results.transfer == 'success'){
                this.delete_picking();
                _.each(this.packages, function(package){
                    package.destroy();
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
            _.each(this.packages, function(package){
                weight += package.get_weight();
            })
            return weight;
        }
    });

    module.BarcodeInterface = module.MobileWidget.extend({
        template: 'AlternativeBarcodeInterface',
        init: function(parent, params){
            console.log('BarcodeInterface.init!', this);
            this._super(parent,params);
            var self = this;
            // Load parameters from query string
            var init_params = $.bbq.getState();
            //~ console.log(init_params);
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

            $.when(this.loaded).done(function(result){self.picking_loaded(result)}).fail(function(error) {console.log(error);});

        },
        picking_loaded: function(result){
            let self = this;
            //~ console.log(self);
            self.set_picking(result.picking);
            self.set_packages(result.packages);
            self.set_packops(result.operations);
            //~ console.log(result.operations);
            self.add_products(result.products);
            self.picking_editor = new module.PickingEditorWidget(self);
            self.picking_editor.replace(self.$('.oe_placeholder_picking_editor'));
            //~ console.log(self.picking_editor);
        },
        goto_picking: function(picking_id){
            // Switch to the given picking
            $.bbq.pushState('#picking_id=' + picking_id);
            window.location.reload();
            // Original. Not sure what the point is? We're missing a listener
            // on haschange that does magic stuff. Seems to overcomplicate things.
            //$(window).trigger('hashchange');
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
            //~ console.log('BarcodeInterface.set_packops', packops, this);
            this.packops = packops;
            this.save('packops');
            var picking_goals = {};
            _.each(packops, function(op) {
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
            let self = this;
            _.each(products, function(product){
                // Check if the product is already in the list.
                let current_product = _.filter(
                    self.products,
                    function(e, pos, l){
                        return e.id == product.id;
                });
                current_product = current_product.length > 0 ? current_product[0]: null;
                if (current_product){
                    // Update the existing product
                    $.extend(current_product, product);
                } else {
                    // Add the new product
                    self.products.push(product);
                }
            })
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
            //~ console.log('BarcodeInterface.load', this.picking_id);
            // Skip storage. We'll probably end up wanting to load from backend on every page load.
            force_reload = true;
            if (! force_reload) {
                var picking = this.storage.getItem('picking');
                var operations = this.storage.getItem('operations');
                var products = this.storage.getItem('products');
                //~ console.log(picking);
                if (picking && picking.id == this.picking_id){
                    // The picking is already loaded in the storage.
                    //~ console.log('loading picking data from storage');
                    var answer = $.Deferred();
                    answer.resolve({picking: picking, operations: operations, products: products});
                    return answer;
                }
            }
            //~ console.log('loading picking data from server');
            return new instance.web.Model('stock.picking')
                .call('abc_load_picking', [[this.picking_id]], {context: self.session.user_context});
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
            // Handle the scanned code.
            console.log('Scanned: ' + code);
            //~ console.log(this);
            var self = this;
            var product = _.filter(
                this.products,
                function(e, pos, l){
                    return e.ean13 == code || e.default_code == code;
                })
            //~ console.log(product);
            if (product.length > 0){
                // Matched a known product.
                this.scanned_product(product);
            } else {
                // Contact backend to get result.
                // May be a product, picking, etc.
                //~ console.log('no product found! products:');
                //~ console.log(this.products);
                new instance.web.Model('stock.picking').call('abc_scan', [code], {context: self.session.user_context})
                    .then(function(result){self.handle_scan_result(result)});
            }
        },
        handle_scan_result: function(result) {
            // Handle the result from backend scan query
            //~ console.log('handle_scan_result', result);
            if (result.type === 'product.product') {
                this.add_products(result.product);
                this.scanned_product(result.product);
            } else if (result.type === 'stock.picking'){
                this.goto_picking(result.picking.id);
            }
            else if (result.type === 'no hit'){
                this.error_beep.play();
                window.alert(result.term + " didn't match any products or pickings.");
            }
        },
        scanned_product: function(products){
            // The user scanned a product. Do something with it.
            var self = this;
            //~ console.log('scanned_product', products);
            var found = false;
            var done = false;
            var candidate;
            // We can get several products as response. Loop through and check them all.
            // 1. Check for a matching row that hasn't been completed yet.
            // 2. Check for a matching row that has been completed.
            _.each(products, function(product){
                if (done){return};
                if (self.picking_editor.has_product(product.id)){
                    found = true;
                    // Increase if this row isn't done yet.
                    if (self.picking_editor.get_current_package().increase(product.id, true)){
                        // 1. A row was increased. We're done here.
                        done = true;
                    } else if (!candidate){
                        // No row was increased, because all matching rows were done. Remember this product for step 2. 
                        candidate = product;
                    }
                }
            });
            if (!done && found){
                // 2. A completed row was found and is the best match. Increase it.
                this.picking_editor.get_current_package().increase(candidate.id)
            } else if (! found) {
                // This product isn't on the picking
                this.error_beep.play();
                //~ var product_names = [];
                //~ _.each(products, function(product){
                    //~ product_names.push(product.display_name);
                //~ });
                this.picking_editor.get_current_package().increase(products[0].id)
                //~ console.log(product_names);
                // TODO: Translation
                //~ window.alert(product_names.join(' / ') + " finns ej på denna plocksedel!");
            }
        },
        log_message: function(msg, type, details){
            // Log a message in the messge area.
            var msg_area = $('.abc-message-area');
            var scrollAtBottom = msg_area.prop('scrollHeight') - msg_area.prop('clientHeight') <= msg_area.scrollTop() + 1;
            var message = $('<li></li>');
            //message.text(msg);
            var first = true;
            _.each(msg.split('\n'), function(m){
                var p = $('<p class="abc-message-row"></p>');
                p.html(m);
                var chevron = $('<span class="abc-message-chevron"></span>');
                if (first){
                    chevron.append($('<i class="fa fa-chevron-right"></i>'));
                    if (details) {
                        var link = $('<a href="#"></a>');
                        link.data('details', details);
                        link.text('[details] ')
                        link.click(function(){window.alert($(this).data('details'))});
                        chevron.prepend(link);
                    }
                    first = false;
                }
                p.prepend(chevron);
                message.append(p)
            });
            message.addClass('abc-message');
            if (type) {
                message.addClass('abc-message-' + type);
            }
            msg_area.append(message);
            if (scrollAtBottom) {
                msg_area.scrollTop(msg_area.prop('scrollHeight') - msg_area.prop('clientHeight'));
            }
        }
    });
    
    openerp.web.client_actions.add('stock.ui.alt', 'instance.stock_barcode_alternative.BarcodeInterface');
    
    module.BarcodeScanner = instance.web.Class.extend({
        init: function(parent, options){
            this.timeout = 200; // The timeout to determine if we're scanning or typing
            this.last_parse = null; // The time of the last parsed character
            this.clear();
        },
        connect: function(callback){
            // Connect the scanner to a callback function.
            //~ console.log('Connecting scanner to:', this);
            this.disconnect();
            var self = this;
            this.handler = function(e){
                //~ console.log('BarcodeScanner.handler: ' + String.fromCharCode(e.which));
                // Check timeout
                var now = new Date();
                if (self.last_parse && ((now - self.last_parse) > self.timeout)){
                    self.clear(now);
                } else {
                    self.last_parse = now;
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
            // Add a char to the scan result
            this.code += char;
        },
        clear: function(now) {
            // Reset and prepare for new scan
            this.code = "";
            this.last_parse = now;
        },
        isEndChar: function(e) {
            // Check if the given action represents our end char.
            
            // We could check shift key and other stuff here if we want to get fancy.
            if(e.which === 13){
                return true;
            }
            return false;
        },
        isStartChar: function(e) {
            // Check if the given action represents our start char.
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
            //~ console.log(key);
            return JSON.parse(sessionStorage.getItem(key));
        },
        setItem: function(key, value, timestamp){
        //~ setItem: function(key, value, timestamp){
            //~ console.log(key + ' ' + value);
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
