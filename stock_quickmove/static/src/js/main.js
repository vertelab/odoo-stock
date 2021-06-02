odoo.define('stock_quickmove.QuickMove', function (require) {
    "use strict";

    var ajax = require('web.ajax');
    var core = require('web.core');
    var CrashManager = require('web.CrashManager').CrashManager;
    var Dialog = require('web.Dialog');

    var _t = core._t;
    var QWeb = core.qweb;

    var location_src_scanned = false;

    ajax.loadXML('/stock_quickmove/static/src/xml/picking.xml', core.qweb);

    function update_product_lines(res) {
        remove_all_product_lines()
        var product_content = QWeb.render('quickmove_product_lines', {
            'product_ids': res,
        });
        $("tbody#quickmove_product_lines").append(product_content);
    }

    function update_product_location_lines(res) {
        var product_id = res['product_id'];
        if (!product_id) return;
        ajax.jsonRpc("/stock/inventory_search_product_location", "call", {
            'product_id': product_id
        }).then(function(locations){
            console.log(locations); //{location_id: 5290, name: "WH/Plocklager/L01D", qty: 3674}
            var location_content = QWeb.render('product_location_lines', {'locations': locations, 'product_id': product_id});

            remove_all_location_lines();
            $("tbody#product_location_lines").append(location_content);
        });
    }

    function remove_all_location_lines() {
        $("tbody#product_location_lines").empty();
    }

    function remove_all_product_lines() {
        $("tbody#quickmove_product_lines").empty();
    }

    // inventory


    (function($){

        $.barcodeListener = function(context, options){

            //~ var $defaults = {
                //~ support: [8, 12, 13]
            //~ };

            var $this = this;
            $this.element = $(context);
            $this.timeout = 0;
            $this.code = '';
            $this.settings = {};

            $this.init = function(){
                $this.settings = $.extend({}, options);
                $this.element.on('keypress', function(e){
                    $this.listen(e);
                })
            };

            $this.listen = function(e){
                var $char = $this.validateKey(e.which);
                if($char === 13){
                    $this.validate();
                } else if($char !== false) {
                    if($this.code == ''){
                        setTimeout($this.clear(), 1000);
                    }
                    $this.add($char);
                }
            };

            $this.validate = function(){
                var $tmp = $this.code;
                //~ if($this.settings.support.indexOf($tmp.length) > -1){
                    var $d = new Date(),
                        $interval = $d.getTime() - $this.timeout;
                    $this.clear();
                    if($interval < 1000){
                        $this.element.trigger('barcode.valid', [$tmp]);
                    }
                //~ } else {
                    //~ $this.clear();
                //~ }
            };

            $this.clear = function(){
                $this.code = '';
                $this.timeout = 0;
            };

            $this.validateKey = function(keycode){
                if(keycode === 13 || (keycode >= 48 && keycode <= 57) || (keycode >= 65 && keycode <= 90)){
                    if(keycode === 13){
                        return keycode;
                    } else {
                        return String.fromCharCode(keycode);
                    }
                } else {
                    return false;
                }
            };

            $this.add = function(char){
                if($this.timeout === 0){
                    var $d = new Date();
                    $this.timeout = $d.getTime();
                }
                $this.code += char;
            };

            $this.init();
        };

        $.fn.barcodeListener = function(options) {

            return this.each(function(){
                if(undefined === $(this).data('barcodeListener')){
                    var plugin = new $.barcodeListener(this, options);
                    $(this).data('barcodeListener', plugin);
                }
            });
        }

    })(jQuery);

    function quickmove_start_scanner() {
        $("body").barcodeListener().on("barcode.valid", function(e, code){
            // var website = openerp.website;
            //
            // website.add_template_file("/stock_quickmove/static/src/xml/picking.xml");
            ajax.jsonRpc("/stock/quickmove_barcode", "call", {
                'barcode': code,
                'location_src_scanned': location_src_scanned
            }).done(function(result){

                if (result === undefined){
                    $(".red-alert-message-undefined").removeClass("hidden");
                    return

                } else if (result.type === 'product') {
                    var newOption = new Option(result.product_ids[1], result.product_ids[0], false, true);
                    $('select#quickmove_product_search').append(newOption).trigger('change');
                    location_src_scanned = true;
                } else if (result.type === 'src_location') {

                    var newOption = new Option(result.product_ids[1], result.product_ids[0], false, true);
                    $('select#quickmove_location_src_id').append(newOption).trigger('change');
                    location_src_scanned = true;

                } else if (result.type === 'dest_location') {
                    var newOption = new Option(result.location.name, result.location.id, false, true);
                    $('select#quickmove_location_dest_id').append(newOption).trigger('change');
                    location_src_scanned = false;
                }
                $(".red-alert-message-undefined").addClass("hidden");
                $('#quickmove_location_src_id').select9('open');

            })
        })
    }

    quickmove_start_scanner()

    function quickmove_inventory_start_scanner() {
        $("body").barcodeListener().on("barcode.valid", function(e, code){

            $.ajax({
                url: '/stock/quickmove_product_search',
                datatype: 'json',
                data: {term: code},
                type: "POST",

                success: function (data)
                {
                    if (Array.isArray(data.results) && data.results.length) {

                    var product_text = data.results[0].text;
                    var product_id = data.results[0].id;

                    var newOption = new Option(product_text, product_id, false, true);
                    $('select#inventory_product_search').append(newOption).trigger('change');
                    location_src_scanned = true;
                    $(".red-alert-message-undefined").addClass("hidden");

                    } else {
                        $(".red-alert-message-undefined").removeClass("hidden");
                    }
                },

                error: function ()
                {
                  $(".red-alert-message").removeClass("hidden");
                }
            });

        })
    }

    quickmove_inventory_start_scanner()

    $(document).ready(function() {

        // var website = openerp.website;
        // website.add_template_file("/stock_quickmove/static/src/xml/picking.xml");
        $("select#quickmove_location_src_id").select9({
            placeholder: _t("Search location"),
            allowClear: true,
            ajax: {
                url: '/stock/quickmove_location_search',
                dataType: 'json',
            }
        });

        $("select#quickmove_location_dest_id").select9({
            placeholder: _t("Search location"),
            allowClear: true,
            ajax: {
                url: '/stock/quickmove_location_search/',
                dataType: 'json'
            }
        });
        $("select#quickmove_product_search").select9({
            placeholder: _t("Search product"),
            allowClear: true,
            ajax: {
                url: '/stock/quickmove_product_search/',
                dataType: 'json'
            }
        });

        function quickmove_product_change(){

            var self = $(this);
            var product_id = $('select#quickmove_product_search').val();
            var location_id = $('select#quickmove_location_src_id').val();

            if (location_id !== null){
                    ajax.jsonRpc("/stock/quickmove_get_product_stock", "call", {
                    'product_id': product_id,
                    'location_id': location_id,
                }).then(function(result){
                      if (result.length === 0) {
                          remove_all_product_lines();
                        }
                        else {
                        update_product_lines(result);
                        if ($('select#quickmove_location_src_id').val()){
                            $('#quickmove_location_dest_id').select9('focus');
                        }
                    }
                });
            }
        }

        $("select#quickmove_product_search").on('change.select9', quickmove_product_change);
        $("select#quickmove_location_src_id").on('change.select9', quickmove_product_change);

        // inventory
        $("select#inventory_product_search").select9({
            placeholder: _t("Search product"),
            allowClear: true,
            ajax: {
                url: '/stock/quickmove_product_search/',
                dataType: 'json'
            }
        });

        var focus = $.bbq.getState('focus');
        // focus = focus ? focus : 'quickmove_product_search';
        $('#' + focus).select9('open');
        if ($('#' + focus).val()){
             $('#quickmove_location_dest_id').select9('open');
        }


        // fix for random problem with templates not loaded in time
        setTimeout(function () {
            $("select#inventory_product_search").on('change.select9', function() {
                update_product_location_lines({"product_id":$(this).val()});
                }).change();
            var state = $.bbq.getState();
            if (state.location && state.location !== "" && state.product && state.product !== ""){
                ajax.jsonRpc("/stock/quickmove_get_product", "call", {
                        'product': state.product,
                    }).then(function(result){
                        var newOption = new Option(result.product_name, result.product_id, false, true);
                        $('select#quickmove_product_search').append(newOption).trigger('change');
                    })

                    ajax.jsonRpc("/stock/quickmove_get_location", "call", {
                            'location': state.location,
                        }).then(function(result){
                            var newOption = new Option(result.location_name, result.location_id, false, true);
                            $('select#quickmove_location_src_id').append(newOption).trigger('change');

                        if ($('select#quickmove_location_src_id').val()){
                            $('#quickmove_location_dest_id').select9('open');
                         }
                         else{
                            $('#quickmove_location_src_id').select9('open');
                         }
                    })
            }
            }, 500);

        $('form').submit(function() {
            $('.odoo-qm-transfer-button').addClass('disabled');
        })

    });

});

function quickmove_minus(e) {
    var input = e.closest("div").find("input");
    var val = input.val();
    if (parseInt(val) === 0) {
        input.val("0");
    }
    else {
        input.val(String(parseInt(val) - 1));
    }
    input.change();
}

function quickmove_plus(e) {
    var input = e.closest("div").find("input");
    var val = input.val();
    input.val(String(parseInt(val) + 1));
    input.change();

}

function quickmove_remove(e) {
    var tr = e.closest("tr").remove();
}


function set_confirm_enabled(e) {
    var elm = e.closest('tr').find('i.fa-check');
    elm.removeClass('disabled');
    elm.addClass('red_icon');
}

function quickmove_adjust(e) {
    var tr = e.parents('tr'),
        id = parseInt(tr.data('id')),
        product_id = parseInt($("select#inventory_product_search").val()),
        input = tr.find('input'),
        quantity = parseInt(input.val());
        tr.find('i.fa-check').removeClass('red_icon').addClass('disabled');

    // $.ajax.jsonRpc("/stock/inventory_adjust", "call", {
    //     'location_id': id, 'product_id': product_id, 'quantity':quantity
    // }).then(function(arg1,res){
    //     console.log(arguments);
    //     window.alert(res.data.message + '\n\n' + res.data.debug);
    //     }).then(function(res){
    // });

    var data = {
        'location_id': id,
        'product_id': product_id,
        'quantity':quantity
    }

    $.ajax({
        url: '/stock/inventory_adjust',
        dataType: 'json',
        type: 'POST',
        data: data,
        // data: JSON.stringify(data)
    }).then(function(arg1,res){
        console.log(arguments);
        window.alert(res.data.message + '\n\n' + res.data.debug);
        }).then(function(res){
    });
}
