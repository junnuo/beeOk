from odoo import models, fields, api

class Product(models.Model):
    _inherit = 'product.template'

    technical_name = fields.Char(string='Nom technique')
    currency_id = fields.Many2one(
        'res.currency', 'Currency',
        required=True, compute='_get_currency_id')
    type = fields.Selection(selection_add=[('box', 'Box'), ('kraft', 'Kraft'), ('preparation_fees', 'Frais de préparation'), ('delivery_fees', 'Frais de livraison')])

    def get_curreny(self):
        return self.currency_id.name

    @api.depends('uom_id')
    def _get_currency_id(self):
        for rec in self:
            if rec.uom_id.name == 'kg':
                ekg_currency_id = self.env['res.currency'].search([('name','=','EKG')])
                if ekg_currency_id:
                    rec.currency_id = ekg_currency_id
            else:
                rec.currency_id = self.env.user.company_id.currency_id
