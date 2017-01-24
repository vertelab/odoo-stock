var picking = new openerp.web.Model('stock.picking');
var move = new openerp.web.Model('stock.move');
var operation = new openerp.web.Model('stock.pack.operation');
var _t = new openerp.web._t;
var picking_id = window.location.href.substr(window.location.href.indexOf("picking_id=") + 11);
var prepicking_ids = [];
var todo_ids = [];

//~ $(document).ready(function() {
    //~ var pressed = false;
    //~ var chars = [];
    //~ $(window).keypress(function(e) {
        //~ if (e.which >= 48 && e.which <= 57) {
            //~ chars.push(String.fromCharCode(e.which));
        //~ }
        //~ if (pressed == false) {
            //~ setTimeout(function(){
                //~ if (chars.length >= 10) {
                    //~ var barcode = chars.join("");
                    //~ rfid_increment(barcode);
                //~ }
                //~ chars = [];
                //~ pressed = false;
            //~ },500);
        //~ }
        //~ pressed = true;
    //~ });
//~ });

//~ $('.move_line_qty_input').live("keypress", function(e) {
    //~ if (e.keyCode == 13) { // TODO: this is enter key, how about enter key on a tablet or other mobile devices?
        //~ var self = this;
            //~ if ($.isNumeric($(self).val())){
            //~ move_line_set(($(self).attr("id").split("_"))[3], parseFloat($(self).val()));
        //~ }
        //~ else
            //~ window.alert(_t("Please enter a number!"));
    //~ }
//~ });

//~ $("#js_select").live("change", function(){
    //~ var selection = $("#js_select").attr("value");
    //~ if (selection === "Prepick"){
        //~ $(".btn_prepick").removeClass("hidden");
        //~ $(".js_putinpack").addClass("hidden");
        //~ $(".js_drop_down").addClass("hidden");
        //~ $(".prepick_body").find(".js_prepick_minus, .js_prepick_qty, .js_prepick_plus").prop('disabled', false);
        //~ $(".js_row_qty").find(".js_minus, .js_qty, .js_plus").prop('disabled', true);
        //~ $.each($("table .js_pack_op_line:not(.processed)"), function(){
            //~ console.log($(this).attr("data-id"));
            //~ $(this).removeClass("hidden");
            //~ todo_ids.push(parseInt($(this).attr("data-id")));
        //~ });
    //~ }
    //~ if (selection === "ToDo"){
        //~ $(".btn_prepick").addClass("hidden");
        //~ $(".js_putinpack").removeClass("hidden");
        //~ $(".js_drop_down").removeClass("hidden");
        //~ $(".js_row_qty").find(".js_minus, .js_qty, .js_plus").prop('disabled', false);
    //~ }
    //~ if (selection === "Processed"){
        //~ $(".btn_prepick").addClass("hidden");
        //~ $.each($("table .js_op_table_todo").find(".success"), function(){
            //~ console.log($(this).attr("data-id"));
            //~ pack_op_ids.push(parseInt($(this).attr("data-id")));
        //~ });
    //~ }
//~ });

$(".btn_prepick").live("click", function(){
    $.each($("table .js_pack_op_line"), function(){
        console.log($(this).attr("data-id"));
        prepicking_ids.push(parseInt($(this).attr("data-id")));
    });
    //~ operation.call('action_waiting',[[parseInt(picking_id)], pack_op_ids])
    //~ picking.call('action_pack',[[parseInt(picking_id)], pack_op_ids])
    //~ .then(function(pack){
        //~ console.log(pack);
        //~ location.reload();
    //~ });
});

//~ $(".pack_from_cart").live("click", function(){
    //~ if(pack_op_ids.length > 0) {
        //~ picking.call('action_pack',[[parseInt(picking_id)], pack_op_ids])
        //~ .then(function(pack){
            //~ console.log(pack);
            //~ location.reload();
        //~ });
    //~ }
//~ });

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


//~ openerp.stock.PickingEditorWidget.include({
    //~ renderElement: function(){console.log('banna'); this._super();}
//~ });

