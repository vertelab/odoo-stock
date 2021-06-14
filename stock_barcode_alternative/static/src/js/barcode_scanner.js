odoo.define('stock_barcode_alternative.BarcodeScanner', function(require) {
    "use strict";

    var Class = require('web.Class');

    var BarcodeScanner = Class.extend({
         init: function(parent, options){
            this.timeout = 200; // The timeout to determine if we're scanning or typing
            this.last_parse = null; // The time of the last parsed character
            this.clear();
        },
        connect: function(callback){
            // Connect the scanner to a callback function.
            this.disconnect();
            var self = this;
            this.handler = function(e){
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
            return e.which === 13;

        },
        isStartChar: function(e) {
            // Check if the given action represents our start char.
            return false;
        }
    })
    return {
        BarcodeScanner: BarcodeScanner
    }

});
