from odoo import api, fields, models, _
from odoo import http
from odoo.http import request
from odoo.tools import safe_eval as eval
import traceback

from odoo.modules.registry import Registry

import logging
_logger = logging.getLogger(__name__)

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.model
    def abc_scan(self, code):
        """Perform scan on the supplied barcode."""
        _logger.warning("victor hej"*999)
        resp = super(StockPicking, self).abc_scan(code)
        _logger.warning(f"victor resp {resp}")
        if(resp['type'] == 'no hit' or resp['type'] == 'product.product'):
            _logger.warning("victor no hit")
            products = self.env['product.product'].search(['|', ('ean13', '=', code), ('default_code', '=', code)])
            _logger.warning(f"victor products hit: {products}")
            if products:
                return {
                    'type': 'product.product',
                    'product': self.abc_make_records(products)}
        return resp






    # ~ def _abc_test_sleep(self, duration):
        # ~ sleep(duration)

    # ~ def abc_transfer_steps(self):
        # ~ steps = super(StockPicking, self).abc_transfer_steps()
        # ~ steps += [
            # ~ (0, 'abc_dn_set_qc'),
            # ~ (25, 'abc_dn_print_delivery_slip'),
            # ~ (35, 'abc_dn_print_unifaun_label'),
            # ~ (70, 'abc_dn_print_invoice')]
        # ~ return steps

    # ~ def abc_dn_label_printer(self):
        # ~ # TODO: Move report to this module
        # ~ report = self.env.ref('stock_barcode_wrapping_dermanord.dummy_report_unifaun_label')
        # ~ printer = report.behaviour()[report.id]['printer']
        # ~ if not printer:
            # ~ action = self.env['ir.actions.act_window'].for_xml_id('report', 'reports_action')
            # ~ url = 'http://localhost:8069/web?debug=#id=%s&view_type=form&model=ir.actions.report.xml&menu_id=%s&action=%s' % (report.id, menu.id, action.id)
            # ~ raise Warning(_("No label printer has been defined for you! Please check the print settings on the report 'Unifaun Label Print Settings'"))
        # ~ return printer

    # ~ def abc_confirm_invoice(self, lines, packages, data, params, res):
        # ~ """Confirm invoice. Split into its own function to not lock the invoice sequence."""
        # ~ # Check if this is a split picking
        # ~ if self.split_picking_ids or (self.unifaun_id and len(self.unifaun_id.picking_ids) > 1):
            # ~ return
        # ~ return super(StockPicking, self).abc_confirm_invoice(lines, packages, data, params, res)

    # ~ def abc_dn_set_qc(self, lines, packages, data, params, res):
        # ~ """Set Quality Controller"""
        # ~ if not self.qc_id:
            # ~ employee = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1)
            # ~ if employee:
                # ~ self.qc_id = employee

    # ~ def abc_dn_print_delivery_slip(self, lines, packages, data, params, res):
        # ~ """Print Stock Delivery Slip"""
        # ~ try:
            # ~ self.env['report'].print_document(self, 'stock_delivery_slip.stock_delivery_slip')
            # ~ report = self.env['report']._get_report_from_name('stock_delivery_slip.stock_delivery_slip')
            # ~ behaviour = report.behaviour()[report.id]
            # ~ printer = behaviour['printer']
            # ~ res['messages'].append(u"Skrev ut fraktsedel %s på skrivare %s." % (self.name, printer and printer.name or 'Unknown'))
        # ~ except Exception as e:
            # ~ res['warnings'].append((
                # ~ u"Något gick fel vid utskrift av fraktsedel!",
                # ~ '%s\n\nTraceback:\n%s' % (e.message, traceback.format_exc())))

    # ~ def abc_dn_print_unifaun_label(self, lines, packages, data, params, res):
        # ~ """Print Unifaun Label"""
        # ~ _logger.warn('\n\nunifaun_no_order: %s unifaun_pdf_ids: %s\n' % (data.get('unifaun_no_order', True), self.unifaun_pdf_ids))
        # ~ if not self.carrier_id.is_unifaun or data.get('unifaun_no_order') or not self.unifaun_pdf_ids:
            # ~ return
        # ~ res['results']['unifaun_label'] = 'failure'
        # ~ printer_name = 'Unknown'
        # ~ try:
            # ~ printer = self.get_label_printer()
            # ~ printer_name = printer.name
            # ~ for pdf in self.unifaun_pdf_ids:
                # ~ printer.print_document(None, base64.b64decode(pdf.attachment_id.datas), 'pdf')
            # ~ res['results']['unifaun_label'] = 'success'
            # ~ res['messages'].append(u"Skrev ut fraktetikett på skrivare %s" % printer_name)
        # ~ except Exception as e:
            # ~ res['warnings'].append((
                # ~ u"Kunde ej skriva ut fraktetikett på skrivare %s!" % printer_name,
                # ~ '%s\n\nTraceback:\n%s' % (e.message, traceback.format_exc())))

    # ~ def abc_dn_print_invoice(self, lines, packages, data, params, res):
        # ~ """Print the invoice, or send it by email."""
        # ~ invoice = params.get('invoice')
        # ~ if not invoice or invoice.state not in ('open', 'paid'):
            # ~ return
        # ~ invoice_type = (self.invoice_type_id and self.invoice_type_id.send_email and 'email') or 'in_package'
        # ~ invoice_name = invoice.number or invoice.name
        # ~ if invoice_type == 'email':
            # ~ # Send invoice by email
            # ~ try:
                # ~ email = invoice.partner_id.email
                # ~ if not email:
                    # ~ self.env['sale.order']
                    # ~ res['warnings'].append((
                        # ~ u"Kunde ej skicka faktura %s (id %s) via epost. Kunden har ingen epostadress inställd." % (invoice_name, invoice.id),
                        # ~ None))
                    # ~ return
                # ~ action = invoice.action_invoice_sent()
                # ~ wizard = self.env[action['res_model']].with_context(action['context']).create({})
                # ~ wizard_onchange = wizard.onchange(wizard.read()[0], 'template_id', wizard._onchange_spec())
                # ~ wizard.write(wizard_onchange.get('value', {}))
                # ~ wizard.send_mail()
                # ~ res['messages'].append(u"Skickade faktura %s till %s" % (invoice.number or invoice.name, email))
            # ~ except Exception as e:
                # ~ res['warnings'].append((
                    # ~ u"Kunde ej skicka faktura %s (id %s) via epost. Kunden har epostadress %s." % (invoice_name, invoice.id, email),
                    # ~ '%s\n\nTraceback:\n%s' % (e.message, traceback.format_exc())))
        # ~ else:
            # ~ # Print invoice
            # ~ printer_name = ''
            # ~ # Do not print invoices for this type
            # ~ if self.invoice_type_id == self.env.ref("invoice_type.invoice_webshop"):
                # ~ return
            # ~ try:
                # ~ default_report = invoice.commercial_partner_id.property_account_position.report_default.report_name
                # ~ report = self.env['report']._get_report_from_name(default_report)
                # ~ behaviour = report.behaviour()[report.id]
                # ~ printer_name = behaviour['printer'].name
                # ~ self.env['report'].print_document(invoice, default_report)
                # ~ res['messages'].append(u"Skrev ut faktura %s på skrivare %s." % (invoice_name, invoice.id))
            # ~ except Exception as e:
                # ~ res['warnings'].append((
                    # ~ u"Kunde ej skriva ut faktura %s (id %s) på skrivare %s." % (invoice_name, invoice.id, printer_name),
                    # ~ '%s\n\nTraceback:\n%s' % (e.message, traceback.format_exc())))
