from odoo import models, fields

class Contact(models.Model):
    _inherit = 'res.partner'

    consigne_amount = fields.Monetary(string='Montant Consigne', default=0)
