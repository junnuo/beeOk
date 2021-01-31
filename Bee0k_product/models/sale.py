from odoo import fields, models, api

class Sale(models.Model):
    _inherit = 'sale.order'

    cart_quantity = fields.Float(compute='_compute_cart_info', string='Cart Quantity')

    @api.multi
    @api.depends('website_order_line.product_uom_qty', 'website_order_line.product_id')
    def _compute_cart_info(self):
        for order in self:
            order.cart_quantity = float(sum(order.mapped('website_order_line.product_uom_qty')))
            order.only_services = all(l.product_id.type in ('service', 'digital') for l in order.website_order_line)
