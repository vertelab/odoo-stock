from odoo import models, fields, api, _
from zeep import Client, Settings
from zeep.transports import Transport
from requests import Session
from zeep.plugins import HistoryPlugin
from zeep.exceptions import Fault
from odoo.exceptions import UserError


class ResCompany(models.Model):
    _inherit = 'res.company'

    ongoing_wsdl = fields.Char(string="URL")
    ongoing_username = fields.Char(string="Username")
    ongoing_password = fields.Char(string="Password")

    @api.model
    def ongoing_client(self, action):
        """
            Creates ongoing client with custom headers.
        """
        if not action:
            raise UserError(_("Action is not defined"))

        headers = {
            'SOAPAction': f'http://ongoingsystems.se/WSI/{action}',
            'Content-Type': 'text/xml;charset=utf-8'
        }

        # Create a session and attach your custom headers
        session = Session()
        session.headers.update(headers)

        # Set settings (e.g., to allow large XML trees)
        settings = Settings(strict=False, xml_huge_tree=True)

        # Create a transport using the session
        transport = Transport(session=session)

        # Initialize the client with the transport and settings
        client = Client(
            'https://wms1.ongoingsystems.se/vertel/service.asmx?WSDL',
            settings=settings,
            transport=transport
        )
        return client

    @api.model
    def ongoing_auth(self):
        """
        Builds the XML structure for the authorization.
        """
        return {
            'GoodsOwnerCode': "Vertel AB",
            'UserName': self.ongoing_username,
            'Password': self.ongoing_password
        }

