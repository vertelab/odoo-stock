var picking = new openerp.web.Model('stock.picking');
var move = new openerp.web.Model('stock.move');

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
                    prepicking_increment(barcode);
                }
                chars = [];
                pressed = false;
            },500);
        }
        pressed = true;
    });
});

function prepicking_increment(barcode){
    picking.call('process_barcode_from_prepicking', [parseInt($("#current_picking").val()), barcode]).then(function(result){
        $("table").load(document.URL +  " table");
    });
}

function move_line_increment(move_id, increase){
    move.call('move_line_increment', [parseInt(move_id), increase]).then(function(result){
        if(result == true)
            $("#move_line_row_" + move_id).attr({"class": "success"});
        if(result == false)
            $("#move_line_row_" + move_id).removeClass("success");
        $("table").load(document.URL +  " table");
    });
}

function rewrite_qty(move_id) {
    console.log($("#move_line_qty_" + move_id).val());
}
