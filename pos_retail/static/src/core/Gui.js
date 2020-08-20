odoo.define('pos_retail.gui', function (require) {
    "use strict";
    var gui = require('point_of_sale.gui');
    var core = require('web.core');
    var _t = core._t;
    var rpc = require('web.rpc');
    var BarcodeEvents = require('barcodes.BarcodeEvents').BarcodeEvents;

    gui.Gui.include({
        init: function (options) {
            this._super(options);
            this.starting_customer_monitors_screen = false;
        },
        closing_session: function () {
            var self = this;
            return new Promise(function (resolve, reject) {
                rpc.query({
                    model: 'pos.session',
                    method: 'close_session_and_validate',
                    args: [[self.pos.pos_session.id]]
                }).then(function (values) {
                    resolve()
                }, function (err) {
                    reject(err)
                })
            })
        },
        show_popup: function (name, options) {
            if (!this.popup_instances[name]) {
                return null;
            }
            if (options && options.title == 'Select pricelist') {
                return this.pos.trigger('open:pricelist');
            }
            this._super(name, options);
            this.popup_current_display = name;
        },
        _close: function () {
            this._super();
            this.pos.polling_job_auto_paid_orders_draft();
            if (this.pos.customer_monitor_screen) {
                this.pos.customer_monitor_screen.close();
            }
        },
        show_screen: function (screen_name, params, refresh, skip_close_popup) {
            var self = this;
            if (!this.screen_instances[screen_name]) {
                self.show_popup('dialog', {
                    title: _t('Alert'),
                    body: screen_name + _t(' not found'),
                })
                return false;
            }
            this._super(screen_name, params, refresh, skip_close_popup);
            if (screen_name && this.pos.config.customer_facing_screen && !this.starting_customer_monitors_screen) {
                this.starting_customer_monitors_screen = true;
                self.pos.trigger('open:customer-monitor-screen');
            }
            if (screen_name != 'products') {
                $('.searchbox >input').focus()
            }
            if (screen_name == 'products') {
                if (!BarcodeEvents.$barcodeInput) {
                   $('.search-products >input').focus();
                }
                var guide_elements = [
                    {
                        element_id: '.apps',
                        title: _t('Todas las aplicaciones'),
                        content: _t('Todas las aplicaciones y funciones aquí')
                    },
                    {
                        element_id: '.new-product-categ',
                        title: _t('Crear nueva categoría'),
                    },
                    {
                        element_id: '.new-product',
                        title: _t('Crear nuevo producto'),
                    },
                    {
                        element_id: '.add-new-client',
                        title: _t('Crear nuevo cliente'),
                    },
                    {
                        element_id: '.find-order',
                        title: _t('Buscar orden'),
                    },
                    {
                        element_id: '.set-customer',
                        title: _t('Establecer cliente a pedido'),
                    },
                    {
                        element_id: '.pay',
                        title: _t('Orden de pago'),
                    },
                    {
                        element_id: '.total_amount',
                        title: _t('Total'),
                    },
                    {
                        element_id: '.multi_variant',
                        title: _t('Establecer variantes'),
                    },
                    {
                        element_id: '.change_cross_selling',
                        title: _t('Venta cruzada'),
                    },
                    {
                        element_id: '.add_discount',
                        title: _t('Agregar descuento'),
                    },
                    {
                        element_id: '.product_packaging',
                        title: _t('Mostrar paquete de producto'),
                    },
                    {
                        element_id: '.button-combo',
                        title: _t('Establecer elementos combinados'),
                    },
                    {
                        element_id: '.service-charge',
                        title: _t('Agregar servicio'),
                    },
                    {
                        element_id: '.search-product',
                        title: _t('Buscar productos'),
                        content: _t('Puede encontrar el producto y agregarlo al carrito aquí')
                    },
                    {
                        element_id: '.find_customer',
                        title: _t('Encontrar cliente'),
                        content: _t('Puede encontrar al cliente rápidamente a través del teléfono móvil / número de teléfono del cliente aquí')
                    },
                    {
                        element_id: '.category_home',
                        title: _t('Inicio'),
                        content: _t('Y mostrar todos los productos')
                    },
                    {
                        element_id: '.screen-mode',
                        title: _t('Modo de pantalla'),
                        content: _t('Puede hacer clic aquí y cambiar entre el modo oscuro y claro')
                    },
                    {
                        element_id: '.keyboard-guide',
                        title: _t('Guía de teclado'),
                        content: _t('Haga clic en mostrar todos los atajos de teclado compatibles con el módulo')
                    },
                    {
                        element_id: '.lock-session',
                        title: _t('Bloquea tu sesión'),
                        content: _t('Puede bloquear su sesión y desbloquearla a través del PIN de paso de POS de configuración de usuario / punto de venta')
                    },
                    {
                        element_id: '.remove-orders-blank',
                        title: _t('Eliminar pedido en blanco'),
                        content: _t('Haga clic aquí para eliminar pedidos con líneas en blanco')
                    },
                    {
                        element_id: '.report-analytic',
                        title: _t('Informe analítico'),
                        content: _t('Si quieres imprimir algún informe sobre ventas, puedes probarlo aquí')
                    },
                    {
                        element_id: '.shop',
                        title: _t('Logo de su POS'),
                        content: _t('Puede hacer clic aquí y cambiar su logotipo POS')
                    },
                    {
                        element_id: '.mobile-mode',
                        title: _t('Ir al modo móvil'),
                        content: _t('Si su Odoo es una licencia EE, o utilizó la aplicación web móvil. Puedes probarlo')
                    },
                    {
                        element_id: '.booked-orders',
                        title: _t('Pantalla de pedidos reservados'),
                        content: _t('Haga clic aquí y vaya a la pantalla de pedidos reservados')
                    },
                    {
                        element_id: '.customer-facing-screen',
                        title: _t('Pantalla de cara al cliente'),
                        content: _t('Haga clic aquí para abrir una nueva pestaña y mirar la pantalla de pedido al cliente')
                    },
                    {
                        element_id: '.invoices-screen',
                        title: _t('Pantalla de facturas'),
                        content: _t('Muestra todas las facturas de tu tienda pos')
                    },
                    {
                        element_id: '.pos-orders-screen',
                        title: _t('Pantalla de pedidos POS'),
                        content: _t('Mostrar todos los pedidos pos de su tienda pos')
                    },
                    {
                        element_id: '.products-sort-by',
                        title: _t('Ordenar por'),
                        content: _t('Puede abreviar por productos, filtrar por productos')
                    },
                    {
                        element_id: '.products-view-type',
                        title: _t('Tipo de vista de productos'),
                        content: _t('Haga clic en él para cambiar entre la vista de caja y los productos de vista de lista')
                    },
                    {
                        element_id: '.products-operation',
                        title: _t('Operación de productos'),
                        content: _t('Vaya a la pantalla Operación de productos, puede crear una nueva categoría, nuevos productos, editar la información de los productos')
                    },
                    {
                        element_id: '.quickly-return-products',
                        title: _t('Devolver productos rápidamente'),
                        content: _t('Vaya a Devolver productos rápidamente, puede activar su escáner y devolver los productos de escaneo')
                    },
                    {
                        element_id: '.review-receipt',
                        title: _t('Imprimir factura sin orden de pago'),
                        content: _t('Haga clic aquí para imprimir la factura de pedido seleccionada, sin pago')
                    },
                    {
                        element_id: '.select-pricelist',
                        title: _t('Establecer lista de precios'),
                        content: _t('Haga clic aquí para ')
                    },
                ];
                this.guide_elements = guide_elements;
                for (var i = 0; i < self.guide_elements.length; i++) {
                    var guide = self.guide_elements[i];
                    self.show_guide_without_chrome(
                        guide.element_id,
                        'top center',
                        guide.title,
                        guide.content
                    );
                }

            }
        },
        close_popup: function () {
            this._super();
            var current_screen = this.get_current_screen();
            if (current_screen == 'report' || current_screen == 'receipt') {
                $('.alert').addClass('oe_hidden');
            }
        },
        show_guide_without_chrome: function (element_id, position, title, content) {
            if (!this.pos.config.guide_pos || window.chrome) {
                return false;
            } else {
                $(element_id).popup({
                    position: position,
                    target: element_id,
                    title: title,
                    content: content
                })
            }
        }
    });
});