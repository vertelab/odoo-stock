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


    
    openerp.web.client_actions.add('stock.ui.alt', 'instance.stock_barcode_alternative.BarcodeInterface');

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
