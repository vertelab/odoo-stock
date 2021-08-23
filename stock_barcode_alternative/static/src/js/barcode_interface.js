odoo.define('stock_barcode_alternative.BarcodeInterface', function(require) {
    "use strict";

    var core = require('web.core');
    var publicWidget = require("web.public.widget");
    var BarcodeScanner = require("stock_barcode_alternative.BarcodeScanner").BarcodeScanner;
    var PickingEditorWidget = require("stock_barcode_alternative.PickingEditorWidget").PickingEditorWidget;
    var _t = core._t;
    var session = require('web.session');

    var sessionStorage = window.sessionStorage;

    var QWeb = core.qweb;

    const { qweb } = require('web.core');

    publicWidget.registry.BarcodeInterface = publicWidget.Widget.extend({
        template: 'AlternativeBarcodeInterface',
        selector: '.barcode_container',
        xmlDependencies: ['/stock_barcode_alternative/static/src/xml/picking.xml'],

        init: function(parent, params){
            this._super.apply(this, arguments);
           //Load parameters from query string
            var init_params = $.bbq.getState();
            this.picking_type_id = init_params.picking_type_id ? init_params.picking_type_id: undefined;
            this.picking_id = init_params.picking_id ? parseInt(init_params.picking_id):undefined;
            this.storage = sessionStorage;
            this.error_beep = new Audio('/stock_barcode_alternative/static/src/sound/negativebeep.wav');
            this.barcode_scanner = new BarcodeScanner;
            this.products = JSON.parse(this.storage.getItem('products')) || [];
            this.picking = {};
            this.packages = [];
            this.packops = [];
            this.picking_goals = {};
            // TODO: Remove force reload
            this.loaded = this.load(true);

        },

        start: function(){
            this._super.apply(this, arguments);
            var self = this;

            this.barcode_scanner.connect(function(ean){
                self.scan(ean);
            });

            this.$('.js_force_reload').click(function(){ self.load(true); });
            this.$('.js_clear_storage').click(function(){ self.storage.clear(); });

            $.when(this.loaded)
                .done((result) => {
                    self.picking_loaded(result)
                })
                .fail((error) => {
                    console.log(error);
                });

            $('.barcode_container').append(QWeb.render('AlternativeBarcodeInterface', {widget: this}));

        },

        picking_loaded: function(res){
            let self = this;
            // console.log('picking', res.picking)
            // console.log('packages', res.packages)
            // console.log('operations', res.operations)
            // console.log('products', res.products)
            self.set_picking(res.picking[0]);
            // self.set_picking(this.picking);
            self.set_packages(res.packages);
            self.set_packops(res.operations);
            self.add_products(res.products);
            self.picking_editor = new PickingEditorWidget(self);
            self.picking_editor.replace(self.$('.oe_placeholder_picking_editor'));
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
                        return e.id === product.id;
                });
                current_product = current_product.length > 0 ? current_product[0]: null;
                if (current_product){
                    // Update the existing product
                    $.extend(current_product, product);
                } else {
                    // Add the new product'
                    self.products.push(product);
                }
            })
            this.save('products');
        },

         quit: function(){
            this.destroy();

            return this._rpc({
                model: 'ir.model.data',
                method: 'search_read',
                args: [[['name', '=', 'stock_picking_type_action']], ['res_id']],
            }).then(function (res) {
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
            // Skip storage. We'll probably end up wanting to load from backend on every page load.
            force_reload = true;
            if (! force_reload) {
                var picking = this.storage.getItem('picking');
                var operations = this.storage.getItem('operations');
                var products = this.storage.getItem('products');
                if (picking && picking.id === this.picking_id){
                    // The picking is already loaded in the storage.
                    var answer = $.Deferred();
                    answer.resolve({picking: picking, operations: operations, products: products});
                    return answer;
                }
            }

            return this._rpc({
                model: 'stock.picking',
                method: 'abc_load_picking',
                args: [[], this.picking_id],
                context: session.user_context
            }).then(function (res) {
                return res
            });

        },

        save: function(fields){
            // Save the data in storage.
            var self = this;
            if (fields === null){
                fields = ['products', 'picking', 'packops', 'packages'];
            }
            if (! Array.isArray(fields)){
                fields = [fields];
            }

            _.each(fields, function(field){
                self.storage.setItem(field, JSON.stringify(self[field]));
            })
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
            var self = this;
            var product = _.filter(
                this.products,
                function(e, pos, l){
                    return e.ean13 === code || e.default_code === code;
                })
            if (product.length > 0){
                // Matched a known product.
                this.scanned_product(product);
            } else {
                // Contact backend to get result.
                // May be a product, picking, etc.
                return this._rpc({
                    model: 'stock.picking',
                    method: 'abc_scan',
                    args: [code],
                    context: session.user_context
                }).then(function (res) {
                    self.handle_scan_result(res)
                });
            }
        },
        handle_scan_result: function(result) {
            // Handle the result from backend scan query
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
            var found = false;
            var done = false;
            var candidate;
            // We can get several products as response. Loop through and check them all.
            // 1. Check for a matching row that hasn't been completed yet.
            // 2. Check for a matching row that has been completed.
            _.each(products, function(product){
                if (done){
                    return
                }
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
                this.picking_editor.get_current_package().increase(products[0].id)
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
});
