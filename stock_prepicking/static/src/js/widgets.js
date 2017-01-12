$(document).ready(function() {
    var pressed = false;
    var chars = [];
    $(window).keypress(function(e) {
        if (e.which >= 48 && e.which <= 57) {
            chars.push(String.fromCharCode(e.which));
        }
        console.log(e.which + ":" + chars.join("|"));
        if (pressed == false) {
            setTimeout(function(){
                if (chars.length >= 10) {
                    var barcode = chars.join("");
                    console.log("Barcode Scanned: " + barcode);
                    console.log(barcode);
                    var move = new openerp.web.Model('stock.picking');
                    move.call('process_barcode_from_prepicking', [parseInt($("#current_picking").val()), barcode]).then(function(result){
                        console.log(result);
                    });
                }
                chars = [];
                pressed = false;
            },500);
        }
        pressed = true;
    });
});
