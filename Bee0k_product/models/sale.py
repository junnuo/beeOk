from odoo import fields, models, api
from odoo.http import request

class Sale(models.Model):
    _inherit = 'sale.order'

    cart_quantity = fields.Float(compute='_compute_cart_info', string='Cart Quantity')
    caution_discount = fields.Monetary(compute='_amount_all', string="Remise consigne", store=True)
    first_date = fields.Char(string='Jour de livraison - Option 1')
    second_date = fields.Char(string='Jour de livraison - Option 2')
    third_date = fields.Char(string='Jour de livraison - Option 3')
    first_time = fields.Float(string='Heure de livraison - Option 1')
    second_time = fields.Float(string='Heure de livraison - Option 2')
    third_time = fields.Float(string='Heure de livraison - Option 3')
    first_time_end = fields.Float()
    second_time_end = fields.Float()
    third_time_end = fields.Float()
    warning_low = fields.Boolean()
    warning_high = fields.Boolean()
    warning_low_take_away = fields.Boolean()
    warning_high_take_away = fields.Boolean()
    take_away_date = fields.Char(string='Jour de récupération de la commande')
    take_away_start_hour = fields.Float()
    take_away_end_hour = fields.Float()
    not_deliverable = fields.Boolean()
    way_of_delivery = fields.Selection([('take_away', 'Emporter'), ('delivery', 'Livraison'), ('collect', 'Point de collecte: Strofilia'), ('collect2', 'Point de collecte: Erasmus')], string='Livraison/Emporter', default='take_away')
    comments = fields.Text(string='Commentaire')

    def action_confirm(self):
        super().action_confirm()
        self.partner_id.consigne_amount -= self.caution_discount
    
    @api.depends('order_line.price_total')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        for order in self:
            amount_untaxed = amount_tax = 0.0
            for line in order.order_line:
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
            amount_total = amount_untaxed + amount_tax
            if order.partner_id.consigne_amount <= amount_total:
                caution_discount = order.partner_id.consigne_amount
            else:
                caution_discount = amount_total
            order.update({
                'amount_untaxed': amount_untaxed,
                'amount_tax': amount_tax,
                'amount_total': amount_total - caution_discount,
                'caution_discount': caution_discount
            })

    @api.multi
    def _cart_update(self, product_id=None, line_id=None, add_qty=0, set_qty=0, **kwargs):
        if not add_qty and set_qty == 0 and not self._context.get('bypass_check', False):
            order_line = self.order_line.filtered(lambda line: line.id == line_id)
            container = order_line.consigne
            if container:
                container_line = self.order_line.filtered(lambda line: line.product_id.id == container.id)
                if container_line:
                    container_line.product_uom_qty -= 1
                    if container_line.product_uom_qty == 0:
                        container_line.unlink()
        add_qty_product = add_qty
        set_qty_product = set_qty
        if request.env['product.product'].browse(int(product_id)).currency_id.name == 'EKG' or request.env['product.product'].browse(int(product_id)).currency_id.name == 'EGR':
            if add_qty:
                add_qty_product = str(float(add_qty)/1000.0)
            if set_qty:
                set_qty_product = str(float(set_qty)/1000.0)
        product = request.env['product.product'].browse(int(product_id))
        consigne_product = product.consigne_id
        if consigne_product:
            add_qty_consigne = add_qty
            set_qty_consigne = set_qty

            if add_qty_consigne and product.qty_per_consigne:
                add_qty_consigne = float(add_qty_consigne) // product.qty_per_consigne
                if add_qty_consigne:
                    if add_qty % product.qty_per_consigne:
                        add_qty_consigne += 1
                else:
                    add_qty_consigne = 1
                add_qty_consigne = str(add_qty_consigne)
            
            if set_qty_consigne and product.qty_per_consigne:
                set_qty_consigne = float(set_qty_consigne) // product.qty_per_consigne
                if set_qty_consigne:
                    if set_qty % product.qty_per_consigne:
                        set_qty_consigne += 1
                else:
                    set_qty_consigne = 1
                set_qty_consigne = str(set_qty_consigne)

            consigne_line = self.order_line.filtered(lambda line: line.product_id.id == consigne_product.id)
            super()._cart_update(consigne_product.id, consigne_line.id, add_qty_consigne, set_qty_consigne, **kwargs)
        res = super()._cart_update(product_id, line_id, add_qty_product, set_qty_product, **kwargs)
        if kwargs.get('container', False):
            order_line = self.env['sale.order.line'].browse(res.get('line_id'))
            order_line.write({'consigne': kwargs.get('container')})
        if product_id and self.env['product.product'].browse(product_id).type == 'delivery_fees':
            order_line = self.env['sale.order.line'].browse(res.get('line_id'))
            untaxed_amount = order_line.order_id.amount_untaxed
            if untaxed_amount < 40.0:
                delivery_fees = 4.96
            elif untaxed_amount < 70.0:
                delivery_fees = 3.30
            elif untaxed_amount < 100.0:
                delivery_fees = 1.65
            else:
                delivery_fees = 0.0
            order_line.price_unit = delivery_fees

        if self.order_line:
            list1 = ['consu', 'service', 'product']
            if not any(item in list1 for item in self.order_line.mapped('product_id.type')):
                self.order_line.unlink()
        return res

    @api.multi
    @api.depends('website_order_line.product_uom_qty', 'website_order_line.product_id')
    def _compute_cart_info(self):
        for order in self:
            order.cart_quantity = float(sum(order.mapped('website_order_line.product_uom_qty')))
            order.only_services = all(l.product_id.type in ('service', 'digital') for l in order.website_order_line)


class SaleLine(models.Model):
    _inherit = 'sale.order.line'

    consigne = fields.Many2one('product.product', string="Conteneur")


class Website(models.Model):
    _inherit = 'website'

    @api.multi
    def sale_get_order(self, force_create=False, code=None, update_pricelist=False, force_pricelist=False):
        """ Return the current sales order after mofications specified by params.
        :param bool force_create: Create sales order if not already existing
        :param str code: Code to force a pricelist (promo code)
                         If empty, it's a special case to reset the pricelist with the first available else the default.
        :param bool update_pricelist: Force to recompute all the lines from sales order to adapt the price with the current pricelist.
        :param int force_pricelist: pricelist_id - if set,  we change the pricelist with this one
        :returns: browse record for the current sales order
        """
        self.ensure_one()
        partner = self.env.user.partner_id
        sale_order_id = request.session.get('sale_order_id')
        if not sale_order_id:
            last_order = partner.last_website_so_id
            available_pricelists = self.get_pricelist_available()
            # Do not reload the cart of this user last visit if the cart uses a pricelist no longer available.
            sale_order_id = last_order.pricelist_id in available_pricelists and last_order.id

        pricelist_id = request.session.get('website_sale_current_pl') or self.get_current_pricelist().id

        if self.env['product.pricelist'].browse(force_pricelist).exists():
            pricelist_id = force_pricelist
            request.session['website_sale_current_pl'] = pricelist_id
            update_pricelist = True

        if not self._context.get('pricelist'):
            self = self.with_context(pricelist=pricelist_id)

        # Test validity of the sale_order_id
        sale_order = self.env['sale.order'].with_context(force_company=request.website.company_id.id).sudo().browse(sale_order_id).exists() if sale_order_id else None

        # create so if needed
        if not sale_order and (force_create or code):
            # TODO cache partner_id session
            pricelist = self.env['product.pricelist'].browse(pricelist_id).sudo()
            so_data = self._prepare_sale_order_values(partner, pricelist)
            sale_order = self.env['sale.order'].with_context(force_company=request.website.company_id.id).sudo().create(so_data)

            # set fiscal position
            if request.website.partner_id.id != partner.id:
                sale_order.onchange_partner_shipping_id()
            else: # For public user, fiscal position based on geolocation
                country_code = request.session['geoip'].get('country_code')
                if country_code:
                    country_id = request.env['res.country'].search([('code', '=', country_code)], limit=1).id
                    fp_id = request.env['account.fiscal.position'].sudo().with_context(force_company=request.website.company_id.id)._get_fpos_by_region(country_id)
                    sale_order.fiscal_position_id = fp_id
                else:
                    # if no geolocation, use the public user fp
                    sale_order.onchange_partner_shipping_id()

            request.session['sale_order_id'] = sale_order.id

        if sale_order:
            # case when user emptied the cart
            if not request.session.get('sale_order_id'):
                request.session['sale_order_id'] = sale_order.id

            # check for change of pricelist with a coupon
            pricelist_id = pricelist_id or partner.property_product_pricelist.id

            # check for change of partner_id ie after signup
            if sale_order.partner_id.id != partner.id and request.website.partner_id.id != partner.id:
                flag_pricelist = False
                if pricelist_id != sale_order.pricelist_id.id:
                    flag_pricelist = True
                fiscal_position = sale_order.fiscal_position_id.id

                # change the partner, and trigger the onchange
                sale_order.write({'partner_id': partner.id})
                sale_order.onchange_partner_id()
                sale_order.write({'partner_invoice_id': partner.id})
                sale_order.onchange_partner_shipping_id() # fiscal position
                sale_order['payment_term_id'] = self.sale_get_payment_term(partner)

                # check the pricelist : update it if the pricelist is not the 'forced' one
                values = {}
                if sale_order.pricelist_id:
                    if sale_order.pricelist_id.id != pricelist_id:
                        values['pricelist_id'] = pricelist_id
                        update_pricelist = True

                # if fiscal position, update the order lines taxes
                if sale_order.fiscal_position_id:
                    sale_order._compute_tax_id()

                # if values, then make the SO update
                if values:
                    sale_order.write(values)

                # check if the fiscal position has changed with the partner_id update
                recent_fiscal_position = sale_order.fiscal_position_id.id
                if flag_pricelist or recent_fiscal_position != fiscal_position:
                    update_pricelist = True

            if code and code != sale_order.pricelist_id.code:
                code_pricelist = self.env['product.pricelist'].sudo().search([('code', '=', code)], limit=1)
                if code_pricelist:
                    pricelist_id = code_pricelist.id
                    update_pricelist = True
            elif code is not None and sale_order.pricelist_id.code and code != sale_order.pricelist_id.code:
                # code is not None when user removes code and click on "Apply"
                pricelist_id = partner.property_product_pricelist.id
                update_pricelist = True

            # update the pricelist
            if update_pricelist:
                request.session['website_sale_current_pl'] = pricelist_id
                values = {'pricelist_id': pricelist_id}
                sale_order.write(values)
                for line in sale_order.order_line:
                    if line.exists():
                        sale_order.with_context(bypass_check=True)._cart_update(product_id=line.product_id.id, line_id=line.id, add_qty=0)

        else:
            request.session['sale_order_id'] = None
            return self.env['sale.order'].with_context(force_company=request.website.company_id.id)

        return sale_order
