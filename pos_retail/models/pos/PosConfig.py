# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import logging
from odoo.exceptions import UserError, ValidationError
import odoo

version_info = odoo.release.version_info[0]

try:
    to_unicode = unicode
except NameError:
    to_unicode = str

_logger = logging.getLogger(__name__)


class pos_config_image(models.Model):
    _name = "pos.config.image"
    _description = "Imagen mostrada a la pantalla del cliente"

    name = fields.Char('Titulo', required=1)
    image = fields.Binary('Imagen', required=1)
    config_id = fields.Many2one('pos.config', 'Configuración POS', required=1)
    description = fields.Text('Descripción')


class pos_config(models.Model):
    _inherit = "pos.config"

    def init(self):
        self.env.cr.execute(
            """DELETE FROM ir_model_data WHERE model IN ('pos.bus', 'pos.bus.log', 'pos.tracking.client')""");

    def set_pricelists_to_pos_sessions_online_without_reload(self):
        for config in self:
            if config.pricelist_id:
                config.pricelist_id.sync_pricelists_all_pos_online()
                break
            else:
                raise UserError('Active la lista de precios y establezca la lista de precios predeterminada')
        return True

    def _get_product_field_char(self):
        product_fields = self.env['ir.model.fields'].search(
            [('model', '=', 'product.product'),
             ('ttype', '=', 'char')])
        return [
            (field.name, field.field_description)
            for field in sorted(product_fields, key=lambda f: f.field_description)
        ]
    def _get_customer_field_char(self):
        product_fields = self.env['ir.model.fields'].search(
            [('model', '=', 'res.partner'),
             ('ttype', '=', 'char')])
        return [
            (field.name, field.field_description)
            for field in sorted(product_fields, key=lambda f: f.field_description)
        ]

    def _get_picking_field_char(self):
        picking_fields = self.env['ir.model.fields'].search(
            [('model', '=', 'stock.picking'),
             ('ttype', '=', 'char')])
        return [
            (field.name, field.field_description)
            for field in sorted(picking_fields, key=lambda f: f.field_description)
        ]

    def _get_invoice_field_char(self):
        invoice_fields = self.env['ir.model.fields'].search(
            [('model', '=', 'account.move'),
             ('ttype', '=', 'char')])
        return [
            (field.name, field.field_description)
            for field in sorted(invoice_fields, key=lambda f: f.field_description)
        ]

    floor_ids = fields.Many2many(
        'restaurant.floor',
        'pos_config_restaurant_floor_rel',
        'pos_config_id',
        'floor_id',
        string="Pisos")

    active_design_layout = fields.Boolean(
        'Active Design Layout',
        help='Esta opción le permite diseñar la pantalla POS  \n'
             'Y todo su diseño se solucionará con su Pantalla en la PC que diseñe \n'
             'Si abre la pantalla POS otro tamaño de diferencia de pantalla con la última pantalla utilizada Diseño \n'
             'Toda la interfaz de usuario de diseño no será la misma \n'
             'Ejemplo: si utilizó un diseño de pantalla de visualización de 14 ", y el contador POS aplica este diseño, se requiere 14" igual'
    )
    load_design_of_pos_config_id = fields.Many2one('pos.config', 'Diseño de plantilla de carga de POS')
    user_id = fields.Many2one('res.users', 'Asignado a')
    config_access_right = fields.Boolean('Configuración de permisos', default=1)
    allow_discount = fields.Boolean('Permitir cambio en los descuentos', default=1)
    allow_qty = fields.Boolean('Permitir cantidad de cambio', default=1)
    allow_price = fields.Boolean('Permitir cambio de precio', default=1)
    allow_remove_line = fields.Boolean('Permitir remover líneas', default=1)
    allow_numpad = fields.Boolean('Permitir uso de teclado numérico', default=1)
    allow_payment = fields.Boolean('Permitir pagos', default=1)
    allow_customer = fields.Boolean('Permitir establecer un cliente', default=1)
    allow_add_order = fields.Boolean('Permitir agregar Orden', default=1)
    allow_remove_order = fields.Boolean('Permitir remover Orden', default=1)
    allow_add_product = fields.Boolean('Permitir agregar Producto', default=1)
    allow_payment_zero = fields.Boolean(
        'Permitir pago en 0',
        default=1,
        help='Si está activo, el cajero puede hacer que el monto total del pedido sea menor o igual a 0')
    allow_lock_screen = fields.Boolean(
        'Pantalla de bloqueo cuando se inicia la sesión',
        default=0,
        help='Cuando comienzan las sesiones pos, \n'
             'los cajeros requieren un punto de venta abierto a través del pase PIN (Configuración / Usuarios)')
    allow_offline_mode = fields.Boolean(
        'Permitir modo sin conexión',
        default=1,
        help='Internet requerido de los cajeros Counter Devlice utilizó la sesión POS en línea \n'
             'Si tiene problemas con Internet del cajero, el punto de venta no permite enviar pedidos al backend \n'
             'Problema de caso de ejemplo: \n'
             '1) Intenet sin conexión, los cajeros envían pedidos al servidor Odoo y no tienen éxito \n'
             '2) Y luego borran la exploración de caché y se eliminan los pedidos guardados en la caché de exploración \n'
             '- Significa que todos los pedidos se perderán \n'
             'Entonces, esta función está activa, cuando cualquier pedido se envía al backend, POS verifica automáticamente el servidor Odoo en línea o no. Si está en línea, permita Validar pedido'
    )
    display_point_receipt = fields.Boolean(
        'Punto de visualización / recibo', help='Active este campo para mostrar lealtad\n'
                                        ' punto más en recibo de factura')
    loyalty_id = fields.Many2one(
        'pos.loyalty', 'Loyalty',
        domain=[('state', '=', 'running')])
    loyalty_combine_promotion = fields.Boolean(
        'Promoción de lealtad combinada',
        help='Si está marcado: permita cada línea de pedido, la lealtad más el punto y la promoción se aplican juntos \n'
             'Si no está marcada: cuando la promoción se agrega a las líneas de pedido, los puntos no serán más'
    )
    promotion_manual_select = fields.Boolean(
        'Elección manual de promoción', default=0,
        help='Cuando marque esta casilla de verificación, \n'
             'Tus cajeros tendrán un botón, \n'
             'Cuando los cajeros hicieron clic en él, \n'
             'todas las promociones activas se mostrarán para elegir')
    promotion_auto_add = fields.Boolean(
        'Promoción automática Aplicar',
        help='Cuando se selecciona,\n'
             'Cuando sus cajeros hagan clic en el botón de pago,\n'
             'todas las promociones activas se auto agregan al pedido')

    create_purchase_order = fields.Boolean('Crear Orden de Compra', default=0)
    create_purchase_order_required_signature = fields.Boolean(
        'PO requiere firma', default=0)
    purchase_order_state = fields.Selection([
        ('confirm_order', 'Auto Confirm'),
        ('confirm_picking', 'Auto Delivery'),
    ], 'Purchaser Order Auto',
        help='Este es el estado del pedido que se procesará para',
        default='confirm_order')
    sale_order = fields.Boolean('Create Sale Order', default=0)
    sale_order_auto_confirm = fields.Boolean('Auto Confirm', default=0)
    sale_order_auto_invoice = fields.Boolean('Auto Paid', default=0)
    sale_order_auto_delivery = fields.Boolean('Auto Delivery', default=0)
    sale_order_required_signature = fields.Boolean(
        'Orden de Venta requiere firma',
        help='Permitir imprimir recibo al crear presupuesto / pedido')

    pos_orders_management = fields.Boolean(
        'Gestión de pedidos de punto de venta',
        default=0)
    shipping_order = fields.Boolean(
        'Orden de entrega',
        default=1,
        help='Crear orden de entrega (COD) \n'
             'Permitir a los cajeros crear una dirección de envío y guardar en el pedido, hacer un pago parcial \n'
             'Cuando el hombre de entrega realiza el pedido correctamente, el cajero confirma el pedido pagado \n'
             'Si activa esta opción, active también el Pago parcial\n'
             'Para que el cajero agregue una parte del pago del Cliente'
    )
    paid_partial = fields.Boolean(
        'Permitir pago parcial', default=1,
        help='Permita que los cajeros paguen una parte del monto total del pedido')
    load_orders_type = fields.Selection([
        ('last_7_days', 'Últimos 7 días a partir de ahora'),
        ('last_1_month', 'Últimos 30 meses a partir de ahora'),
        ('last_1_year', 'Último 1 año (365 días) a partir de ahora'),
        ('load_all', 'Cargar todo'),
    ],
        default='last_7_days',
        string='Período días cargando pedidos'
    )
    pos_orders_filter_by_branch = fields.Boolean(
        'Sucursal de filtro de orden POS', default=0,
        help='Si se selecciona, \n'
             'pos sesión no puede ver las órdenes de otra sucursal')
    pos_order_period_return_days = fields.Float(
        'Período de devolución días',
        help='Esto es días de período permiten al cliente \n'
             'puede devolver el pedido o una parte del pedido',
        default=30)
    display_pos_order_return_policy = fields.Boolean(
        'Mostrar recibo de política de devolución',
        default=1
    )
    pos_order_return_policy = fields.Text(
        'Política de devoluciones',
        default='7 días para devoluciones'
    )
    required_reason_return = fields.Boolean(
        'Motivo Requerido Retorno',
        help='Entrada de cajero requerida Motivo Devuelva cada línea si el Pedido es devuelto'
    )
    hide_buttons_order_return = fields.Boolean(
        'Ocultar botones si la orden vuelve',
        default=0,
        help='Ocultar todos los botones cuando la orden es el modo de retorno')
    display_return_days_receipt = fields.Boolean('Mostrar días de devolución en el recibo', default=0)
    display_onhand = fields.Boolean(
        'Mostrar stock en mano de cada producto', default=1,
        help='Muestra la cantidad disponible de todos los productos en la pantalla pos')
    allow_order_out_of_stock = fields.Boolean(
        'Permitir venta cuando el producto está agotado',
        default=1)
    print_voucher = fields.Boolean(
        'Crear cupón',
        help='Permitir a los cajeros crear un Cupón Manual en el POS',
        default=0)
    expired_days_voucher = fields.Integer(
        'Días de vencimiento del cupón',
        default=30,
        help='Total de días que puede usar el cupón, \n'
             'si fuera del período de días desde la fecha de creación, el comprobante caducará')
    sync_multi_session = fields.Boolean('Sincronizar entre sesiones', default=0)
    sync_to_pos_config_ids = fields.Many2many(
        'pos.config',
        'sync_session_rel',
        'from_id',
        'to_id',
        string='Sincronizar con configuraciones POS',
        domain="['|', ('pos_branch_id', '=', pos_branch_id), ('pos_branch_id', '=', None)]",
        help='Cualquier cambio de eventos desde esta configuración pos se sincronizará directamente \n' \
             'a esta configuración pos seleccionada aquí'
    )
    sync_manual_button = fields.Boolean(
        'Botón manual de sincronización',
        help='Si está activo, la sesión pos tendrá el botón Sincronizar seleccionado \n'
             'Al hacer clic en él, el orden seleccionado sincronizará otras configuraciones de posición agregadas anteriormente\n'
             'El orden seleccionado reemplazará otro orden de otra sesión con el mismo uid')
    sync_multi_session_offline = fields.Boolean('Sincronizar entre sesiones sin conexión', default=0)
    sync_multi_session_offline_iot_ids = fields.Many2many('pos.iot', 'pos_config_iot_rel', 'pos_config_id',
                                                          'iot_box_id', string='IoT Cajas',
                                                          help='Uso de la caja de IoT para la sincronización entre sesiones \n'
                                                               'cuando Odoo Server Offline o su Internet desconectado')
    display_person_add_line = fields.Boolean('Mostrar líneas de información', default=0,
                                             help="Cuando marcó, en la pantalla de líneas de orden pos, \n"
                                                  "mostrará información creada por la persona \n"
                                                  "(líneas) Ej .: fecha de creación, fecha actualizada ..")
    internal_transfer = fields.Boolean('Permitir transferencia interna', default=0,
                                       help='Ir a Inventario y activar almacén múltiple y ubicación')

    discount = fields.Boolean('Descuento global', default=0)
    delay = fields.Integer('Tiempo de retardo', default=3000)

    guide_pos = fields.Boolean('Mostrar guía POS', default=1)

    discount_limit = fields.Boolean('Límite de descuento', default=0)
    discount_limit_amount = fields.Float('Límite de descuento (%)', default=10)
    discount_sale_price = fields.Boolean('Precio de venta con descuento')
    discount_sale_price_limit = fields.Float(
        'Límite de descuento en el precio de venta',
        help='El cajero no pudo establecer un precio de descuento mayor o igual a este campo'
    )
    return_products = fields.Boolean('Permitir al cajera devolución de productos / pedidos',
                                     help='Permitir al cajera devolución de productos, pedidos',
                                     default=0)
    return_duplicate = fields.Boolean(
        'Permitir pedido de devolución duplicado',
        help='Si está marcado, un pedido puede regresar muchas veces'
    )
    lock_order_printed_receipt = fields.Boolean('Bloquear Orden de Recibo impreso', default=0)

    validate_payment = fields.Boolean('Validar pago')
    validate_remove_order = fields.Boolean('Validar eliminar orden')
    validate_new_order = fields.Boolean('Validar nueva orden')
    validate_login_pos = fields.Boolean('Validar Login POS')
    validate_change_minus = fields.Boolean('Validar presionados +/-')
    validate_quantity_change = fields.Boolean('Validar cambio de cantidad')
    validate_price_change = fields.Boolean('Validar cambio de precio')
    validate_discount_change = fields.Boolean('Validar cambio de descuento')
    validate_remove_line = fields.Boolean('Validar quitar línea')
    validate_close_session = fields.Boolean('Validar cierre de sesión')
    apply_validate_return_mode = fields.Boolean(
        'Validar modo de retorno',
        help='Si está marcado, solo se aplica validar cuando se devuelve el pedido',
        default=1)

    print_user_card = fields.Boolean('Imprimir tarjeta de usuario')

    product_operation = fields.Boolean(
        'Operación del producto', default=0,
        help='Permitir que los cajeros agreguen categorías y productos pos en la pantalla pos')
    quickly_payment_full = fields.Boolean('Rápidamente pagado completo')
    note_order = fields.Boolean('Orden de notas', default=0)
    note_orderline = fields.Boolean('Nota línea de pedido', default=0)
    signature_order = fields.Boolean('Orden de firma', default=0)
    display_amount_discount = fields.Boolean('Mostrar importe de descuento', default=1)

    booking_orders = fields.Boolean(
        'Pedidos de reserva',
        default=0,
        help='Orders may be come from many sources locations\n'
             'Example: Web E-Commerce, Call center, or phone call order\n'
             'And your Cashiers will made Booking Orders and save it\n'
             'Your Shipper or customer come shop will delivery Orders')
    load_booked_orders_type = fields.Selection([
        ('last_7_days', 'Last 7 Days from now'),
        ('last_1_month', 'Last 30 Month from now'),
        ('last_1_year', 'Last 1 Year (365 days) from now'),
        ('load_all', 'Load All'),
    ],
        default='last_7_days',
        string='Period days loading Booked Orders'
    )
    booking_orders_required_cashier_signature = fields.Boolean(
        'Required Signature',
        help='When your cashiers create Book Order\n'
             'Will require your cashier signature on order',
        default=0)
    booking_orders_alert = fields.Boolean(
        'Alert Order Coming', default=0,
        help='When have any Booking Order come from another Source Location to POS\n'
             'POS will Alert one popup inform your cashier have new Order coming')
    booking_allow_confirm_sale = fields.Boolean(
        'Delivery Booked Orders', default=0,
        help='Allow Cashier can Confirm Booked Orders and create Delivery Order')
    delivery_orders = fields.Boolean(
        'Delivery Order',
        help='Finish Order and Give Receipt to your Shipper delivery Order',
        default=0)
    booking_orders_display_shipping_receipt = fields.Boolean('Shipping Address Receipt', default=0)
    display_tax_orderline = fields.Boolean('Display Taxes Order Line', default=0)
    display_tax_receipt = fields.Boolean('Display Taxes Receipt', default=0)
    display_fiscal_position_receipt = fields.Boolean('Display Fiscal Position on Receipt', default=0)

    display_image_orderline = fields.Boolean('Display Image on Order Lines', default=0)
    display_image_receipt = fields.Boolean('Display Image on Receipt', default=0)
    duplicate_receipt = fields.Boolean(
        'Duplicate Receipt',
        help='If you need print bigger than 1 receipt / 1 order,\n'
             ' add bigger than 1')
    print_number = fields.Integer(
        'No.of Receipt',
        help='How many Bill need print on one Order', default=0)
    allow_cashier_update_print_number = fields.Boolean(
        'Allow Cashier Update Print Number',
        help='If checked, Cashier can change number of receipt via Payment Screen'

    )
    category_wise_receipt = fields.Boolean(
        'Category Wise Receipt',
        default=0,
        help='Bill will wise each POS Category')
    management_invoice = fields.Boolean('Display Invoices Screen', default=0)
    load_invoices_type = fields.Selection([
        ('last_7_days', 'Last 7 Days from now'),
        ('last_1_month', 'Last 1 Month (30 days) from now'),
        ('last_1_year', 'Last 1 Year (365 days) from now'),
        ('load_all', 'Load All'),
    ],
        default='last_7_days',
        string='Period days loading Invoices'
    )
    invoice_offline = fields.Boolean(
        'Invoice Offline Mode',
        help='Any Orders come from POS Session always create invoice \n'
             'Invoice will create few second after POS Orders created \n'
             'This future not print invoice number on POS Receipt \n'
             'Only create invoice each order and auto post invoice when POS Order submitted to backend \n'
             'Please set Customer Default or all orders on POS required set Customer before do payment'
    )
    invoice_offline_auto_register_payment = fields.Boolean(
        'Auto Register Payment',
        help='Any Invoice create from Order will auto register payment and reconcile'
    )
    wallet = fields.Boolean(
        'Wallet Card',
        help='Keeping all change money back to Customer Wallet Card\n'
             'Example: customer bought products with total amount is 9.5 USD\n'
             'Customer give your Cashier 10 USD, \n'
             'Default your cashier will return back change money 0.5 USD\n'
             'But Customer no want keep it, \n'
             'They need change money including to Wallet Card for next order\n'
             'Next Time customer come back, \n'
             'When your cashier choice client have Wallet Credit Amount bigger than 0\n'
             'Customer will have one more payment method via Wallet Credit')
    invoice_journal_ids = fields.Many2many(
        'account.journal',
        'pos_config_invoice_journal_rel',
        'config_id',
        'journal_id',
        'Dynamic Account Journal',
        domain=[('type', '=', 'sale')],
        help="Default POS Odoo save Invoice Journal from only one Invoicing Journal of POS Config\n"
             "This future allow you add many Journals here\n"
             "And when your cashier choice Journal on POS\n"
             "Invoice create from order will the same Journal selected by cashier")
    send_invoice_email = fields.Boolean(
        'Send email invoice',
        help='Help cashier send invoice to email of customer',
        default=0)
    pos_auto_invoice = fields.Boolean(
        'Auto create Invoice',
        help='Auto check to button Invoice on POS Payment Screen',
        default=0)
    receipt_customer_vat = fields.Boolean(
        'Add Customer Vat on Receipt',
        help='Show customer VAT(TIN) on receipt header', default=0)
    fiscal_position_auto_detect = fields.Boolean(
        'Fiscal position auto detect',
        default=0
    )
    display_sale_price_within_tax = fields.Boolean(
        'Display Sale Price Within Taxes',
        default=1
    )
    display_cost_price = fields.Boolean('Display Cost Price', default=0)
    display_product_ref = fields.Boolean('Display Product Ref', default=0)
    display_product_second_name = fields.Boolean(
        'Display Product Second Name',
        default=1,
        help='If you need show Product Second Name on product record \n'
             'Active it for display second name on order cart and receipt/bill'
    )
    hide_product_image = fields.Boolean('Hide Product Image', default=0)
    multi_location = fields.Boolean('Allow Multi Location', default=0)
    multi_location_check_stock_line_selected = fields.Boolean(
        'Check Stock On hand each Product',
        help='Allow cashier check stock on hand of line in cart selected'
    )
    multi_location_update_default_stock = fields.Boolean(
        'Change default Stock',
        help='Allow cashier change default pos warehouse stock'
    )
    multi_location_check_all_stock = fields.Boolean('Check stock on hand products all stock locations')
    update_stock_onhand_realtime = fields.Boolean(
        'Update Stock onhand Realtime',
        help='Auto update stock on hand of products realtime \n'
             'If this future active, may be pos actions will slow when change order selected \n'
             'Because POS auto update stock on hand of products via event change order selected'
    )
    product_view = fields.Selection([
        ('box', 'Box View'),
        ('list', 'List View'),
    ], default='box', string='Product Screen View Type', required=1)
    product_image_size = fields.Selection([
        ('default', 'Default'),
        ('small', 'Small'),
        ('big', 'Big')
    ],
        default='big',
        string='Product Image Size')
    ticket_font_size = fields.Integer('Bill Font Size', default=12,
                                      help='Font Size of Bill print via Web, not support posbox')
    allow_ticket_font_size = fields.Boolean(
        'Allow Cashier change Fontsize',
        help='Allow Cashier change Fontsize of Receipt'
    )
    customer_default_id = fields.Many2one('res.partner', 'Customer Default', help='When you put customer here, \n'
                                                                                  'when cashier create new order, pos auto add this customer to order for default')
    medical_insurance = fields.Boolean('Medical insurance', default=0)
    set_guest = fields.Boolean('Set Guests', default=0)
    set_guest_when_add_new_order = fields.Boolean(
        'Auto Ask Guests',
        help='When Cashiers add Orders, pos auto popup and ask guest name and guest number')
    reset_sequence = fields.Boolean('Reset Sequence Order', default=0)
    update_tax = fields.Boolean(
        'Modify Taxes of Lines',
        default=0,
        help='Allow Cashiers can change Taxes of Lines')
    update_tax_ids = fields.Many2many(
        'account.tax',
        'pos_config_tax_rel',
        'config_id',
        'tax_id', string='List Taxes')
    subtotal_tax_included = fields.Boolean(
        'Show Tax-Included Prices',
        help='When checked, subtotal each line of Order Cart and Bill/Receipt will display Total Amount with taxes included')
    cash_out = fields.Boolean('Take Money Out', default=0, help='Allow cashiers take money out')
    cash_in = fields.Boolean('Push Money In', default=0, help='Allow cashiers input money in')
    min_length_search = fields.Integer(
        'Min Character Search',
        default=3,
        help='Allow auto suggestion items when cashiers input on search box')
    review_receipt_before_paid = fields.Boolean(
        'Display Receipt Before Payment',
        help='On Payment Screen and Client Screen,\n'
             ' receipt will render left page for review',
        default=1)
    switch_user = fields.Boolean('Switch User', default=0, help='Allow cashiers user change between pos config')
    change_unit_of_measure = fields.Boolean('Change Unit of Measure', default=0,
                                            help='Allow cashiers change unit of measure of order lines')
    print_last_order = fields.Boolean(
        'Print Last Receipt',
        default=0,
        help='Allow cashiers print last receipt')
    printer_on_off = fields.Boolean('On/Off printer', help='Help cashier turn on/off printer via posbox', default=0)
    check_duplicate_email = fields.Boolean('Check duplicate email', default=0)
    check_duplicate_phone = fields.Boolean('Check duplicate phone', default=0)
    hide_title = fields.Boolean('Hide Title', default=1)
    hide_country = fields.Boolean('Hide Country', default=0)
    hide_barcode = fields.Boolean('Hide Barcode', default=0)
    hide_tax = fields.Boolean('Hide Taxes', default=0)
    hide_pricelist = fields.Boolean('Hide Pricelists', default=0)
    quickly_search_client = fields.Boolean("Quickly Search Client", default=1)
    required_title = fields.Boolean('Required Title')
    required_street = fields.Boolean('Required Street')
    required_city = fields.Boolean('Required City')
    required_birthday = fields.Boolean('Required Birthday')
    required_email = fields.Boolean('Required Email')
    required_phone = fields.Boolean('Required Phone')
    required_mobile = fields.Boolean('Required Mobile')
    required_pricelist = fields.Boolean('Required Pricelist')
    auto_remove_line = fields.Boolean(
        'Auto Remove Line',
        default=1,
        help='When cashier set quantity of line to 0, \n'
             'Line auto remove not keep line with qty is 0')
    chat = fields.Boolean(
        'Chat message',
        default=1,
        help='Online support visitors website \n'
             'Take Order from website ecommerce \n'
             'Discuss between users backend and between pos sessions')
    add_sale_person = fields.Boolean('Add Sale Person', default=0)
    default_seller_id = fields.Many2one(
        'res.users',
        'Default Seller',
        help='This is Seller automatic assigned to new Orders and new Order Lines'
    )
    seller_ids = fields.Many2many(
        'res.users',
        'pos_config_sellers_rel',
        'config_id',
        'user_id',
        string='Sellers',
        help='This is list sellers use for choice and add to Order or Order Line')
    force_seller = fields.Boolean(
        'Force Seller',
        help='When Your POS session select/change another Seller \n'
             'POS auto assigned New Seller to each Line of Order Cart',
        default=0)
    fast_remove_line = fields.Boolean('Fast Remove Line', default=1)
    logo = fields.Binary('Receipt Logo')
    suggest_cash_amount_payment = fields.Boolean('Suggest Cash Amount Payment')
    suggest_cash_ids = fields.Many2many('pos.quickly.payment')
    paid_full = fields.Boolean(
        'Full Fill Cash Payment', default=0,
        help='Auto Full Fill Cash Payment')
    backup = fields.Boolean(
        'Backup/Restore Orders Manual', default=0,
        help='Allow cashiers backup and restore orders on pos screen')
    backup_orders = fields.Text('Backup Orders', readonly=1)
    backup_orders_automatic = fields.Boolean(
        'Automatic BackUp Orders',
        help='Schedule 5 seconds, POS Session automatic backup Orders to BackEnd Odoo \n'
             'If POS Sessions Screen crashed, Computer PC Crashed or Browse Crashed ... could not open POS back \n'
             'Them can change to another PC, Devices and Open POS Session back \n'
             'Last Orders not Paid will automatic restore \n'
             'Nothing Unpaid Orders lost on POS Session \n'
             'Only Case will lost UnPaid Orders: POS Users turnoff Internet and them Remove Cache of Browse (**)\n'
             'With (**), we have not solution for covert It. Required Input Orders Unpaid Manual back'
    )
    change_logo = fields.Boolean(
        'Change Shop Logo', default=1, help='Allow cashiers change logo of shop on pos screen')
    management_session = fields.Boolean(
        'Management Cash Control',
        default=0,
        help='Allow pos users can take money in/out session\n'
             'If you active this future please active Cash Control of POS Odoo Original too'
    )
    cash_inout_reason_ids = fields.Many2many(
        'product.product',
        'pos_config_cash_inout_product_rel',
        'config_id',
        'product_id',
        sting='Cash In/Out Reason')
    barcode_receipt = fields.Boolean('Display Barcode Receipt', default=0)
    print_delivery_report = fields.Boolean(
        'Print Delivery Report',
        default=0,
        help='If you active it \n'
             'When Cashiers print POS Bill, POS auto print PDF Delivery Order Report'
    )
    print_order_report = fields.Boolean('Print Order Report',
                                        default=0,
                                        help='If you active it \n'
                                             'When Cashiers print POS Bill, POS auto print PDF POS Order Report'
                                        )
    hide_mobile = fields.Boolean("Hide Client's Mobile", default=1)
    hide_phone = fields.Boolean("Hide Client's Phone", default=1)
    hide_email = fields.Boolean("Hide Client's Email", default=1)
    update_client = fields.Boolean('Allow Update Clients',
                                   help='Uncheck if you dont want cashier change customer information on pos')
    add_client = fields.Boolean(
        'Allow Add Client',
        help='Allow POS Session can create new Client')
    remove_client = fields.Boolean('Allow Remove Clients',
                                   help='Uncheck if you dont want cashier remove customers on pos')
    mobile_responsive = fields.Boolean('Mobile Mode', default=0)
    report_no_of_report = fields.Integer(string="No.of copy Receipt", default=1)
    report_signature = fields.Boolean(string="Report Signature", default=0)

    report_product_summary = fields.Boolean(string="Report Product Summary", default=0)
    report_product_current_month_date = fields.Boolean(string="Report This Month", default=0)
    report_product_summary_auto_check_product = fields.Boolean('Auto Checked to Product Summary')
    report_product_summary_auto_check_category = fields.Boolean('Auto Checked to Product Category Summary')
    report_product_summary_auto_check_location = fields.Boolean('Auto Checked to Product Location Summary')
    report_product_summary_auto_check_payment = fields.Boolean('Auto Checked to Product Payment Summary')

    report_order_summary = fields.Boolean(string='Report Order Summary', default=0)
    report_order_current_month_date = fields.Boolean(string="Report Current Month", default=0)
    report_order_summary_auto_check_order = fields.Boolean('Auto Checked to Order Summary')
    report_order_summary_auto_check_category = fields.Boolean('Auto Checked to Order Category Summary')
    report_order_summary_auto_check_payment = fields.Boolean('Auto Checked to Order Payment Summary')
    report_order_summary_default_state = fields.Selection([
        ('new', 'New'),
        ('paid', 'Paid'),
        ('posted', 'Posted'),
        ('invoiced', 'Invoiced'),
        ('all', 'All')
    ], string='Report with state', default='all')

    report_payment_summary = fields.Boolean(string="Report Payment Summary", default=0)
    report_payment_current_month_date = fields.Boolean(string="Payment Current Month", default=0)

    report_sale_summary = fields.Boolean('Report Sale Summary (Z-Report)')
    report_sale_summary_show_profit = fields.Boolean('Report Sale Summary show Gross/Profit')
    report_current_session_report = fields.Boolean('Auto checked current session')

    active_product_sort_by = fields.Boolean('Active Sort By Product', default=0)
    default_product_sort_by = fields.Selection([
        ('a_z', 'Sort Name A to Z'),
        ('z_a', 'Sort Name Z to A'),
        ('low_price', 'Sort from Low to High Sale Price'),
        ('high_price', 'Sort from High to Low Sale Price'),
        ('pos_sequence', 'Product POS Sequence')
    ], string='Default Sort By', default='a_z')
    add_customer_before_products_already_in_shopping_cart = fields.Boolean(
        'Required choice Client before Add to Cart',
        help='Add customer before products \n'
             'already in shopping cart',
        default=0)
    allow_cashier_select_pricelist = fields.Boolean(
        'Allow Cashier select Pricelist',
        help='If uncheck, pricelist only work when select customer.\n'
             ' Cashiers could not manual choose pricelist',
        default=1)
    big_datas_turbo = fields.Boolean(
        'Turbo Starting POS Session',
        help='If you active it, any change from backend like pos config, payment method ... not load new when reload POS Session \n'
             'Only use it when everything ready to sell on POS'
    )
    big_datas_sync_backend = fields.Boolean(
        'Auto Sync Reltime with Backend',
        help='If have any change Products/Customer. POS auto sync with event change',
        default=1)
    sale_with_package = fields.Boolean(
        'Sale with Package')
    allow_set_price_smaller_min_price = fields.Boolean(
        'Allow Cashier set Price smaller than Sale Price of Product',
        default=1)
    checking_lot = fields.Boolean(
        'Validate Lot/Serial Number',
        help='Validate lot name input by cashiers is wrong or correctly')

    sync_sales = fields.Boolean(
        'Sync Sales/Quotations', default=1,
        help='Synchronize quotations/sales order between backend and pos')
    auto_nextscreen_when_validate_payment = fields.Boolean(
        'Auto Next Screen',
        help='Auto Next Screen when Cashiers Validate Order',
        default=0)
    auto_print_web_receipt = fields.Boolean('Auto Print Web Receipt', default=0)
    multi_lots = fields.Boolean('Allow Multi Lots/Serial', help='One order line can set many lots')
    create_lots = fields.Boolean('Allow Create Lots/Serial', help='Allow cashier create lots on pos')
    promotion_ids = fields.Many2many(
        'pos.promotion',
        'pos_config_promotion_rel',
        'config_id',
        'promotion_id',
        string='Promotions Applied')
    replace_payment_screen = fields.Boolean(
        'Replace Payment Screen', default=0,
        help='If checked, payment screen and products made to one \n'
             'Keyboard of payment screen will turn off\n'
             'This future only support on PC, without mobile tablet')
    pos_branch_id = fields.Many2one('pos.branch', 'Branch')

    stock_location_ids = fields.Many2many(
        'stock.location', string='Stock Locations',
        help='Stock Locations for cashier select checking stock on hand \n'
             'and made picking source location from location selected',
        domain=[('usage', '=', 'internal')])
    validate_by_manager = fields.Boolean('Validate by Managers')
    discount_unlock_by_manager = fields.Boolean('Unlock Limit Discount by Manager')
    manager_ids = fields.Many2many('res.users', 'pos_config_res_user_manager_rel', 'config_id', 'user_id',
                                   string='Manager Validation')
    stock_location_id = fields.Many2one('stock.location', string='POS Default Source Location',
                                        related='picking_type_id.default_location_src_id',
                                        readonly=1)
    stock_location_dest_id = fields.Many2one('stock.location', string='POS Default Dest Location',
                                             related='picking_type_id.default_location_dest_id',
                                             readonly=1)
    receipt_display_subtotal = fields.Boolean('Receipt Display Sub Total', default=1)
    receipt_display_taxes = fields.Boolean('Receipt Display Taxes', default=1)
    receipt_display_warehouse = fields.Boolean('Receipt Display Warehouse', default=0)
    receipt_header_style = fields.Selection([
        ('left', 'Left'),
        ('center', 'Center'),
        ('right', 'Right')
    ],
        default='left',
        string='Header Receipt Style',
        help='Header style, this future only apply on posbox and printer connected\n'
             'Not apply for printer direct web browse'
    )
    receipt_fullsize = fields.Boolean(
        'Receipt FullSize',
        help='Replace POS Receipt default of Odoo Original \n'
             'To POS Receipt Report fullsize, allow Print Page A4 A5 ...'
    )
    validate_order_without_receipt = fields.Boolean(
        'Validate Order without Receipt',
        help='If checked, on pos payment screen, \n'
             'will have one button allow validate order without print Receipt',
        default=1
    )
    discount_value = fields.Boolean('Discount Value')
    discount_value_limit = fields.Float(
        'Discount Value Limit',
        help='This is limited money cashier can setff'
    )
    posbox_save_orders = fields.Boolean('Save Orders on PosBox')
    posbox_save_orders_iot_ids = fields.Many2many(
        'pos.iot',
        'pos_config_iot_save_orders_rel',
        'config_id',
        'iot_id',
        string='IoT boxes'
    )
    posbox_save_orders_server_ip = fields.Char(
        'Odoo Public Ip Address',
        help='Example Ip: 192.168.100.100'
    )
    posbox_save_orders_server_port = fields.Char(
        'Odoo Public Port Number',
        default='8069',
        help='Example Port: 8069'
    )
    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        'Analytic Account'
    )
    limit_categories = fields.Boolean("Restrict Available Product Categories")
    iface_available_categ_ids = fields.Many2many(
        'pos.category',
        string='Available PoS Product Categories',
        help='The point of sale will only display products \n'
             'which are within one of the selected category trees. \n'
             'If no category is specified, all available products will be shown')
    hide_dock = fields.Boolean('Hide Dock', default=0)
    barcode_scan_with_camera = fields.Boolean(
        'Use Camera Scan Barcode',
        help='If you check it, and your device use POS have camera \n'
             'You can use camera of device scan barcode for add products, return orders ....\n'
             'This future only supported web browse and SSL \n'
             'SSL required if you are on cloud. As without SSL permission of camera not work.'
    )
    barcode_scan_timeout = fields.Float(
        'Times timeout',
        default=1000,
        help='Period times timeout for next scan\n'
             '1000 = 1 second\n'
             'I good time for scan we think 1000'
    )
    rounding_total_paid = fields.Boolean('Rounding Amount Paid')
    rounding_type = fields.Selection([
        ('rounding_by_decimal_journal', 'By Decimal Rounding of Journal'),
        ('rounding_integer', 'Rounding to Integer'),
    ],
        default='rounding_integer',
        help='By Decimal Rounding Journal: We will follow rounding of Journal Decimal Rounding Amount\n'
             'Rounding Integer: \n'
             'From decimal from 0 to 0.25 become 0\n'
             'From decimal from 0.25 to 0.75 become 0.5\n'
             'From decimal from 0.75 to 0.999 become to 1')
    dynamic_combo = fields.Boolean(
        'Dynamic Combo',
        help='One Order Line can add many combo items,\n'
             'Combo items is product have checked Combo Item field \n'
             'When Combo Item add, price extra will included to Order Line selected \n'
             'If you active this future, please go to Products and check to Combo Item field \n'
             'And set Combo Price, POS Combo Category both for product combo item')

    service_charge_ids = fields.Many2many(
        'pos.service.charge',
        'pos_config_service_charge_rel',
        'config_id',
        'charge_id',
        string='Services Charge'
    )
    payment_reference = fields.Boolean(
        'Payment Reference',
        help='Allow cashier add reference Note each payment line'
    )
    display_margin = fields.Boolean('Display Margin %')
    turbo_sync_orders = fields.Boolean(
        'Turbo Sync Orders',
        default=0,
        help='Cashiers push orders from Session always save Order state Draft \n'
             'System automatic process Orders (create picking, add payment ...) And processing Orders to Paid\n'
             'Cashiers will push Orders from POS Session very fast, no need waiting times \n'
             'This future only apply on Orders not request Invoice'
    )
    customer_facing_screen = fields.Boolean(
        'Active Customer Facing Screen',
        help='If you have not IoT/pos Boxes, you can active it and use client facing screen'
    )
    allow_split_table = fields.Boolean('Allow Split Table')
    allow_merge_table = fields.Boolean('Merge/Combine Tables')
    start_session_oneclick = fields.Boolean(
        'Start Session One Click'
    )
    translate_products_name = fields.Boolean(
        'Load Translate Products Name',
        help='When active, all products name language will load correct language of language POS User started session',
        default=0
    )
    set_product_name_from_field = fields.Selection(
        _get_product_field_char,
        default='name',
        string='Product Name display by field',
        help="Choose the field of the table Product which will be used for Product Display"
    )
    replace_partners_name = fields.Boolean(
        'Replace Partners Name',
        help='When active, partners name will replace buy field you choose bellow',
        default=0
    )
    set_partner_name_from_field = fields.Selection(
        _get_customer_field_char,
        default='name',
        string='Customer Name display from field',
        help="Choose the field of the table Customer which will be used for Customer Display"
    )
    default_display_cart = fields.Boolean(
        'Default Display Cart',
        default=1,
        help='If uncheck, default Product Screen cart list will automatic invisible'
    )
    search_customer_not_found_auto_fill_to_field = fields.Selection(
        _get_customer_field_char,
        default='mobile',
        string='Search customer not found, auto full fill value inputed on search box to field',
        help="Please choice one field of table Customer \n"
             "If pos user search not found customer and click add new customer \n"
             "Value of search box automatic full fill to this field selected here"
    )
    add_picking_field_to_receipt = fields.Selection(
        _get_picking_field_char,
        default='name',
        string='Add Picking Field to Receipt',
        help="Please choose one field of Delivery Object\n"
             "Display to your POS receipt"
    )
    add_invoice_field_to_receipt = fields.Selection(
        _get_invoice_field_char,
        default='name',
        string='Add Invoice Field to Receipt',
        help="Please choose one field of Invoice Object\n"
             "for Display to your POS receipt"
    )
    create_quotation = fields.Boolean(
        'Create Quotation Order',
        help='Allow cashier create Quotation Order, \n'
             'If customer full fill payment order, automatic processing to paid \n'
             'Else cashier can cancel quotation direct POS screen'
    )

    def remove_sync_between_session_logs(self):
        for config in self:
            sessions = self.env['pos.session'].search([(
                'config_id', '=', config.id
            )])
            session_ids = [session.id for session in sessions]
            self.env['pos.sync.session.log'].search([
                ('send_to_session_id', 'in', session_ids)
            ]).unlink()
        return True

    def reinstall_database(self):
        ###########################################################################################################
        # new field append :
        #                    - update param
        #                    - remove logs datas
        #                    - remove cache
        #                    - reload pos
        #                    - reinstall pos data
        # reinstall data button:
        #                    - remove all param
        #                    - pos start save param
        #                    - pos reinstall with new param
        # refresh call logs:
        #                    - get fields domain from param
        #                    - refresh data with new fields and domain
        ###########################################################################################################
        parameters = self.env['ir.config_parameter'].sudo().search([('key', 'in',
                                                                     ['product.product', 'res.partner',
                                                                      'account.move',
                                                                      'account.move.line', 'pos.order',
                                                                      'pos.order.line',
                                                                      'sale.order', 'sale.order.line'])])
        if parameters:
            parameters.sudo().unlink()
        del_database_sql = ''' delete from pos_cache_database'''
        del_log_sql = ''' delete from pos_call_log'''
        self.env.cr.execute(del_database_sql)
        self.env.cr.execute(del_log_sql)
        self.env.cr.commit()
        for config in self:
            sessions = self.env['pos.session'].sudo().search(
                [('config_id', '=', config.id), ('state', '=', 'opened')])
            if not sessions:
                raise UserError(_('Please open one session and try again'))
            sessions.write({'required_reinstall_cache': True})
            config_fw = config
            self.env['pos.session'].sudo().search(
                [('config_id', '!=', config.id), ('state', '=', 'opened')]).write({'required_reinstall_cache': True})
        return {
            'type': 'ir.actions.act_url',
            'url': '/pos/web?config_id=%d' % config_fw.id,
            'target': 'self',
        }

    def remote_sessions(self):
        return {
            'name': _('Remote sessions'),
            'view_type': 'form',
            'target': 'new',
            'view_mode': 'form',
            'res_model': 'pos.remote.session',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'context': {},
        }

    def validate_and_post_entries_session(self):
        for config in self:
            sessions = self.env['pos.session'].search([('config_id', '=', config.id), ('state', '!=', 'closed')])
            if sessions:
                for session in sessions:
                    session.close_session_and_validate()
        return True

    def write(self, vals):
        if vals.get('allow_discount', False) or vals.get('allow_qty', False) or vals.get('allow_price', False):
            vals['allow_numpad'] = True
        if vals.get('expired_days_voucher', None) and vals.get('expired_days_voucher') < 0:
            raise UserError('Expired days of voucher could not smaller than 0')
            if config.pos_order_period_return_days <= 0:
                raise UserError('Period days return orders and products required bigger than or equal 0 day')
        res = super(pos_config, self).write(vals)
        for config in self:
            if vals.get('management_session', False) and not vals.get('default_cashbox_id'):
                if not config.default_cashbox_id and not config.cash_control:
                    raise UserError(
                        'Your POS config missed config Default Opening (Cash Control), Please go to Cash control and set Default Opening')
        return res

    @api.model
    def create(self, vals):
        if vals.get('allow_discount', False) or vals.get('allow_qty', False) or vals.get('allow_price', False):
            vals['allow_numpad'] = True
        if vals.get('expired_days_voucher', 0) < 0:
            raise UserError('Expired days of voucher could not smaller than 0')
        config = super(pos_config, self).create(vals)
        if config.pos_order_period_return_days <= 0:
            raise UserError('Period days return orders and products required bigger than or equal 0 day')
        if config.management_session and not config.default_cashbox_id and not config.cash_control:
            raise UserError(
                'Your POS config missed config Default Opening (Cash Control), Please go to Cash control and set Default Opening')
        return config

    @api.model
    @api.onchange('management_session')
    def _onchange_management_session(self):
        self.cash_control = self.management_session

    def init_payment_method(self, journal_name, journal_sequence, journal_code, account_code, pos_method_type):
        Journal = self.env['account.journal'].sudo()
        Method = self.env['pos.payment.method'].sudo()
        IrModelData = self.env['ir.model.data'].sudo()
        IrSequence = self.env['ir.sequence'].sudo()
        Account = self.env['account.account'].sudo()
        user = self.env.user
        accounts = Account.search([
            ('code', '=', account_code), ('company_id', '=', self.company_id.id)])
        if accounts:
            accounts.sudo().write({'reconcile': True})
            account = accounts[0]

        else:
            account = Account.create({
                'name': journal_name,
                'code': account_code,
                'user_type_id': self.env.ref('account.data_account_type_current_assets').id,
                'company_id': self.company_id.id,
                'note': 'code "%s" auto give voucher histories of customers' % account_code,
                'reconcile': True
            })
            model_datas = IrModelData.search([
                ('name', '=', account_code + str(self.company_id.id)),
                ('module', '=', 'pos_retail'),
                ('model', '=', 'account.account'),
                ('res_id', '=', account.id),
            ])
            if not model_datas:
                IrModelData.create({
                    'name': account_code + str(self.company_id.id),
                    'model': 'account.account',
                    'module': 'pos_retail',
                    'res_id': account.id,
                    'noupdate': True,  # If it's False, target record (res_id) will be removed while module update
                })

        journals = Journal.search([
            ('code', '=', journal_code),
            ('company_id', '=', self.company_id.id),
        ])
        if journals:
            journals.sudo().write({
                'default_debit_account_id': account.id,
                'default_credit_account_id': account.id,
                'pos_method_type': pos_method_type,
                'sequence': journal_sequence,
            })
            journal = journals[0]
        else:
            new_sequence = IrSequence.create({
                'name': journal_name + str(self.company_id.id),
                'padding': 3,
                'prefix': account_code + str(self.company_id.id),
            })
            model_datas = IrModelData.search(
                [
                    ('name', '=', account_code + str(new_sequence.id)),
                    ('module', '=', 'pos_retail'),
                    ('model', '=', 'ir.sequence'),
                    ('res_id', '=', new_sequence.id),
                ])
            if not model_datas:
                IrModelData.create({
                    'name': account_code + str(new_sequence.id),
                    'model': 'ir.sequence',
                    'module': 'pos_retail',
                    'res_id': new_sequence.id,
                    'noupdate': True,
                })
            journal = Journal.create({
                'name': journal_name,
                'code': journal_code,
                'type': 'cash',
                'pos_method_type': pos_method_type,
                'sequence_id': new_sequence.id,
                'company_id': self.company_id.id,
                'default_debit_account_id': account.id,
                'default_credit_account_id': account.id,
                'sequence': journal_sequence,
            })
            model_datas = IrModelData.search(
                [
                    ('name', '=', account_code + str(journal.id)),
                    ('module', '=', 'pos_retail'),
                    ('model', '=', 'account.journal'),
                    ('res_id', '=', int(journal.id)),
                ])
            if not model_datas:
                IrModelData.create({
                    'name': account_code + str(journal.id),
                    'model': 'account.journal',
                    'module': 'pos_retail',
                    'res_id': int(journal.id),
                    'noupdate': True,
                })
        methods = Method.search([
            ('name', '=', journal_name),
            ('company_id', '=', self.company_id.id)
        ])
        if not methods:
            method = Method.create({
                'name': journal_name,
                'receivable_account_id': account.id,
                'is_cash_count': True,
                'cash_journal_id': journal.id,
                'company_id': self.company_id.id,
            })
        else:
            method = methods[0]
        for config in self:
            opened_session = config.mapped('session_ids').filtered(lambda s: s.state != 'closed')
            if not opened_session:
                payment_method_added_ids = [payment_method.id for payment_method in config.payment_method_ids]
                if method.id not in payment_method_added_ids:
                    payment_method_added_ids.append(method.id)
                    config.sudo().write({
                        'payment_method_ids': [(6, 0, payment_method_added_ids)],
                    })
        return True

    def open_ui(self):
        self.init_payment_method('Voucher', 100, 'JV', 'AJV', 'voucher')
        self.init_payment_method('Wallet', 101, 'JW', 'AJW', 'wallet')
        self.init_payment_method('Credit', 102, 'JC', 'AJC', 'credit')
        self.init_payment_method('Return Order', 103, 'JRO', 'AJRO', 'return')
        self.init_payment_method('Rounding Amount', 100, 'JRA', 'AJRA', 'rounding')
        return super(pos_config, self).open_ui()

    def open_session_cb(self):
        self.init_payment_method('Voucher', 100, 'JV', 'AJV', 'voucher')
        self.init_payment_method('Wallet', 101, 'JW', 'AJW', 'wallet')
        self.init_payment_method('Credit', 102, 'JC', 'AJC', 'credit')
        self.init_payment_method('Return Order', 103, 'JRO', 'AJRO', 'return')
        self.init_payment_method('Rounding Amount', 100, 'JRA', 'AJRA', 'rounding')
        return super(pos_config, self).open_session_cb()

    # TODO: for supported multi pricelist difference currency
    @api.constrains('pricelist_id', 'use_pricelist', 'available_pricelist_ids', 'journal_id', 'invoice_journal_id',
                    'payment_method_ids')
    def _check_currencies(self):
        return True
        # for config in self:
        #     if config.use_pricelist and config.pricelist_id not in config.available_pricelist_ids:
        #         raise ValidationError(_("The default pricelist must be included in the available pricelists."))
        # if self.invoice_journal_id.currency_id and self.invoice_journal_id.currency_id != self.currency_id:
        #     raise ValidationError(_(
        #         "The invoice journal must be in the same currency as the Sales Journal or the company currency if that is not set."))
        # if any(
        #         self.payment_method_ids \
        #                 .filtered(lambda pm: pm.is_cash_count) \
        #                 .mapped(
        #             lambda pm: self.currency_id not in (self.company_id.currency_id | pm.cash_journal_id.currency_id))
        # ):
        #     raise ValidationError(_(
        #         "All payment methods must be in the same currency as the Sales Journal or the company currency if that is not set."))

    def new_rate(self, from_amount, to_currency):
        pricelist_currency = self.env['res.currency'].browse(to_currency)
        company_currency = self.company_id.currency_id
        new_rate = company_currency._convert(from_amount, pricelist_currency,
                                             self.company_id or self.env.user.company_id, fields.Date.today())
        return new_rate

    def _open_session(self, session_id):
        session_form = super(pos_config, self)._open_session(session_id)
        session = self.env['pos.session'].browse(session_id)
        if session.config_id.start_session_oneclick:
            session.action_pos_session_open()
            return session.open_frontend_cb()
        else:
            return session_form
