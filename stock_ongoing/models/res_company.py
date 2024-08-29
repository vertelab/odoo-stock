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
    ongoing_owner_code = fields.Char(string="GoodsOwnerCode")

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

        # Create a session and attach custom headers
        session = Session()
        session.headers.update(headers)
        settings = Settings(strict=False, xml_huge_tree=True)

        # Create a transport using the session
        transport = Transport(session=session)

        # Initialize the client with the transport and settings
        client = Client(
            self.ongoing_wsdl,
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
            'GoodsOwnerCode': self.ongoing_owner_code,
            'UserName': self.ongoing_username,
            'Password': self.ongoing_password
        }

