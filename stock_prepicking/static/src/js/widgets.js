var picking = new openerp.web.Model('stock.picking');
var move = new openerp.web.Model('stock.move');

$(document).ready(function() {
    var pressed = false;
    var chars = [];
    $(window).keypress(function(e) {
        if (e.which >= 48 && e.which <= 57) {
            chars.push(String.fromCharCode(e.which));
        }
        if (pressed == false) {
            setTimeout(function(){
                if (chars.length >= 10) {
                    var barcode = chars.join("");
                    rfid_increment(barcode);
                }
                chars = [];
                pressed = false;
            },500);
        }
        pressed = true;
    });
});

$('.move_line_qty_input').live("keypress", function(e) {
    if (e.keyCode == 13) { // TODO: this is enter key, how about enter key on a tablet or other mobile devices?
        var self = this;
            if ($.isNumeric($(self).val())){
            move_line_set(($(self).attr("id").split("_"))[3], parseFloat($(self).val()));
        }
        else
            window.alert("Please enter a number!");
    }
});

function rfid_increment(barcode){
    picking.call('process_barcode_from_prepicking', [parseInt($("#current_picking").val()), barcode]).then(function(result){
        $("table").load(document.URL +  " table");
    });
}

function move_line_increment(move_id, increase){
    move.call('move_line_increment', [parseInt(move_id), increase]).then(function(result){
        if(result == true)
            $("#move_line_row_" + move_id).addClass("success");
        if(result == false)
            $("#move_line_row_" + move_id).removeClass("success");
        $("table").load(document.URL +  " table");
    });
}

function move_line_set(move_id, qty) {
    move.call('move_line_set', [parseInt(move_id), qty]).then(function(result){
        $("table").load(document.URL +  " table");
    });
}


