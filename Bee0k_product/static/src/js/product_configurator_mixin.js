odoo.define('Bee0k_product.ProductConfiguratorMixin', function (require) {
    'use strict';

    var ProductConfiguratorMixin = require('website_sale_stock.ProductConfiguratorMixin');
    var ajax = require('web.ajax');
    var core = require('web.core');
    var QWeb = core.qweb;
    var xml_load = ajax.loadXML(
        '/website_sale_stock/static/src/xml/website_sale_stock_product_availability.xml',
        QWeb
    );

    ProductConfiguratorMixin._onChangeCombinationStock = function (ev, $parent, combination) {
        var product_id = 0;
        // needed for list view of variants
        if ($parent.find('input.product_id:checked').length) {
            product_id = $parent.find('input.product_id:checked').val();
        } else {
            product_id = $parent.find('.product_id').val();
        }
        var isMainProduct = combination.product_id &&
            ($parent.is('.js_main_product') || $parent.is('.main_product')) &&
            combination.product_id === parseInt(product_id);
    
        if (!this.isWebsite || !isMainProduct){
            return;
        }
        
        if ($('#info_qty')[0]) {
            var qty_g = $parent.find('input[name="add_qty"]').val();
            var qty = qty_g/1000;
            document.getElementById("add_qty_kg").innerHTML = qty.toString()
            document.getElementById("add_qty_g").innerHTML = qty_g.toString()
        } else {
            var qty = $parent.find('input[name="add_qty"]').val();
        }
    
        $parent.find('#add_to_cart').removeClass('out_of_stock');
        if (combination.product_type === 'product' && _.contains(['always', 'threshold'], combination.inventory_availability)) {
            combination.virtual_available -= parseInt(combination.cart_qty);
            if (combination.virtual_available < 0) {
                combination.virtual_available = 0;
            }
            // Handle case when manually write in input
            if (qty > combination.virtual_available) {
                var $input_add_qty = $parent.find('input[name="add_qty"]');
                qty = combination.virtual_available || 1;
                $input_add_qty.val(qty);
                if ($('#info_qty')[0]) {
                    var qty_g = qty*1000;
                    document.getElementById("add_qty_kg").innerHTML = qty.toString()
                    document.getElementById("add_qty_g").innerHTML = qty_g.toString()
                }
            }
            if (qty > combination.virtual_available
                || combination.virtual_available < 0 || qty < 0) {
                $parent.find('#add_to_cart').addClass('disabled out_of_stock');
            }
        }
    
        xml_load.then(function () {
            $('.oe_website_sale')
                .find('.availability_message_' + combination.product_template)
                .remove();
    
            var $message = $(QWeb.render(
                'website_sale_stock.product_availability',
                combination
            ));
            $('div.availability_messages').html($message);
        });
    };
    return ProductConfiguratorMixin;
})


odoo.define('Bee0k_product.website_sale', function (require) {
    'use strict';

    // var ProductConfiguratorMixin = require('sale.ProductConfiguratorMixin');
    var sAnimations = require('website.content.snippets.animation');
    sAnimations.registry.WebsiteSale.include({
        events: _.extend({
            'focus .oe_cart input.js_quantity[data-product-id]': '_onFocusCartQuantity',
        }, sAnimations.registry.WebsiteSale.prototype.read_events),

        _onFocusCartQuantity: function(ev){
            $(this).data('val', ev.target.value);
        },

        _onChangeCartQuantity: function (ev) {
            var self = this
            var old_value = $(this).data('val')
            var $input = $(ev.currentTarget);
            if ($input.data('update_change')) {
                return;
            }
            var value = parseFloat($input.val() || 0, 10);
            if (isNaN(value)) {
                value = 1;
            }
            if (value % 1 != 0 && ($input.data('currency') != 'EKG' || $input.data('currency') != 'EGR')){
                ev.target.value = old_value
            }
            else {
                var $dom = $input.closest('tr');
                // var default_price = parseFloat($dom.find('.text-danger > span.oe_currency_value').text());
                var $dom_optional = $dom.nextUntil(':not(.optional_product.info)');
                var line_id = parseInt($input.data('line-id'), 10);
                var productIDs = [parseInt($input.data('product-id'), 10)];
                self._changeCartQuantity($input, value, $dom_optional, line_id, productIDs);
            }
        },

        _changeCartQuantity: function ($input, value, $dom_optional, line_id, productIDs) {
            _.each($dom_optional, function (elem) {
                $(elem).find('.js_quantity').text(value);
                productIDs.push($(elem).find('span[data-product-id]').data('product-id'));
            });
            $input.data('update_change', true);
            this._rpc({
                route: "/shop/cart/update_json",
                params: {
                    line_id: line_id,
                    product_id: parseInt($input.data('product-id'), 10),
                    set_qty: value
                },
            }).then(function (data) {
                $input.data('update_change', false);
                var check_value = parseFloat($input.val() || 0, 10);
                if (isNaN(check_value)) {
                    check_value = 1;
                }
                if (value !== check_value) {
                    $input.trigger('change');
                    return;
                }
                var $q = $(".my_cart_quantity");
                if (data.cart_quantity) {
                    $q.parents('li:first').removeClass('d-none');
                }
                else {
                    window.location = '/shop/cart';
                }
                $q.html(data.cart_quantity).hide().fadeIn(600);
                $input.val(data.quantity);
                $('.js_quantity[data-line-id='+line_id+']').val(data.quantity).html(data.quantity);
    
                $(".js_cart_lines").first().before(data['website_sale.cart_lines']).end().remove();
                $(".js_cart_summary").first().before(data['website_sale.short_cart_summary']).end().remove();
    
                if (data.warning) {
                    var cart_alert = $('.oe_cart').parent().find('#data_warning');
                    if (cart_alert.length === 0) {
                        $('.oe_cart').prepend('<div class="alert alert-danger alert-dismissable" role="alert" id="data_warning">'+
                                '<button type="button" class="close" data-dismiss="alert" aria-hidden="true">&times;</button> ' + data.warning + '</div>');
                    }
                    else {
                        cart_alert.html('<button type="button" class="close" data-dismiss="alert" aria-hidden="true">&times;</button> ' + data.warning);
                    }
                    $input.val(data.quantity);
                }
            });
        }
    })
})


odoo.define('Bee0k_product.website_sale_beeok', function (require) {
    'use strict';

    var OptionalProductsModal = require('sale.OptionalProductsModal');
    var sAnimations = require('website.content.snippets.animation')
    var website_sale = require('website_sale_options.website_sale');
    var core = require('web.core');
    var _t = core._t;

    website_sale.include({
        _onClickAdd: function (ev) {
            if ($('#info_qty')[0]){
                if ($('#kraft')[0] || $('#box')[0]){
                    var kraft = $('#kraft')[0].checked;
                    var box = $('#box')[0].checked;
                }
            }
            if (($('#kraft')[0] || $('#box')[0]) && $('#info_qty')[0] && (!kraft && !box)){
                $('#warning_container')[0].innerHTML = "Veuillez choisir un contenant avant d'ajouter le produit";
            }
            else if(!$('#info_qty')[0] && parseFloat($('input[name="add_qty"]').val() || 1) % 1 != 0){
                $('#warning_container')[0].innerHTML = "";
                $('#warning_unity')[0].innerHTML = "Veuillez choisir une valeur entière pour les produits à l'unité";
            }
            else {
                ev.preventDefault();
                return this._handleAdd($(ev.currentTarget).closest('form'));
            }
        },

        _handleAdd: function ($form) {
            var self = this;
            this.$form = $form;
            this.isWebsite = true;
    
            var productSelector = [
                'input[type="hidden"][name="product_id"]',
                'input[type="radio"][name="product_id"]:checked'
            ];
    
            var productReady = this.selectOrCreateProduct(
                $form,
                parseInt($form.find(productSelector.join(', ')).first().val(), 10),
                $form.find('.product_template_id').val(),
                false
            );
    
            return productReady.done(function (productId) {
                $form.find(productSelector.join(', ')).val(productId);
    
                var quantity = 1;
                self.rootProduct = {
                    product_id: productId,
                    quantity: quantity,
                    product_custom_attribute_values: self.getCustomVariantValues($form.find('.js_product')),
                    variant_values: self.getSelectedVariantValues($form.find('.js_product')),
                    no_variant_attribute_values: self.getNoVariantAttributeValues($form.find('.js_product'))
                };
    
                self.optionalProductsModal = new OptionalProductsModal($form, {
                    rootProduct: self.rootProduct,
                    isWebsite: true,
                    okButtonText: _t('Proceed to Checkout'),
                    cancelButtonText: _t('Continue Shopping'),
                    title: _t('Add to cart')
                }).open();
    
                self.optionalProductsModal.on('options_empty', null, self._onModalOptionsEmpty.bind(self));
                self.optionalProductsModal.on('update_quantity', null, self._onOptionsUpdateQuantity.bind(self));
                self.optionalProductsModal.on('confirm', null, self._onModalConfirm.bind(self));
                self.optionalProductsModal.on('back', null, self._onModalBack.bind(self));
    
                return self.optionalProductsModal.opened();
            });
        },
    })
    return sAnimations.registry.WebsiteSaleOptions;
})
