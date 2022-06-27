from odoo import models, fields, api

class Product(models.Model):
    _inherit = 'product.template'

    technical_name = fields.Char(string='Nom technique')
    currency_id = fields.Many2one(
        'res.currency', 'Currency',
        required=True, compute='_get_currency_id')
    type = fields.Selection(selection_add=[('box', 'Box'), ('kraft', 'Kraft'), ('preparation_fees', 'Frais de préparation'), ('delivery_fees', 'Frais de livraison'), ('consigne', 'Consigne'), ('collect_point_fees', 'Frais point de collecte')])
    has_consigne = fields.Boolean('Produit avec consigne')
    consigne_id = fields.Many2one('product.product', string='Consigne')
    need_box_kraft = fields.Boolean(string='Produit nécessitant une boite ou un sachet')
    qty_per_consigne = fields.Float(string='Quantité par consigne (gr)')
    
    def get_curreny(self):
        return self.currency_id.name

    @api.depends('uom_id')
    def _get_currency_id(self):
        for rec in self:
            if rec.uom_id.name == 'kg':
                ekg_currency_id = self.env['res.currency'].search([('name','=','EKG')])
                if ekg_currency_id:
                    rec.currency_id = ekg_currency_id
            elif rec.uom_id.name == '100g':
                gr_currency_id = self.env['res.currency'].search([('name','=','EGR')])
                if gr_currency_id:
                    rec.currency_id = gr_currency_id
            else:
                rec.currency_id = self.env.user.company_id.currency_id

class ProductCateg(models.Model):
    _inherit = 'product.category'

    is_fruit_vegetable = fields.Boolean(string='Fruit ou légume')
