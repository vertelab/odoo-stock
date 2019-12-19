function openerp_picking_alt_widgets_unifaun(instance){
    console.log('openerp_picking_alt_widgets_unifaun');
    var module = instance.stock_barcode_alternative;
    var _t     = instance.web._t;
    var QWeb   = instance.web.qweb;
    
    module.OperationEditorWidget = instance.stock_barcode_alternative.OperationEditorWidget.extend({
        
    });
    
    module.PackageEditorWidget = instance.stock_barcode_alternative.PackageEditorWidget.extend({
        
    });
    
    module.PickingEditorWidget = instance.stock_barcode_alternative.PickingEditorWidget.extend({
        transfer_done: function(result){
            
            return this._super(result);
        }
    });
}

openerp.stock_barcode_alternative_original_unifaun = openerp.stock_barcode_alternative;
openerp.stock_barcode_alternative = function(openerp) {
    openerp.stock_barcode_alternative_original_unifaun(openerp);
    openerp_picking_alt_widgets_unifaun(openerp);
}
