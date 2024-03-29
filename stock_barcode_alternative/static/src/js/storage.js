odoo.define('stock_barcode_alternative.Storage', function(require) {
    "use strict";

    var Widget = require('web.Widget');
    var ajax = require('web.ajax');
    var core = require('web.core');
    var publicWidget = require("web.public.widget");
    var _t = core._t;

    var QWeb = core.qweb;

    var Storage = core.Class.extend({
        init: function(parent, options){

        },
        getItem: function(key){
            return JSON.parse(sessionStorage.getItem(key));
        },
        setItem: function(key, value, timestamp){
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

    return {
        Storage: Storage
    }

});
