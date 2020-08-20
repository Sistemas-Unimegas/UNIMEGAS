odoo.define('pos_retail.multi_locations', function (require) {
    var screens = require('point_of_sale.screens');
    var core = require('web.core');
    var _t = core._t;
    var qweb = core.qweb;
    var PopupWidget = require('point_of_sale.popups');
    var gui = require('point_of_sale.gui');

    var popup_set_locations = PopupWidget.extend({
        template: 'popup_set_locations',
        show: function (options) {
            var self = this;
            this.options = options;
            this._super(options);
            this.location_selected = [];
            var locations = this.pos.stock_locations;
            this.$el.find('.card-content').html(qweb.render('locations_list', {
                locations: locations,
                widget: this
            }));
            this.$('.selection-item').click(function () {
                var location_id = parseInt($(this).data('id'));
                var location = self.pos.stock_location_by_id[location_id];
                if (location) {
                    if ($(this).closest('.selection-item').hasClass("item-selected") == true) {
                        $(this).closest('.selection-item').toggleClass("item-selected");
                        for (var i = 0; i < self.location_selected.length; ++i) {
                            if (self.location_selected[i].id == location.id) {
                                self.location_selected.splice(i, 1);
                            }
                        }
                        if (self.location_selected.length == 0) {
                            return self.wrong_input("div[class='card-content']", "(*) Please select minimum 1 location")
                        } else {
                            return self.passed_input("div[class='card-content']")
                        }
                    } else {
                        $(this).closest('.selection-item').toggleClass("item-selected");
                        self.location_selected.push(location);
                        if (self.location_selected.length != 0) {
                            return self.passed_input("div[class='card-content']")
                        }
                    }
                }
            });
            this.$('.confirm').click(function () {
                if (self.location_selected.length == 0) {
                    return self.wrong_input("div[class='card-content']", "(*) Please select minimum 1 location")
                } else {
                    self.pos.gui.close_popup();
                    var location_ids = [];
                    for (var i = 0; i < self.location_selected.length; i++) {
                        location_ids.push(self.location_selected[i]['id'])
                    }
                    return self.pos._get_stock_on_hand_by_location_ids([], location_ids).then(function (datas) {
                        self.pos.stock_datas_by_location_id = datas;
                        var stock_datas = {};
                        var products = [];
                        for (var location_id in datas) {
                            var stock_datas_by_location_id = datas[location_id];
                            for (var product_id in stock_datas_by_location_id) {
                                if (stock_datas[product_id] == undefined) {
                                    stock_datas[product_id] = stock_datas_by_location_id[product_id]
                                } else {
                                    stock_datas[product_id] += stock_datas_by_location_id[product_id]
                                }
                                var product = self.pos.db.product_by_id[product_id];
                                if (product) {
                                    products.push(product)
                                }
                            }
                        }
                        self.pos.db.stock_datas = stock_datas;
                        if (products.length) {
                            self.pos.auto_update_stock_products(products);
                            self.pos.gui.screen_instances["products_operation"].refresh_screen();
                        }
                        return self.gui.show_popup('dialog', {
                            title: _t('Terminado'),
                            body: _t('Pantalla de productos con stock de exhibición disponible con sus ubicaciones de stock seleccionadas'),
                            color: 'success'
                        });
                    });
                }
            });
            this.$('.cancel').click(function () {
                self.pos.gui.close_popup();
            });
        }
    });
    gui.define_popup({name: 'popup_set_locations', widget: popup_set_locations});

    var button_set_locations = screens.ActionButtonWidget.extend({
        template: 'button_set_locations',
        init: function (parent, options) {
            this._super(parent, options);
        },
        button_click: function () {
            this.pos.show_products_type_only_product();
            if (this.pos.stock_locations.length != 0) {
                this.gui.show_popup('popup_set_locations', {
                    title: _t('Elija ubicaciones de stock'),
                    body: _t('Seleccione ubicaciones y vea toda la cantidad disponible de productos')
                })
            } else {
                this.gui.show_popup('dialog', {
                    'title': 'Advertencia',
                    'body': 'Sus ubicaciones de stock no tienen ninguna ubicación marcada en la casilla de verificación [Disponible en POS]. Vuelve al backend y configúralo'
                })
            }
        }
    });
    screens.define_action_button({
        'name': 'button_set_locations',
        'widget': button_set_locations,
        'condition': function () {
            return this.pos.stock_locations && this.pos.config.display_onhand && this.pos.config.multi_location_check_all_stock;
        }
    });

    var popup_set_location = PopupWidget.extend({
        template: 'popup_set_location',
        show: function (options) {
            var self = this;
            this.options = options;
            this._super(options);
            var stock_locations = this.pos.stock_locations;
            var locations = [];
            for (var i = 0; i < stock_locations.length; i++) {
                var location = stock_locations[i];
                if (location.company_id && location.company_id[0] == self.pos.company.id) {
                    locations.push(location)
                }
            }
            this.$el.find('.card-content').html(qweb.render('locations_list', {
                locations: locations,
                widget: this
            }));
            this.$('.selection-item').click(function () {
                var location_id = parseInt($(this).data('id'));
                var location = self.pos.stock_location_by_id[location_id];
                var order = self.pos.get_order();
                if (location && order) {
                    order.set_picking_source_location(location);
                    self.pos.gui.close_popup();
                } else {
                    self.pos.gui.show_popup('confirm', {
                        title: 'Advertencia',
                        body: 'El pedido es nulo o no se encuentra la ubicación'
                    });
                }
                return self.pos._get_stock_on_hand_by_location_ids([], [location_id]).then(function (stock_datas_by_location_id) {
                    self.pos.stock_datas_by_location_id = stock_datas_by_location_id;
                    var location = self.pos.get_picking_source_location();
                    var datas = stock_datas_by_location_id[location.id];
                    var products = [];
                    self.pos.db.stock_datas = datas;
                    for (var product_id in datas) {
                        var product = self.pos.db.product_by_id[product_id];
                        if (product) {
                            product['qty_available'] = datas[product_id];
                            products.push(product)
                        }
                    }
                    if (products.length) {
                        self.pos.auto_update_stock_products(products);
                        self.pos.gui.screen_instances["products_operation"].refresh_screen();
                    }
                    return self.gui.show_popup('dialog', {
                        title: _t('Terminado'),
                        body: _t('Orden de entrega de la orden seleccionada establecerá la ubicación de origen desde ' + location.name),
                        color: 'success'
                    });
                })
            });
            this.$('.cancel').click(function () {
                self.pos.gui.close_popup();
            });
        }
    });
    gui.define_popup({name: 'popup_set_location', widget: popup_set_location});

    var button_set_location = screens.ActionButtonWidget.extend({
        template: 'button_set_location',
        init: function (parent, options) {
            this._super(parent, options);
            if (this.pos.config.display_onhand && this.pos.config.update_stock_onhand_realtime) {
                this.pos.bind('change:selectedOrder', function () {
                    this.renderElement();
                    this.pos.update_stock_on_hand_products();
                }, this);
            }
        },
        button_click: function () {
            this.pos.show_products_type_only_product();
            if (this.pos.stock_locations.length != 0) {
                this.gui.show_popup('popup_set_location', {
                    title: _t('Cambiar la ubicación de stock predeterminada de los pedidos'),
                    body: _t('Esta es la ubicación de la lista que tiene la misma empresa que su empresa de usuario, Elija la ubicación y agregue al pedido, cuando el pedido finalice, la cantidad disponible de producto se reducirá desde la ubicación seleccionada')
                })
            } else {
                this.gui.show_popup('dialog', {
                    'title': _t('Advertencia'),
                    'body': _t('Sus ubicaciones de stock no tienen ninguna ubicación marcada en la casilla de verificación [Disponible en POS]. Vuelve al backend y configúralo')
                })
            }
        }
    });
    screens.define_action_button({
        'name': 'button_set_location',
        'widget': button_set_location,
        'condition': function () {
            return this.pos.config.multi_location && this.pos.stock_locations && this.pos.config.multi_location_update_default_stock;
        }
    });

    var button_check_stock = screens.ActionButtonWidget.extend({
        template: 'button_check_stock',
        button_click: function () {
            var order = this.pos.get_order();
            if (!order) {
                return this.pos.gui.show_popup('dialog', {
                    title: _t('Advertencia'),
                    body: _t('No ha seleccionado el pedido, seleccione el pedido')
                })
            }
            var selected_line = order.get_selected_orderline();
            if (!selected_line) {
                return this.pos.gui.show_popup('dialog', {
                    title: _t('Advertencia'),
                    body: _t('No ha seleccionado la línea, seleccione la línea')
                })
            }
            if (selected_line.product.type != 'product') {
                return this.pos.gui.show_popup('dialog', {
                    title: _t('Advertencia'),
                    body: _t('El tipo de producto seleccionado no es producto almacenable')
                })
            }
            return this.pos.update_onhand_by_product(selected_line.product)
        }
    });
    screens.define_action_button({
        'name': 'button_check_stock',
        'widget': button_check_stock,
        'condition': function () {
            return this.pos.config.multi_location && this.pos.config.display_onhand && this.pos.config.multi_location_check_stock_line_selected;
        }
    });
});