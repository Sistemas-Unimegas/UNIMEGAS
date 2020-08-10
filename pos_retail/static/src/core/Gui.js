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
                    title: _t('Alerta'),
                    body: screen_name + _t(' no encontrado'),
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
                        title: _t('Aplicaciones'),
                        content: _t('Todas las aplicaciones y funciones aquí')
                    },
                    {
                        element_id: '.new-product-categ',
                        title: _t('Crear nueva Categoría'),
                    },
                    {
                        element_id: '.new-product',
                        title: _t('Crear nuevo Producto'),
                    },
                    {
                        element_id: '.add-new-client',
                        title: _t('Crear nuevo Cliente'),
                    },
                    {
                        element_id: '.find-order',
                        title: _t('Encontrar Orden'),
                    },
                    {
                        element_id: '.set-customer',
                        title: _t('Establecer cliente al Pedido'),
                    },
                    {
                        element_id: '.pay',
                        title: _t('Orden de Pago'),
                    },
                    {
                        element_id: '.total_amount',
                        title: _t('Total'),
                    },
                    {
                        element_id: '.multi_variant',
                        title: _t('Establecer Variantes'),
                    },
                    {
                        element_id: '.change_cross_selling',
                        title: _t('Venta Cruzada'),
                    },
                    {
                        element_id: '.add_discount',
                        title: _t('Agregar Descuento'),
                    },
                    {
                        element_id: '.product_packaging',
                        title: _t('Mostrar Paquete de Productos'),
                    },
                    {
                        element_id: '.button-combo',
                        title: _t('Establecer Productos del Combo'),
                    },
                    {
                        element_id: '.service-charge',
                        title: _t('Agregar Servicios'),
                    },
                    {
                        element_id: '.search-product',
                        title: _t('Busqueda de Productos'),
                        content: _t('Puedes buscar Productos y agregar al carrito de ventas aquí')
                    },
                    {
                        element_id: '.find_customer',
                        title: _t('Buscar Clientes'),
                        content: _t('Puedes buscar clientes por el Nombre o Número de Teléfono')
                    },
                    {
                        element_id: '.category_home',
                        title: _t('Regresar a Inicio'),
                        content: _t('Y mostrar todos los Productos')
                    },
                    {
                        element_id: '.screen-mode',
                        title: _t('Modo Pantalla'),
                        content: _t('Puede cambiar aquí entre modo Oscuro y Claro')
                    },
                    {
                        element_id: '.keyboard-guide',
                        title: _t('Guía del Teclado'),
                        content: _t('Haga clic en mostrar todos los atajos de teclado compatibles con el módulo')
                    },
                    {
                        element_id: '.lock-session',
                        title: _t('Lock your Session'),
                        content: _t('You can lock your session and unlock via POS Pass Pin of User Setting / Point Of Sale')
                    },
                    {
                        element_id: '.remove-orders-blank',
                        title: _t('Quitar Orden en blanco'),
                        content: _t('Haga clic aquí para eliminar las líneas en blanco de los pedidos')
                    },
                    {
                        element_id: '.report-analytic',
                        title: _t('Reportes Analíticos'),
                        content: _t('Muestra los reportes de Ventas')
                    },
                    {
                        element_id: '.shop',
                        title: _t('ubicación del Logo del POS'),
                        content: _t('Clic aquí para cambiar el Logo del Punto de Venta')
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
                        title: _t('Pantalla de frente al cliente'),
                        content: _t('Haga clic aquí para abrir una nueva pestaña y mirar la pantalla de pedido al cliente')
                    },
                    {
                        element_id: '.invoices-screen',
                        title: _t('Pantalla de facturas'),
                        content: _t('Muestra todas las facturas de tu tienda POS')
                    },
                    {
                        element_id: '.pos-orders-screen',
                        title: _t('Pantalla de Órdenes POS'),
                        content: _t('Muestra todos los pedidos pos de su tienda POS')
                    },
                    {
                        element_id: '.products-sort-by',
                        title: _t('Ordenar Por'),
                        content: _t('Puede ordenar por Productos, filtrar por Productos')
                    },
                    {
                        element_id: '.products-view-type',
                        title: _t('Vista por tipo de Producto'),
                        content: _t('Haga clic para cambiar entre la vista de caja y la vista de lista')
                    },
                    {
                        element_id: '.products-operation',
                        title: _t('Operación de Productos'),
                        content: _t('Vaya a la pantalla Operación de productos, puede crear una nueva categoría, nuevos productos, editar la información de los productos')
                    },
                    {
                        element_id: '.quickly-return-products',
                        title: _t('Devolver productos rápidamente'),
                        content: _t('Vaya a Devolución rápida de productos, puede activar su escáner y la devolución de productos de escaneo')
                    },
                    {
                        element_id: '.review-receipt',
                        title: _t('Imprimir factura sin orden de pago'),
                        content: _t('Haga clic aquí para imprimir la factura de pedido seleccionada, sin pago')
                    },
                    {
                        element_id: '.select-pricelist',
                        title: _t('Establecer lista de precios'),
                        content: _t('Clic aquí para establecer listas de precios')
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