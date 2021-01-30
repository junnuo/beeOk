from odoo import models, fields

class Product(models.Model):
    _inherit = 'product.template'

    technical_name = fields.Char(string='Nom technique')
