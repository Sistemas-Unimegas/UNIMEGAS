"use strict";
odoo.define('pos_retail.screen_order_widget', function (require) {

    var screens = require('point_of_sale.screens');
    var core = require('web.core');
    var _t = core._t;
    var ServiceChargeWidget = require('pos_retail.service_charge');
    var rpc = require('pos.rpc');

    screens.OrderWidget.include({
        init: function (parent, options) {
            var self = this;
            this.decimal_point = _t.database.parameters.decimal_point;
            this._super(parent, options);
            this.pos.bind('change:mode', function () {
                self.change_mode();
            });
            this.inputbuffer = "";
        },
        change_line_selected: function (keycode) {
            var order = this.pos.get_order();
            var line_selected = order.get_selected_orderline();
            if (!line_selected && order && order.orderlines.models.length > 0) {
                this.pos.get_order().select_orderline(order.orderlines.models[0]);
                this.numpad_state.reset();
            }
            if (line_selected && order && order.orderlines.models.length > 1) {
                $('.orderline').removeClass('selected');
                for (var i = 0; i < order.orderlines.models.length; i++) {
                    var line_check = order.orderlines.models[i];
                    if (line_check.cid == line_selected.cid) {
                        if (keycode == 38) {
                            if ((i - 1) >= 0) {
                                var line_will_select = order.orderlines.models[i - 1];
                                this.pos.get_order().select_orderline(line_will_select);
                                this.numpad_state.reset();
                                break;
                            }
                        } else {
                            var line_will_select = order.orderlines.models[i + 1];
                            this.pos.get_order().select_orderline(line_will_select);
                            this.numpad_state.reset();
                            break;
                        }
                    }
                }
            }
        },
        click_line: function (orderline, event) {
            this._super(orderline, event);
            var order = this.pos.get_order();
            if (order && order.get_selected_orderline()) {
                var line = order.get_selected_orderline();
                this.inputbuffer = "";
                this.firstinput = true;
                var mode = this.numpad_state.get('mode');
                if (mode === 'quantity') {
                    this.inputbuffer = line['quantity'].toString();
                } else if (mode === 'discount') {
                    this.inputbuffer = line['discount'].toString();
                } else if (mode === 'price') {
                    this.inputbuffer = line['price'].toString();
                }
                if (mode == 'quantity') {
                    this.$('.qty').addClass('selected-mode');
                    this.$('.price-unit').removeClass('selected-mode');
                    this.$('.discount').removeClass('selected-mode');
                }
                if (mode == 'discount') {
                    this.$('.discount').addClass('selected-mode');
                    this.$('.price-unit').removeClass('selected-mode');
                    this.$('.qty').removeClass('selected-mode');
                }
                if (mode == 'price') {
                    this.$('.price-unit').addClass('selected-mode');
                    this.$('.discount').removeClass('selected-mode');
                    this.$('.qty').removeClass('selected-mode');
                }
            }
        },
        change_mode: function () {
            this.inputbuffer = "";
            this.firstinput = true;
            var mode = this.numpad_state.get('mode');
        },
        change_selected_order: function () {
            this._super();
            var order = this.pos.get_order();
            if (order) {
                var product_ids = [];
                for (var i = 0; i < order.orderlines.models.length; i++) {
                    product_ids.push(order.orderlines.models[i].product.id)
                }
            }
        },
        render_orderline: function (orderline) {
            var self = this;
            var el_node = this._super(orderline);
            this._change_event_line(orderline);
            var el_edit_item = el_node.querySelector('.edit-item');
            if (el_edit_item) {
                el_edit_item.addEventListener('click', (function () {
                    self.pos.hide_selected_line_detail = false;
                    self.pos.trigger('selected:line', self.pos.get_order().get_selected_orderline())
                }.bind(this)));
            }
            var el_remove_item = el_node.querySelector('.remove-item');
            if (el_remove_item) {
                el_remove_item.addEventListener('click', (function () {
                    var selected_line = self.pos.get_order().get_selected_orderline();
                    if (selected_line) {
                        selected_line.order.remove_orderline(selected_line);
                    }
                }.bind(this)));
            }
            return el_node;
        },
        remove_shopping_cart: function () {
            var self = this;
            var order = self.pos.get_order();
            var selected_orderline = order.selected_orderline;
            if (order && selected_orderline) {
                order.remove_orderline(selected_orderline);
            } else {
                return self.pos.gui.show_popup('dialog', {
                    title: _t('Advertencia'),
                    body: _t('El carrito de compras está vacío'),
                })
            }
        },
        set_tags: function () {
            var self = this;
            var order = self.pos.get_order();
            if (order && order.selected_orderline) {
                var selected_orderline = order.selected_orderline;
                return self.gui.show_popup('popup_selection_tags', {
                    selected_orderline: selected_orderline,
                    title: _t('Agregar etiquetas')
                });
            } else {
                return self.pos.gui.show_popup('dialog', {
                    title: _t('Advertencia'),
                    body: _t('El carrito de compras está vacío'),
                })
            }
        },
        set_reason_return: function () {
            var self = this;
            var order = self.pos.get_order();
            if (order && order.selected_orderline) {
                return self.gui.show_popup('popup_selection_tags', {
                    selected_orderline: order.selected_orderline,
                    title: _t('Agregar motivos de devolución'),
                    tags: self.pos.return_reasons,
                });
            }
        },
        set_note: function () {
            var self = this;
            var order = self.pos.get_order();
            if (order && order.selected_orderline) {
                var selected_orderline = order.selected_orderline;
                self.pos.gui.show_popup('popup_add_order_line_note', {
                    title: _t('Agregar una nota a la línea seleccionada'),
                    value: selected_orderline.get_line_note(),
                    confirm: function (note) {
                        selected_orderline.set_line_note(note);
                    }
                });
            } else {
                return self.pos.gui.show_popup('confirm', {
                    title: _t('Advertencia'),
                    body: _t('Su carrito de compras está vacío'),
                })
            }
        },
        set_unit: function () {
            var self = this;
            var order = self.pos.get_order();
            var selected_orderline = order.selected_orderline;
            if (order) {
                if (selected_orderline) {
                    selected_orderline.change_unit();
                } else {
                    return self.pos.gui.show_popup('dialog', {
                        title: _t('Advertencia'),
                        body: _t('Selecciona una línea'),
                    });
                }
            } else {
                return self.pos.gui.show_popup('dialog', {
                    title: _t('Advertencia'),
                    body: _t('Líneas de la Orden está vacía'),
                });
            }
        },
        set_seller: function () {
            var self = this;
            var sellers = self.pos.sellers;
            return self.pos.gui.show_popup('popup_selection_extend', {
                title: _t('Selecciona el vendedor'),
                fields: ['name', 'email', 'id'],
                sub_datas: sellers,
                sub_template: 'sale_persons',
                body: _t('Selecciona un vendedor (a)'),
                confirm: function (user_id) {
                    var seller = self.pos.user_by_id[user_id];
                    var order = self.pos.get_order();
                    if (order && order.get_selected_orderline()) {
                        return order.get_selected_orderline().set_sale_person(seller)
                    } else {
                        self.pos.gui.show_popup('dialog', {
                            title: _t('Advertencia'),
                            body: _t('No ha seleccionado la línea, seleccione una línea antes de agregar al vendedor')
                        })
                    }
                }
            })
        },
        remove_orderline: function (order_line) {
            try {
                this._super(order_line);
            } catch (ex) {
                console.error('no te preocupes, cliente sin mesa seleccionada: ' + ex);
            }
            this.pos.trigger('selected:line', null);
            var order = this.pos.get_order();
            if (order && order.orderlines.length == 0) {
                order.is_return = false; // TODO: cashier select pos order and click return, they clear cart and made to order normal
                this.pos.trigger('hide:orderline-detail');
            }
        },
        set_value: function (val) {
            var self = this;
            var mode = this.numpad_state.get('mode');
            var order = this.pos.get_order();
            if (!order) {
                return false;
            }
            var line_selected = order.get_selected_orderline();
            if (!line_selected) {
                return false;
            }
            if (mode == 'discount' && this.pos.config.discount_limit && line_selected) { // TODO: Security limit discount filter by cashiers
                this.gui.show_popup('number', {
                    'title': _t('¿Qué porcentaje de descuento aplicaría? ?'),
                    'value': self.pos.config.discount_limit_amount,
                    'confirm': function (discount) {
                        if (discount > self.pos.config.discount_limit_amount) {
                            if (self.pos.config.discount_unlock_by_manager) {
                                var manager_validate = [];
                                _.each(self.pos.config.manager_ids, function (user_id) {
                                    var user = self.pos.user_by_id[user_id];
                                    if (user) {
                                        manager_validate.push({
                                            label: user.name,
                                            item: user
                                        })
                                    }
                                });
                                if (manager_validate.length == 0) {
                                    return self.pos.gui.show_popup('confirm', {
                                        title: _t('Advertencia'),
                                        body: _t('No se pudo establecer un descuento mayor que: ') + self.pos.config.discount_limit_amount + _t(' . Si es necesario, necesita la aprobación del administrador, pero los usuarios del administrador no han establecido la posición en la pestaña Seguridad.'),
                                    })
                                }
                                return self.pos.gui.show_popup('selection', {
                                    title: _t('Validar la selección del gerente'),
                                    body: _t('Solo un gerente puede aprobar este descuento, por favor pregúntele.'),
                                    list: manager_validate,
                                    confirm: function (manager_user) {
                                        if (!manager_user.pos_security_pin) {
                                            return self.pos.gui.show_popup('confirm', {
                                                title: _t('Advertencia'),
                                                body: manager_user.name + _t(' no ha puesto pin de seguridad pos antes. Primero configure el pin de seguridad pos')
                                            })
                                        } else {
                                            return self.pos.gui.show_popup('ask_password', {
                                                title: _t('Pos PIN de seguridad del gerente'),
                                                body: _t('Su personal necesita aprobar el descuento es ') + discount + _t(' por favor apruébalo'),
                                                confirm: function (password) {
                                                    if (manager_user['pos_security_pin'] != password) {
                                                        self.pos.gui.show_popup('dialog', {
                                                            title: _t('Error'),
                                                            body: _t('PIN de seguridad POS de ') + manager_user.name + _t(' no es correcto !')
                                                        });
                                                    } else {
                                                        var selected_line = order.get_selected_orderline();
                                                        selected_line.manager_user = manager_user;
                                                        return selected_line.set_discount(discount);
                                                    }
                                                }
                                            });
                                        }
                                    }
                                })
                            } else {
                                return self.gui.show_popup('dialog', {
                                    title: _t('Advertencia'),
                                    body: _t('No puede establecer un descuento mayor que ') + self.pos.config.discount_limit_amount + _t('. Comuníquese con su gerente de posición y establezca un valor mayor'),
                                })
                            }
                        } else {
                            order.get_selected_orderline().set_discount(discount);
                        }
                    }
                });
            } else {
                if (this.pos.config.validate_remove_line && val == 'remove' && this.pos.get_order() && this.pos.get_order().get_selected_orderline()) {
                    return this.pos._validate_by_manager("this.pos.get_order().remove_orderline(this.pos.get_order().get_selected_orderline())", 'Eliminar línea seleccionada');
                }
                this._super(val);
            }
        },
        set_lowlight_order: function (buttons) {
            for (var button_name in buttons) {
                buttons[button_name].highlight(false);
            }
        },
        active_button_combo_item_add_lot: function (buttons, selected_order) { // active button set combo
            if (selected_order.selected_orderline && buttons && buttons.button_combo_item_add_lot) {
                var has_combo_item_tracking_lot = selected_order.selected_orderline.has_combo_item_tracking_lot();
                buttons.button_combo_item_add_lot.highlight(has_combo_item_tracking_lot);
            }
        },
        active_internal_transfer_button: function (buttons, selected_order) { // active button set combo
            if (buttons && buttons.internal_transfer_button) {
                var active = selected_order.validation_order_can_do_internal_transfer();
                buttons.internal_transfer_button.highlight(active);
            }
        },
        active_button_create_purchase_order: function (buttons, selected_order) {
            if (buttons.button_create_purchase_order) {
                if (selected_order.orderlines.length > 0 && selected_order.get_client()) {
                    buttons.button_create_purchase_order.highlight(true);
                } else {
                    buttons.button_create_purchase_order.highlight(false);
                }
            }
        },
        active_button_variants: function (buttons, selected_order) {
            if (buttons.button_add_variants) {
                if (selected_order.selected_orderline && this.pos.variant_by_product_tmpl_id[selected_order.selected_orderline.product.product_tmpl_id]) {
                    buttons.button_add_variants.highlight(true);
                } else {
                    buttons.button_add_variants.highlight(false);
                }
            }
        },
        active_medical_insurance: function (buttons, selected_order) {
            if (buttons.button_medical_insurance_screen) {
                if (selected_order.medical_insurance) {
                    buttons.button_medical_insurance_screen.highlight(true);
                } else {
                    buttons.button_medical_insurance_screen.highlight(false);
                }
            }
        },
        active_reprint_last_order: function (buttons, selected_order) {
            if (buttons.button_print_last_order) {
                if (this.pos.report_html) {
                    buttons.button_print_last_order.highlight(true);

                } else {
                    buttons.button_print_last_order.highlight(false);
                }
            }
        },
        active_button_cash_management: function (buttons) {
            if (buttons.button_cash_management) {
                buttons.button_cash_management.highlight(true);
            }
        },
        set_total_gift: function (total_gift) {
            $('.total_gift').html(total_gift);
        },
        _change_event_line: function (line) {
            console.log('-------------------------------')
            if (line.order.pricelist && this.pos.config.use_pricelist) {
                $(this.chrome.screens['products'].order_widget.el).find('.pricelist').removeClass('oe_hidden');
                $(this.chrome.screens['products'].order_widget.el).find('.pricelist .pricelist-name').text(line.order.pricelist.display_name);
                $(this.chrome.screens['products'].order_widget.el).find('.pricelist').addClass('selected-mode');
            } else {
                $(this.chrome.screens['products'].order_widget.el).find('.pricelist').addClass('oe_hidden');
            }
            if (line.order.get_client()) {
                $(this.chrome.screens['products'].order_widget.el).find('.shipping-order').addClass('highlight');
                $(this.chrome.screens['products'].order_widget.el).find('.find-order').addClass('highlight');
            } else {
                $(this.chrome.screens['products'].order_widget.el).find('.shipping-order').removeClass('highlight');
                $(this.chrome.screens['products'].order_widget.el).find('.find-order').removeClass('highlight');
            }
            if (this.pos.config.service_charge_ids) {
                $(this.chrome.screens['products'].order_widget.el).find('.service-charge').removeClass('oe_hidden');
                $(this.chrome.screens['products'].order_widget.el).find('.service-charge').addClass('highlight');
            } else {
                $(this.chrome.screens['products'].order_widget.el).find('.service-charge').addClass('oe_hidden');
                $(this.chrome.screens['products'].order_widget.el).find('.service-charge').removeClass('highlight');
            }
            if (this.pos.config.print_voucher) {
                $(this.chrome.screens['products'].order_widget.el).find('.edit_voucher_card').removeClass('oe_hidden');
                $(this.chrome.screens['products'].order_widget.el).find('.edit_voucher_card').addClass('highlight');
            } else {
                $(this.chrome.screens['products'].order_widget.el).find('.edit_voucher_card').addClass('oe_hidden');
                $(this.chrome.screens['products'].order_widget.el).find('.edit_voucher_card').removeClass('highlight');
            }
            if (this.pos.config.create_quotation) {
                $(this.chrome.screens['products'].order_widget.el).find('.create_quotation').removeClass('oe_hidden');
                $(this.chrome.screens['products'].order_widget.el).find('.create_quotation').addClass('highlight');
            } else {
                $(this.chrome.screens['products'].order_widget.el).find('.create_quotation').addClass('oe_hidden');
                $(this.chrome.screens['products'].order_widget.el).find('.create_quotation').removeClass('highlight');
            }
            if (this.pos.config.required_reason_return) {
                $(this.chrome.screens['products'].order_widget.el).find('.input_reason_return').removeClass('oe_hidden');
                $(this.chrome.screens['products'].order_widget.el).find('.input_reason_return').addClass('highlight');
            } else {
                $(this.chrome.screens['products'].order_widget.el).find('.input_reason_return').addClass('oe_hidden');
                $(this.chrome.screens['products'].order_widget.el).find('.input_reason_return').removeClass('highlight');
            }
            $(this.chrome.screens['products'].order_widget.el).find('.remove_shopping_cart').addClass('selected-mode');
            if (line.is_return && this.pos.config.required_reason_return) {
                $(this.chrome.screens['products'].order_widget.el).find('.input_reason_return').removeClass('oe_hidden');
                $(this.chrome.screens['products'].order_widget.el).find('.input_reason_return').addClass('highlight');
            } else {
                $(this.chrome.screens['products'].order_widget.el).find('.input_reason_return').addClass('oe_hidden');
                $(this.chrome.screens['products'].order_widget.el).find('.input_reason_return').removeClass('highlight');
            }
            if (this.pos.config.add_sale_person && this.pos.sellers && this.pos.sellers.length > 0) {
                $(this.chrome.screens['products'].order_widget.el).find('.set_seller').removeClass('oe_hidden');
                $(this.chrome.screens['products'].order_widget.el).find('.set_seller').addClass('highlight');
            } else {
                $(this.chrome.screens['products'].order_widget.el).find('.set_seller').addClass('oe_hidden');
                $(this.chrome.screens['products'].order_widget.el).find('.set_seller').removeClass('highlight');
            }
            if (this.pos.config.note_orderline) {
                $(this.chrome.screens['products'].order_widget.el).find('.set_note').removeClass('oe_hidden');
                $(this.chrome.screens['products'].order_widget.el).find('.set_note').addClass('highlight');
            } else {
                $(this.chrome.screens['products'].order_widget.el).find('.set_note').addClass('oe_hidden');
                $(this.chrome.screens['products'].order_widget.el).find('.set_note').removeClass('highlight');
            }
            if (this.pos.tags && this.pos.tags.length > 0) {
                $(this.chrome.screens['products'].order_widget.el).find('.set_tags').removeClass('oe_hidden');
                $(this.chrome.screens['products'].order_widget.el).find('.set_tags').addClass('highlight');
            } else {
                $(this.chrome.screens['products'].order_widget.el).find('.set_tags').addClass('oe_hidden');
                $(this.chrome.screens['products'].order_widget.el).find('.set_tags').removeClass('highlight');
            }
            if (line.has_multi_unit()) {
                $(this.chrome.screens['products'].order_widget.el).find('.set_unit_measure').removeClass('oe_hidden');
                $(this.chrome.screens['products'].order_widget.el).find('.set_unit_measure').addClass('highlight');
            } else {
                $(this.chrome.screens['products'].order_widget.el).find('.set_unit_measure').addClass('oe_hidden');
                $(this.chrome.screens['products'].order_widget.el).find('.set_unit_measure').removeClass('highlight');
            }
            if (line.is_multi_variant()) {
                $(this.chrome.screens['products'].order_widget.el).find('.multi_variant').removeClass('oe_hidden');
                $(this.chrome.screens['products'].order_widget.el).find('.multi_variant').addClass('highlight');
            } else {
                $(this.chrome.screens['products'].order_widget.el).find('.multi_variant').addClass('oe_hidden');
                $(this.chrome.screens['products'].order_widget.el).find('.multi_variant').removeClass('highlight');
            }
            if (line.has_dynamic_combo_active()) {
                $(this.chrome.screens['products'].order_widget.el).find('.set-dynamic-com').removeClass('oe_hidden');
                $(this.chrome.screens['products'].order_widget.el).find('.set-dynamic-com').addClass('highlight');
            } else {
                $(this.chrome.screens['products'].order_widget.el).find('.set-dynamic-com').addClass('oe_hidden');
                $(this.chrome.screens['products'].order_widget.el).find('.set-dynamic-com').removeClass('highlight');
            }
            if (line.product.cross_selling) {
                $(this.chrome.screens['products'].order_widget.el).find('.suggest_buy_more').removeClass('oe_hidden');
                $(this.chrome.screens['products'].order_widget.el).find('.suggest_buy_more').addClass('highlight');
            } else {
                $(this.chrome.screens['products'].order_widget.el).find('.suggest_buy_more').addClass('oe_hidden');
                $(this.chrome.screens['products'].order_widget.el).find('.suggest_buy_more').removeClass('highlight');
            }
            if (this.pos.discounts && this.pos.discounts.length > 0) {
                $(this.chrome.screens['products'].order_widget.el).find('.set_discount').removeClass('oe_hidden');
                $(this.chrome.screens['products'].order_widget.el).find('.set_discount').addClass('highlight');
            } else {
                $(this.chrome.screens['products'].order_widget.el).find('.set_discount').addClass('oe_hidden');
                $(this.chrome.screens['products'].order_widget.el).find('.set_discount').removeClass('highlight');
            }
            if (this.pos.config.discount_value && this.pos.config.discount_value_limit > 0) {
                $(this.chrome.screens['products'].order_widget.el).find('.discount-value').removeClass('oe_hidden');
                $(this.chrome.screens['products'].order_widget.el).find('.discount-value').addClass('highlight');
            } else {
                $(this.chrome.screens['products'].order_widget.el).find('.discount-value').addClass('oe_hidden');
                $(this.chrome.screens['products'].order_widget.el).find('.discount-value').removeClass('highlight');
            }
            if (this.pos.config.signature_order) {
                $(this.chrome.screens['products'].order_widget.el).find('.signature-receipt').removeClass('oe_hidden');
                $(this.chrome.screens['products'].order_widget.el).find('.signature-receipt').addClass('highlight');
            } else {
                $(this.chrome.screens['products'].order_widget.el).find('.signature-receipt').addClass('oe_hidden');
                $(this.chrome.screens['products'].order_widget.el).find('.signature-receipt').removeClass('highlight');
            }
        },
        add_event_left_buttons: function (selected_order) {
            var self = this;
            var el_pricelist = this.el.querySelector('.pricelist');
            if (el_pricelist) {
                el_pricelist.addEventListener('click', function () {
                    self.pos.gui.screen_instances['products'].actionpad.$el.find('.select-pricelist').click();
                })
            }
            var el_create_quotation = this.el.querySelector('.create_quotation');
            if (el_create_quotation) {
                el_create_quotation.addEventListener('click', function () {
                    var order = self.pos.get_order();
                    if (order) {
                        self.quotation_order = order;
                        rpc.query({
                            model: 'pos.session',
                            method: 'search_read',
                            domain: [['state', '=', 'opened']],
                            fields: ['name', 'user_id', 'config_id', 'start_at']
                        }).then(function (sessions) {
                            self.search_session_string = '';
                            self.session_by_id = {};
                            for (var i = 0; i < sessions.length; i++) {
                                var session = sessions[i];
                                var str = session.name || '';
                                if (session.user_id) {
                                    str += '|' + session.user_id[1];
                                }
                                if (session.config_id) {
                                    str += '|' + session.config_id[1];
                                }
                                str = '' + session.id + ':' + str.replace(':', '') + '\n';
                                self.search_session_string += str;
                                self.session_by_id[session.id] = session;
                            }

                            self.gui.show_popup('popup_selection_extend', {
                                title: _t('Asignar a sesión de tienda'),
                                fields: ['name', 'email', 'phone', 'mobile'],
                                sub_datas: sessions,
                                sub_search_string: self.search_session_string,
                                sub_record_by_id: self.session_by_id,
                                sub_template: 'sessions_list',
                                body: 'Seleccione una tienda para Asignar este pedido de cotización',
                                confirm: function (session_id) {
                                    var session = self.session_by_id[session_id];
                                    self.selected_session_id = session_id;
                                    self.pos.gui.close_popup();
                                    setTimeout(function () {
                                        self.pos.gui.show_popup('textarea', {
                                            title: _t('¿Quiere asignar esta orden de cotización a la tienda POS? ' + session.config_id[1] + ' ? Agregue algunas notas para encontrar fácilmente el pedido cuando el cliente regrese'),
                                            value: self.quotation_order.get_note(),
                                            confirm: function (note) {
                                                self.quotation_order.set_note(note);
                                                self.quotation_order.save_order_to_quotation(self.selected_session_id);
                                            },
                                        });
                                    }, 500)
                                }
                            })
                        }, function (err) {
                            self.pos.query_backend_fail(err)
                        });
                    }
                })
            }
            var el_edit_voucher_card = this.el.querySelector('.edit_voucher_card');
            if (el_edit_voucher_card) {
                el_edit_voucher_card.addEventListener('click', function () {
                    var order = self.pos.get_order();
                    if (order) {
                        order.show_popup_create_voucher();
                    }
                })
            }
            var el_input_return_reason = this.el.querySelector('.input_reason_return');
            if (el_input_return_reason) {
                el_input_return_reason.addEventListener('click', function () {
                    self.set_reason_return();
                })
            }
            var el_set_seller = this.el.querySelector('.set_seller');
            if (el_set_seller) {
                el_set_seller.addEventListener('click', function () {
                    self.set_seller()
                })
            }
            var el_set_note = this.el.querySelector('.set_note');
            if (el_set_note) {
                el_set_note.addEventListener('click', function () {
                    self.set_note()
                })
            }
            var el_set_multi_variant = this.el.querySelector('.multi_variant');
            if (el_set_multi_variant) {
                el_set_multi_variant.addEventListener('click', function () {
                    self.pos.show_products_with_field('multi_variant');
                    var order = self.pos.get_order();
                    var selected_orderline = order.selected_orderline;
                    if (selected_orderline && selected_orderline.product.multi_variant && self.pos.variant_by_product_tmpl_id[selected_orderline.product.product_tmpl_id]) {
                        return self.gui.show_popup('popup_select_variants', {
                            variants: self.pos.variant_by_product_tmpl_id[selected_orderline.product.product_tmpl_id],
                            selected_orderline: selected_orderline,
                        });
                    } else {
                        return self.pos.gui.show_popup('dialog', {
                            title: _t('Advertencia'),
                            body: _t('Línea seleccionada no activa Variante múltiple'),
                        })
                    }
                })
            }
            var el_set_change_cross_selling = this.el.querySelector('.change_cross_selling');
            if (el_set_change_cross_selling) {
                el_set_change_cross_selling.addEventListener('click', function () {
                    self.pos.show_products_with_field('cross_selling');
                    var order = self.pos.get_order();
                    if (order && order.selected_orderline) {
                        order.selected_orderline.change_cross_selling();
                    }
                })
            }
            var el_set_product_packaging = this.el.querySelector('.product_packaging');
            if (el_set_product_packaging) {
                el_set_product_packaging.addEventListener('click', function () {
                    self.pos.show_products_with_field('sale_with_package');
                    var order = self.pos.get_order();
                    if (order) {
                        var selected_orderline = order.selected_orderline;
                        if (selected_orderline) {
                            var product_id = selected_orderline.product.id;
                            var list = [];
                            var packagings = self.pos.packaging_by_product_id[product_id];
                            if (packagings) {
                                for (var j = 0; j < packagings.length; j++) {
                                    var packaging = packagings[j];
                                    list.push({
                                        'label': packaging.name + ' con precio: ' + packaging.list_price + ' y cantidad: ' + packaging.qty,
                                        'item': packaging
                                    });
                                }
                            }
                            if (list.length) {
                                return self.pos.gui.show_popup('selection', {
                                    title: _t('Seleccionar embalaje'),
                                    list: list,
                                    confirm: function (packaging) {
                                        var order = self.pos.get_order();
                                        if (order && order.selected_orderline && packaging.list_price > 0 && packaging.qty > 0) {
                                            var selected_orderline = order.selected_orderline;
                                            selected_orderline.packaging = packaging;
                                            return self.pos.gui.show_popup('number', {
                                                title: 'Cuantas cajas',
                                                body: 'Cuantas cajas necesitas vender ?',
                                                confirm: function (number) {
                                                    if (number > 0) {
                                                        var order = self.pos.get_order();
                                                        if (!order) {
                                                            return self.pos.gui.show_popup('dialog', {
                                                                title: 'Advertencia',
                                                                body: 'No se pudo encontrar el pedido seleccionado',
                                                            })
                                                        }
                                                        var selected_orderline = order.selected_orderline;
                                                        if (!selected_orderline) {
                                                            return self.pos.gui.show_popup('dialog', {
                                                                title: 'Advertencia',
                                                                body: 'No se pudo encontrar la línea de pedido seleccionada',
                                                            })
                                                        }
                                                        selected_orderline.packaging = packaging;
                                                        selected_orderline.set_quantity(packaging.qty * number);
                                                        selected_orderline.set_unit_price(packaging.list_price / packaging.qty);
                                                        selected_orderline.price_manually_set = true;
                                                        return self.pos.gui.show_popup('dialog', {
                                                            title: 'Success',
                                                            body: 'Gran trabajo ! Solo agrega ' + number + ' cajas para ' + selected_orderline.product.display_name,
                                                            color: 'success'
                                                        })
                                                    } else {
                                                        return self.pos.gui.show_popup('dialog', {
                                                            title: 'Advertencia',
                                                            body: 'El número de embalaje / caja no puede ser inferior a 0',
                                                        })
                                                    }
                                                }
                                            })
                                        }
                                        if (packaging.list_price <= 0 || packaging.qty <= 0) {
                                            self.pos.gui.show_popup('dialog', {
                                                title: 'Advertencia',
                                                body: 'Su embalaje seleccionado tiene precio o cantidad menor o igual a 0'
                                            })
                                        }
                                    }
                                });
                            } else {
                                return self.pos.gui.show_popup('dialog', {
                                    title: _t('Alerta'),
                                    body: _t('La línea seleccionada no ha establecido la venta por paquete')
                                })
                            }
                        }
                    }
                })
            }
            var el_set_unit_measure = this.el.querySelector('.set_unit_measure');
            if (el_set_unit_measure) {
                el_set_unit_measure.addEventListener('click', function () {
                    self.set_unit()
                })
            }
            var el_set_tags = this.el.querySelector('.set_tags');
            if (el_set_tags) {
                el_set_tags.addEventListener('click', function () {
                    self.set_tags()
                })
            }
            var el_remove_shopping_cart = this.el.querySelector('.remove_shopping_cart');
            if (el_remove_shopping_cart) {
                el_remove_shopping_cart.addEventListener('click', function () {
                    self.remove_shopping_cart()
                })
            }
            var el_set_dynamic_combo = this.el.querySelector('.set-dynamic-com');
            if (el_set_dynamic_combo) {
                el_set_dynamic_combo.addEventListener('click', function () {
                    var order = self.pos.get_order();
                    var selected_line = order.get_selected_orderline();
                    if (!selected_line) {
                        return self.pos.gui.show_popup('confirm', {
                            title: _t('Advertencia'),
                            body: _t('No hay línea seleccionada, seleccione una línea dentro del carrito de pedido antes')
                        })
                    }
                    var pos_categories_combo = _.filter(self.pos.pos_categories, function (categ) {
                        return categ.is_category_combo
                    });
                    if (pos_categories_combo.length == 0) {
                        return self.pos.gui.show_popup('confirm', {
                            title: _t('Advertencia'),
                            body: _t('Sus categorías de POS no tienen ninguna combinación de categorías')
                        })
                    }
                    self.pos.gui.show_popup('popup_dynamic_combo', {
                        title: _t('Seleccione una categoría y agregue elementos combinados'),
                        body: _t('Seleccione elementos combinados y agréguelos a la línea seleccionada'),
                        selected_combo_items: selected_line.selected_combo_items,
                        confirm: function (selected_combo_items) {
                            // TODO: selected_combo_items is {product_id: quantity}
                            selected_line.set_dynamic_combo_items(selected_combo_items)
                        }
                    })
                })
            }
            var el_suggest_buy_more = this.el.querySelector('.suggest_buy_more');
            if (el_suggest_buy_more) {
                el_suggest_buy_more.addEventListener('click', function () {
                    var order = self.pos.get_order();
                    if (order && order.selected_orderline) {
                        var selected_orderline = order.selected_orderline;
                        selected_orderline.show_cross_sale();
                    } else {
                        self.pos.gui.show_popup('dialog', {
                            title: _t('Advertencia'),
                            body: _t('Venta cruzada solo activa cuando tiene una línea seleccionada')
                        })
                    }
                })
            }
            var el_service_charge = this.el.querySelector('.service-charge');
            if (el_service_charge) {
                el_service_charge.addEventListener('click', function () {
                    $('.control-buttons-extend').empty();
                    $('.control-buttons-extend').removeClass('oe_hidden');
                    self.ServiceChargeWidget = new ServiceChargeWidget(self, {
                        widget: self,
                    });
                    self.ServiceChargeWidget.appendTo($('.control-buttons-extend'));
                })
            }
            var el_shipping_order = this.el.querySelector('.shipping-order');
            if (el_shipping_order) {
                el_shipping_order.addEventListener('click', function () {
                    var order = self.pos.get_order();
                    if (order && order.orderlines.models.length == 0) {
                        return self.pos.gui.show_popup('dialog', {
                            title: _t('Advertencia'),
                            body: _t('Seleccione Cliente y agregue artículos al carrito')
                        });
                    }
                    if (!order || !order.get_client()) {
                        self.pos.gui.show_popup('dialog', {
                            title: _t('Advertencia'),
                            body: _t('Seleccione Cliente y agregue artículos al carrito')
                        });
                        return self.pos.gui.show_screen('clientlist');
                    } else {
                        return self.pos.gui.show_popup('popup_shipping_address', {
                            title: _t('Envío de información de contacto y creación de pedido contra reembolso'),
                            body: _t('Introduzca la dirección de información del cliente, para que el hombre de entrega envíe la orden a: ' + order.get_client().name + '. Si marca la casilla de COD, este es un pedido parcial con un monto de pago 0'),
                            order: self.pos.get_order(),
                            confirm: function (values) {
                                self.cod = values['cod'];
                                var order = self.pos.get_order();
                                var client = order.get_client();
                                var client_val = {
                                    city: values['city'],
                                    comment: values['comment'],
                                    email: values['email'],
                                    mobile: values['email'],
                                    name: values['name'],
                                    phone: values['phone'],
                                    property_product_pricelist: values['property_product_pricelist'],
                                    street: values['street'],
                                    street2: values['street2'],
                                };
                                if (values['signature']) {
                                    order.signature = values['signature']
                                }
                                if (values.new_shipping_address == "true") {
                                    client_val['parent_id'] = client.id;
                                    client_val['type'] = 'delivery';
                                    client_val['id'] = null;
                                } else {
                                    client_val['id'] = client.id
                                }
                                if (values['shipping_notes']) {
                                    order.set_note(values['shipping_notes']);
                                }
                                return rpc.query({
                                    model: 'res.partner',
                                    method: 'create_from_ui',
                                    args: [client_val]
                                }).then(function (partner_id) {
                                    var pushing = self.pos._search_read_by_model_and_id('res.partner', [partner_id]);
                                    pushing.then(function (datas) {
                                        self.pos.sync_with_backend('res.partner', datas, true);
                                        var partner_id = datas[0]['id'];
                                        var client = self.pos.db.get_partner_by_id(partner_id);
                                        var order = self.pos.get_order();
                                        if (client && order) {
                                            order.set_shipping_client(client);
                                            self.pos.gui.show_screen('payment');
                                        }
                                        if (self.cod == 'true') {
                                            order.do_partial_payment();
                                            self.pos.gui.show_popup('dialog', {
                                                title: _t('Advertencia'),
                                                body: _t('El nuevo pedido COD (entrega del pedido del cliente) enviado se realizó correctamente. Envíe el pedido al cliente y realice el pago completo'),
                                                color: 'success'
                                            })
                                        }
                                    })
                                }, function (err) {
                                    self.pos.query_backend_fail(err);
                                });
                            }
                        })
                    }
                })
            }
            var el_set_discount = this.el.querySelector('.set_discount');
            if (el_set_discount) {
                el_set_discount.addEventListener('click', function () {
                    self.pos.trigger('open:discounts');
                })
            }
            var el_discount_value = this.el.querySelector('.discount-value');
            if (el_discount_value) {
                el_discount_value.addEventListener('click', function () {
                    self.gui.show_popup('number', {
                        title: _t('Establecer valor de descuento'),
                        body: 'Ingrese el valor de descuento, pero se requiere menor que: ' + self.pos.gui.chrome.format_currency(self.pos.discount_value_limit),
                        confirm: function (discount_value) {
                            var order = self.pos.get_order();
                            if (order) {
                                order.set_discount_value(discount_value)
                            }
                        }
                    });
                })
            }
            var el_signature_receipt = this.el.querySelector('.signature-receipt');
            if (el_signature_receipt) {
                el_signature_receipt.addEventListener('click', function () {
                    self.pos.gui.show_popup('popup_order_signature', {
                        title: _t('Recibo con firma'),
                        body: _t('La firma se mostrará en el recibo del pedido'),
                        order: self.pos.get_order()
                    });
                })
            }
            var el_find_order = this.el.querySelector('.find-order');
            if (el_find_order) {
                el_find_order.addEventListener('click', function () {
                    self.pos.show_purchased_histories();
                })
            }
            var el_take_note = this.el.querySelector('.take-note');
            if (el_take_note) {
                el_take_note.addEventListener('click', function () {
                    self.gui.show_popup('textarea', {
                        title: _t('Agregar nota de pedido'),
                        value: selected_order.get_note(),
                        confirm: function (note) {
                            self.pos.get_order().set_note(note);
                            return self.pos.gui.show_popup('dialog', {
                                title: _t('Terminado'),
                                body: _t('Pones nota a la orden: ' + note),
                                color: 'success'
                            })
                        },
                    });
                })
            }
            var el_signature_note = this.el.querySelector('.signature-note');
            if (el_signature_note) {
                el_signature_note.addEventListener('click', function () {
                    self.gui.show_popup('popup_order_signature', {
                        title: _t('Por favor firma'),
                        body: _t('La firma se mostrará al recibirla'),
                        order: selected_order
                    });
                })
            }
            var el_promotion = this.el.querySelector('.promotion_details');
            if (el_promotion) {
                el_promotion.addEventListener('click', function () {
                    self.pos.trigger('open:promotions');
                })
            }
        },
        renderElement: function (scrollbottom) {
            var self = this;
            this._super(scrollbottom);
            var selected_order = this.pos.get_order();
            if (selected_order) {
                this.add_event_left_buttons(selected_order);
            }
        },
        update_summary: function () {
            console.log('update_summary');
            this._super();
            var self = this;
            $('.mode-button').click(function () {
                self.change_mode();
            });
            var selected_order = this.pos.get_order();
            if (selected_order && selected_order.orderlines.length && !this.first_event_line) {
                self._change_event_line(selected_order.orderlines.models[0]);
                this.first_event_line = true;
            }
            var buttons = this.getParent().action_buttons;
            if (selected_order) {
                this.pos.trigger('update:customer-facing-screen');
                this.pos.trigger('update:summary');
                var promotion_lines = _.filter(selected_order.orderlines.models, function (line) {
                    return line.promotion;
                });
                if (promotion_lines.length > 0) {
                    this.set_total_gift(promotion_lines.length)
                }
                var el_signature = $('.signature');
                if (el_signature) {
                    el_signature.attr('src', selected_order.get_signature());
                }
                var el_order_note = $('.order-note');
                if (el_order_note) {
                    el_order_note.html(selected_order.get_note());
                }
                this.pos._update_cart_qty_by_order();
                if (buttons) {
                    this.active_button_cash_management(buttons);
                    this.active_reprint_last_order(buttons, selected_order);
                    this.active_medical_insurance(buttons, selected_order);
                    this.active_button_combo_item_add_lot(buttons, selected_order);
                    this.active_internal_transfer_button(buttons, selected_order);
                    this.active_button_variants(buttons, selected_order);
                    this.active_button_create_purchase_order(buttons, selected_order);
                    var changes = selected_order.hasChangesToPrint();
                    if (buttons && buttons.button_kitchen_receipt_screen) {
                        buttons.button_kitchen_receipt_screen.highlight(changes);
                    }
                    // TODO: promotion
                    this.active_promotion(buttons, selected_order);
                    this.promotion_added(buttons, selected_order);
                    this.active_buyers_promotion(buttons, selected_order);
                    this.active_button_remove_promotions(buttons, selected_order);
                    // TODO: loyalty
                    if (buttons.reward_button && this.pos.loyalty) {
                        this.active_loyalty(buttons, selected_order);
                    }
                    // TODO: booking orders
                    this.active_button_create_sale_order(buttons, selected_order);
                    this.active_button_booking_order(buttons, selected_order);
                    this.active_button_delivery_order(buttons, selected_order);
                    this.show_delivery_address(buttons, selected_order);
                }
            }
        }
    });
});
