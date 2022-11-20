from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSaleForm
import json

day_mapping = {
    'monday': 'Lundi',
    'tuesday': 'Mardi',
    'wednesday': 'Mercredi',
    'thursday': 'Jeudi',
    'friday': 'Vendredi',
    'saturday': 'Samedi',
    'sunday': 'Dimanche',
}


class WebsiteSale(WebsiteSale):

    @http.route(['/shop/cart/update'], type='http', auth="public", methods=['POST'], website=True, csrf=False)
    def cart_update(sale_orderself, product_id, add_qty=1, set_qty=0, **kw):
        """This route is called when adding a product to cart (no options)."""
        sale_order = request.website.sale_get_order(force_create=True)
        if sale_order.state != 'draft':
            request.session['sale_order_id'] = None
            sale_order = request.website.sale_get_order(force_create=True)

        product_custom_attribute_values = None
        if kw.get('product_custom_attribute_values'):
            product_custom_attribute_values = json.loads(kw.get('product_custom_attribute_values'))

        no_variant_attribute_values = None
        if kw.get('no_variant_attribute_values'):
            no_variant_attribute_values = json.loads(kw.get('no_variant_attribute_values'))

        if kw.get('consigne', False) == 'box':
            container_id = request.env['product.product'].search([('type','=','box')]).id
        elif kw.get('consigne', False) == 'kraft':
            container_id = request.env['product.product'].search([('type','=','kraft')]).id
        else:
            container_id = False

        sale_order._cart_update(
            product_id=int(product_id),
            add_qty=add_qty,
            set_qty=set_qty,
            product_custom_attribute_values=product_custom_attribute_values,
            no_variant_attribute_values=no_variant_attribute_values,
            container=container_id,
        )

        if container_id:
            sale_order._cart_update(
                    product_id=container_id,
                    add_qty=1,
                    set_qty=0,
                )

        if not sale_order.order_line.filtered(lambda line: line.product_id.type == 'preparation_fees'):
            preparation_fees_id = request.env['product.product'].search([('type','=','preparation_fees')]).id
            sale_order._cart_update(
                product_id=preparation_fees_id,
                add_qty=1,
                set_qty=0,
            )

        if sale_order.order_line.filtered(lambda line: line.product_id.type == 'delivery_fees'):
            line = sale_order.order_line.filtered(lambda line: line.product_id.type == 'delivery_fees')
            if line:
                untaxed_amount = sale_order.amount_untaxed
                if untaxed_amount < 40.0:
                    delivery_fees = 4.96
                elif untaxed_amount < 70.0:
                    delivery_fees = 3.30
                elif untaxed_amount < 100.0:
                    delivery_fees = 1.65
                else:
                    delivery_fees = 0.0
                line.price_unit = delivery_fees

        return request.redirect("/shop/cart")


    @http.route(['/shop/cart/get_currency'], type='json', auth="public", methods=['POST'], website=True, csrf=False)
    def cart_get_product_currency(self, product_id):
        product = request.env['product.product'].browse(product_id)
        return product.currency_id.name


    @http.route(['/shop/payment'])
    def payment(self, **post):
        order = request.website.sale_get_order()
        if order.warning_low or order.warning_high or order.warning_low_take_away or order.warning_high_take_away or order.not_deliverable:
            return request.redirect('/shop/extra_info')
        if order.way_of_delivery == 'delivery' and not order.order_line.filtered(lambda line: line.product_id.type == 'delivery_fees'):
            order.order_line.filtered(lambda line: line.product_id.type == 'collect_point_fees').unlink()
            delivery_fees_id = request.env['product.product'].search([('type','=','delivery_fees')]).id
            order._cart_update(
                product_id=delivery_fees_id,
                add_qty=1,
            )
        if order.way_of_delivery == 'take_away' and order.order_line.filtered(lambda line: line.product_id.type == 'delivery_fees' or line.product_id.type == 'collect_point_fees'):
            order.order_line.filtered(lambda line: line.product_id.type == 'delivery_fees' or line.product_id.type == 'collect_point_fees').unlink()
        if (order.way_of_delivery == 'collect') and not order.order_line.filtered(lambda line: line.product_id.type == 'collect_point_fees'):
            order.order_line.filtered(lambda line: line.product_id.type == 'delivery_fees').unlink()
            collect_fees_id = request.env['product.product'].search([('type','=','collect_point_fees')]).id
            order._cart_update(
                product_id=collect_fees_id,
                add_qty=1,
            )
        return super(WebsiteSale, self).payment(**post)

    def _get_mandatory_shipping_fields(self):
        return ["name", "street", "city", "country_id", "zip"]

    @http.route(['/shop/address'], type='http', methods=['GET', 'POST'], auth="public", website=True, sitemap=False)
    def address(self, **kw):
        Partner = request.env['res.partner'].with_context(show_address=1).sudo()
        order = request.website.sale_get_order()

        redirection = self.checkout_redirection(order)
        if redirection:
            return redirection

        mode = (False, False)
        can_edit_vat = False
        def_country_id = order.partner_id.country_id
        values, errors = {}, {}

        partner_id = int(kw.get('partner_id', -1))

        # IF PUBLIC ORDER
        if order.partner_id.id == request.website.user_id.sudo().partner_id.id:
            mode = ('new', 'billing')
            can_edit_vat = True
            country_code = request.session['geoip'].get('country_code')
            if country_code:
                def_country_id = request.env['res.country'].search([('code', '=', country_code)], limit=1)
            else:
                def_country_id = request.website.user_id.sudo().country_id
        # IF ORDER LINKED TO A PARTNER
        else:
            if partner_id > 0:
                if partner_id == order.partner_id.id:
                    mode = ('edit', 'billing')
                    can_edit_vat = order.partner_id.can_edit_vat()
                else:
                    shippings = Partner.search([('id', 'child_of', order.partner_id.commercial_partner_id.ids)])
                    if partner_id in shippings.mapped('id'):
                        mode = ('edit', 'shipping')
                    else:
                        return Forbidden()
                if mode:
                    values = Partner.browse(partner_id)
            elif partner_id == -1:
                mode = ('new', 'shipping')
            else: # no mode - refresh without post?
                return request.redirect('/shop/checkout')

        # IF POSTED
        if 'submitted' in kw:
            pre_values = self.values_preprocess(order, mode, kw)
            errors, error_msg = self.checkout_form_validate(mode, kw, pre_values)
            post, errors, error_msg = self.values_postprocess(order, mode, pre_values, errors, error_msg)

            if errors or not kw.get('age_verification', False):
                errors['error_message'] = error_msg
                values = kw
            else:
                partner_id = self._checkout_form_save(mode, post, kw)
                if mode[1] == 'billing':
                    order.partner_id = partner_id
                    order.onchange_partner_id()
                    # This is the *only* thing that the front end user will see/edit anyway when choosing billing address
                    order.partner_invoice_id = partner_id
                    if not kw.get('use_same'):
                        kw['callback'] = kw.get('callback') or \
                            (not order.only_services and (mode[0] == 'edit' and '/shop/checkout' or '/shop/address'))
                elif mode[1] == 'shipping':
                    order.partner_shipping_id = partner_id

                order.message_partner_ids = [(4, partner_id), (3, request.website.partner_id.id)]
                if not errors:
                    return request.redirect(kw.get('callback') or '/shop/confirm_order')

        country = 'country_id' in values and values['country_id'] != '' and request.env['res.country'].browse(int(values['country_id']))
        country = country and country.exists() or def_country_id
        render_values = {
            'website_sale_order': order,
            'partner_id': partner_id,
            'mode': mode,
            'checkout': values,
            'can_edit_vat': can_edit_vat,
            'country': country,
            'countries': country.get_website_sale_countries(mode=mode[1]),
            "states": country.get_website_sale_states(mode=mode[1]),
            'error': errors,
            'callback': kw.get('callback'),
            'only_services': order and order.only_services,
        }
        if not kw.get('age_verification', False) and 'submitted' in kw:
            render_values['error_age'] = True
        return request.render("website_sale.address", render_values)


class WebsiteSaleForm(WebsiteSaleForm):

    @http.route('/website_form/shop.sale.order', type='http', auth="public", methods=['POST'], website=True)
    def website_form_saleorder(self, **kwargs):
        model_record = request.env.ref('sale.model_sale_order')
        try:
            data = self.extract_data(model_record, kwargs)
        except ValidationError as e:
            return json.dumps({'error_fields': e.args[0]})

        order = request.website.sale_get_order()
        order.warning_low = False
        order.warning_high = False
        order.warning_low_take_away = False
        order.warning_high_take_away = False
        order.first_date = False
        order.first_time = False
        order.first_time_end = False
        order.second_date = False
        order.second_time = False
        order.second_time_end = False
        order.third_date = False
        order.third_time = False
        order.third_time_end = False
        order.not_deliverable = False
        if data['record']:
            order.write(data['record'])

        if data['custom']:
            if kwargs.get('Give us your feedback', False):
                comments = kwargs['Give us your feedback']
                order.comments = comments

            time_slot_list = []
            for key in kwargs:
                if key.isdigit():
                    time_slot_list.append(int(key))

            if kwargs['choice'] == 'take_away':
                order.way_of_delivery = 'take_away'
                if len(time_slot_list) < 1:
                    order.warning_low_take_away = True
                elif len(time_slot_list) > 1:
                    order.warning_high_take_away = True
                else:
                    availability = request.env['delivery.availability'].browse(time_slot_list[0])
                    order.take_away_date = day_mapping[availability.day]
                    order.take_away_start_hour = availability.start_hour
                    order.take_away_end_hour = availability.end_hour
            elif kwargs['choice'] == 'delivery':
                order.way_of_delivery = 'delivery'
                if len(time_slot_list) > 3:
                    order.warning_high = True
                else:
                    if order.partner_shipping_id.zip not in request.env['delivery.availability.zone'].search([]).mapped('zip'):
                        order.not_deliverable = True
                    else:
                        if len(time_slot_list) < 1:
                            order.warning_low = True
                        if len(time_slot_list) > 0:
                            availability = request.env['delivery.availability'].browse(time_slot_list[0])
                            order.first_date = day_mapping[availability.day]
                            order.first_time = availability.start_hour
                            order.first_time_end = availability.end_hour
                        if len(time_slot_list) > 1:
                            availability = request.env['delivery.availability'].browse(time_slot_list[1])
                            order.second_date = day_mapping[availability.day]
                            order.second_time = availability.start_hour
                            order.second_time_end = availability.end_hour
                        if len(time_slot_list) > 2:
                            availability = request.env['delivery.availability'].browse(time_slot_list[2])
                            order.third_date = day_mapping[availability.day]
                            order.third_time = availability.start_hour
                            order.third_time_end = availability.end_hour
            elif kwargs['choice']:
                order.way_of_delivery = 'collect'
                order.write({'collect_point_id': int(kwargs['choice'])})
                if len(time_slot_list) < 1:
                    order.warning_low_take_away = True
                elif len(time_slot_list) > 1:
                    order.warning_high_take_away = True
                else:
                    availability = request.env['collect.availability'].browse(time_slot_list[0])
                    order.take_away_date = day_mapping[availability.day]
                    order.take_away_start_hour = availability.start_hour
                    order.take_away_end_hour = availability.end_hour
        else:
            order.warning_low = True

        if data['attachments']:
            self.insert_attachment(model_record, order.id, data['attachments'])

        return json.dumps({'id': order.id})
