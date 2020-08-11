odoo.define('pos_retail.big_data', function (require) {
    var models = require('point_of_sale.models');
    var export_models = require('point_of_sale.models');
    var session = require('web.session');
    var core = require('web.core');
    var _t = core._t;
    var db = require('point_of_sale.DB');
    var rpc = require('pos.rpc');
    var indexed_db = require('pos_retail.indexedDB');
    var screens = require('point_of_sale.screens');
    var QWeb = core.qweb;
    var field_utils = require('web.field_utils');
    var time = require('web.time');
    var utils = require('web.utils');
    var round_pr = utils.round_precision;
    var retail_db = require('pos_retail.database');

    var indexedDB = window.indexedDB || window.mozIndexedDB || window.webkitIndexedDB || window.msIndexedDB || window.shimIndexedDB;

    if (!indexedDB) {
        window.alert("Su navegador no admite una versión estable de IndexedDB.")
    }

    // TODO testing case:
    // 1. create new product/partner backend >> passed
    // 2. update product/partner at backend > passed
    // 3. remove product in backend without product in cart >> passed
    // 4. remove product in backend within product in cart >> passed
    // 5. product operation still update in pos and backend change / remove
    // 6. remove partner in backend
    // 7. remove partner in backend but partner have set in order
    // 8. update partner in backend but partner mode edit on pos

    var _super_PosModel = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        initialize: function (session, attributes) {
            var self = this;
            this.deleted = {};
            this.partner_model = null;
            this.product_model = null;
            this.total_products = 0;
            this.total_clients = 0;
            this.load_datas_cache = false;
            this.max_load = 9999;
            this.next_load = 10000;
            this.first_load = 10000;
            this.session = session;
            this.sequence = 0;
            this.model_lock = [];
            this.model_unlock = [];
            this.model_ids = session['model_ids'];
            this.company_currency_id = session['company_currency_id'];
            _super_PosModel.initialize.call(this, session, attributes);
            var fonts = _.find(this.models, function (model) { // TODO: odoo default need 5 seconds load fonts, we dont use font 'Lato','Inconsolata', it reason no need to wait
                return model.label == 'fonts'
            });
            fonts.loaded = function (self) {
                return true;
            };
            for (var i = 0; i < this.models.length; i++) {
                var this_model = this.models[i];
                if (this_model.model && this.model_ids[this_model.model]) {
                    this_model['max_id'] = this.model_ids[this_model.model]['max_id'];
                    this_model['min_id'] = this.model_ids[this_model.model]['min_id'];
                    if (this_model.model == 'product.product' && this_model.fields && this_model.fields.length >= 30) {
                        this.product_model = this_model;
                        this.model_lock.push(this_model);
                    }
                    if (this_model.model == 'res.partner' && this_model.fields) {
                        this.model_lock.push(this_model);
                        this.partner_model = this_model;
                    }
                } else {
                    this.model_unlock.push(this_model);
                }
            }
            if (this.product_model && this.partner_model) {
                models = {
                    'product.product': {
                        fields: this.product_model.fields,
                        domain: this.product_model.domain,
                        context: this.product_model.context,
                    },
                    'res.partner': {
                        fields: this.partner_model.fields,
                        domain: this.partner_model.domain,
                        context: this.partner_model.context,
                    }
                };
                rpc.query({
                    model: 'pos.cache.database',
                    method: 'save_parameter_models_load',
                    args: [[], models]
                }, {
                    shadow: true,
                    timeout: 60000
                }).then(function (reinstall) {
                    console.log('Result of save_parameter_models_load: ' + reinstall);
                }, function (err) {
                    console.error(err);
                });
            }
            this.models = this.model_unlock;
            var pos_session_object = this.get_model('pos.session');
            if (pos_session_object) {
                pos_session_object.fields.push('required_reinstall_cache')
            }
            this.indexed_db = new indexed_db(this);
            // TODO: loaded cache of browse
            this.indexed_db.get_datas(this, 'cached', 1).then(function (results) {
                self.json_datas = {};
                if (results && results.length) {
                    for (var i=0; i < results.length; i++) {
                        var result = results[i];
                        self.json_datas[result.id] = result.value
                    }
                }
            })
        },
        // TODO: sync backend
        update_products_in_cart: function (product_datas) {
            var orders = this.get('orders').models;
            for (var i = 0; i < orders.length; i++) {
                var order = orders[i];
                for (j = 0; j < product_datas.length; j++) {
                    var product = product_datas[j];
                    var lines_the_same_product = _.filter(order.orderlines.models, function (line) {
                        return line.product.id == product.id
                    });
                    if (!lines_the_same_product) {
                        continue
                    } else {
                        for (n = 0; n < lines_the_same_product.length; n++) {
                            var line_required_update = lines_the_same_product[n];
                            line_required_update.product = this.db.get_product_by_id(product['id']);
                            line_required_update.set_unit_price(product.lst_price);
                        }
                    }
                }
            }
        },
        remove_product_deleted_outof_orders: function (product_id) {
            var orders = this.get('orders').models;
            for (var n = 0; n < orders.length; n++) {
                var order = orders[n];
                for (var i = 0; i < order.orderlines.models.length; i++) {
                    var line = order.orderlines.models[i];
                    if (line.product.id == product_id) {
                        order.remove_orderline(line);
                    }
                }
            }
        },
        update_customer_in_cart: function (partner_datas) {
            var orders = this.get('orders').models;
            for (var i = 0; i < orders.length; i++) {
                var order = orders[i];
                var client_order = order.get_client();
                if (!client_order || order.finalized) {
                    continue
                }
                for (var n = 0; n < partner_datas.length; n++) {
                    var partner_data = partner_datas[n];
                    if (partner_data['id'] == client_order.id) {
                        var client = this.db.get_partner_by_id(client_order.id);
                        order.set_client(client);
                    }
                }
            }
        },
        remove_partner_deleted_outof_orders: function (partner_id) {
            var orders = this.get('orders').models;
            var order = orders.find(function (order) {
                var client = order.get_client();
                if (client && client['id'] == partner_id) {
                    return true;
                }
            });
            if (order) {
                order.set_client(null)
            }
            return order;
        },
        sync_with_backend: function (model, datas, dont_check_write_time) {
            var self = this;
            if (datas.length == 0) {
                console.warn('La sincronización de datos es antigua. Rechazar:' + model);
                return false;
            }
            this.db.set_last_write_date_by_model(model, datas);
            if (model == 'pos.order') {
                this.db.save_pos_orders(datas);
                for (var n = 0; n < datas.length; n++) {
                    var order = datas[n];
                    this.trigger('refresh:pos_orders_screen', order.id)
                }
            }
            if (model == 'pos.order.line') {
                this.db.save_pos_order_line(datas);
            }
            if (model == 'account.move') {
                this.db.save_invoices(datas);
                this.trigger('refresh:invoice_screen');
            }
            if (model == 'account.move.line') {
                this.db.save_invoice_lines(datas);
            }
            if (model == 'sale.order') {
                this.db.save_sale_orders(datas);
                var order = datas[0];
                if (!order.deleted && this.config.booking_orders_alert)
                    this.trigger('new:booking_order', order['id']);
            }
            if (model == 'sale.order.line') {
                this.db.save_sale_order_lines(datas);
            }
            if (model == 'res.partner') {
                var partner_datas = _.filter(datas, function (partner) {
                    return !partner.deleted || partner.deleted != true
                });
                if (partner_datas.length) {
                    this.db.add_partners(partner_datas);
                    if (this.gui.screen_instances && this.gui.screen_instances['clientlist']) {
                        this.gui.screen_instances["clientlist"].do_update_partners_cache(partner_datas);
                    }
                    this.update_customer_in_cart(partner_datas);
                    for (var i = 0; i < partner_datas.length; i++) {
                        var partner_data = partner_datas[i];
                        this.db.partners_removed = _.filter(this.db.partners_removed, function (partner_id) {
                            return partner_data.id != partner_id
                        });
                    }

                }
            }
            if (model == 'product.product') {
                var product_datas = _.filter(datas, function (product) {
                    return !product.deleted || product.deleted != true
                });
                if (product_datas.length && this.gui.screen_instances["products"]) {
                    if (this.gui.screen_instances && this.gui.screen_instances['products']) {
                        this.gui.screen_instances["products"].do_update_products_cache(product_datas);
                    }
                    this.update_products_in_cart(product_datas);
                    this.gui.screen_instances["products_operation"].refresh_screen();
                }
            }
            if (model == 'res.partner' || model == 'product.product') {
                var values_deleted = _.filter(datas, function (data) {
                    return data.deleted == true
                });
                var values_updated = _.filter(datas, function (data) {
                    return !data.deleted
                });
                if (values_updated.length) {
                    self.indexed_db.write(model, values_updated);
                }
                for (var i = 0; i < values_deleted.length; i++) {
                    var value_deleted = values_deleted[i];
                    self.indexed_db.unlink(model, value_deleted);
                    if (model == 'res.partner') {
                        this.remove_partner_deleted_outof_orders(value_deleted['id']);
                        this.db.partners_removed.push(value_deleted['id']);
                    }
                    if (model == 'product.product') {
                        this.remove_product_deleted_outof_orders(value_deleted['id']);
                        this.gui.screen_instances["products"].remove_product_out_of_screen(value_deleted);
                    }
                }
            }
        },
        // TODO : -------- end sync -------------
        query_backend_fail: function (error) {
            if (error && error.message && error.message.code && error.message.code == 200) {
                return this.gui.show_popup('error', {
                    title: error.message.code,
                    body: error.message.data.message,
                })
            }
            if (error && error.message && error.message.code && error.message.code == -32098) {
                return this.gui.show_popup('error', {
                    title: error.message.code,
                    body: 'Tu servidor Odoo sin conexión',
                })
            } else {
                return this.gui.show_popup('error', {
                    title: 'Error',
                    body: 'El modo fuera de línea de Odoo o los códigos de backend tienen problemas. Comuníquese con su administrador del sistema',
                })
            }
        },
        get_model: function (_name) {
            var _index = this.models.map(function (e) {
                return e.model;
            }).indexOf(_name);
            if (_index > -1) {
                return this.models[_index];
            }
            return false;
        },
        sort_by: function (field, reverse, primer) {
            var key = primer ?
                function (x) {
                    return primer(x[field])
                } :
                function (x) {
                    return x[field]
                };
            reverse = !reverse ? 1 : -1;
            return function (a, b) {
                return a = key(a), b = key(b), reverse * ((a > b) - (b > a));
            }
        },
        _get_active_pricelist: function () {
            var current_order = this.get_order();
            var default_pricelist = this.default_pricelist;
            if (current_order && current_order.pricelist) {
                var pricelist = _.find(this.pricelists, function (pricelist_check) {
                    return pricelist_check['id'] == current_order.pricelist['id']
                });
                return pricelist;
            } else {
                if (default_pricelist) {
                    var pricelist = _.find(this.pricelists, function (pricelist_check) {
                        return pricelist_check['id'] == default_pricelist['id']
                    });
                    return pricelist
                } else {
                    return null
                }
            }
        },
        get_process_time: function (min, max) {
            if (min > max) {
                return 1
            } else {
                return (min / max).toFixed(1)
            }
        },
        get_modifiers_backend: function (model) { // TODO: when pos session online, if pos session have notification from backend, we get datas modifires and sync to pos
            var self = this;
            return new Promise(function (resolve, reject) {
                if (self.db.write_date_by_model[model]) {
                    var args = [[], self.db.write_date_by_model[model], model, null];
                    if (model == 'pos.order' || model == 'pos.order.line') {
                        args = [[], self.db.write_date_by_model[model], model, self.config.id];
                    }
                    return rpc.query({
                        model: 'pos.cache.database',
                        method: 'get_modifiers_backend',
                        args: args
                    }).then(function (results) {
                        if (results.length) {
                            var model = results[0]['model'];
                            self.sync_with_backend(model, results);
                        }
                        self.set('sync_backend', {state: 'connected', pending: 0});
                        resolve()
                    }, function (error) {
                        self.query_backend_fail(error);
                        reject()
                    })
                } else {
                    resolve()
                }
            });
        },
        _bind_sync_backend: function () {
            var self = this;
            this.get_modifiers_backend_all_models().then(function (total_sync) {
                setTimeout(_.bind(self._bind_sync_backend, self), 5000);
                if (total_sync > 0) {
                    console.log('filas totales de backend actualizadas: ' + total_sync)
                }
            }, function (err) {
                console.error(err);
                setTimeout(_.bind(self._bind_sync_backend, self), 5000);
            })
        },
        get_modifiers_backend_all_models: function () { // TODO: get all modifiers of all models from backend and sync to pos
            var self = this;
            return new Promise(function (resolve, reject) {
                var model_values = self.db.write_date_by_model;
                var args = [];
                args = [[], model_values, self.config.id];
                rpc.query({
                    model: 'pos.cache.database',
                    method: 'get_modifiers_backend_all_models',
                    args: args
                }, {
                    shadow: true,
                    timeout: 65000,
                }).then(function (results) {
                    var total = 0;
                    for (var model in results) {
                        var vals = results[model];
                        if (vals && vals.length) {
                            self.sync_with_backend(model, vals);
                            total += vals.length;
                        }
                    }
                    resolve(total);
                }, function (err) {
                    reject(err);
                });
            });
        },
        save_results: function (model, results) { // TODO: When loaded all results from indexed DB, we restore back to POS Odoo
            if (model == 'product.product') {
                this.total_products += results.length;
                var process_time = this.get_process_time(this.total_products, this.model_ids[model]['count']) * 100;
                this.chrome.loading_message(_t('Productos agregados : ' + process_time.toFixed(0) + ' %'), process_time / 100);
            }
            if (model == 'res.partner') {
                this.total_clients += results.length;
                var process_time = this.get_process_time(this.total_clients, this.model_ids[model]['count']) * 100;
                this.chrome.loading_message(_t('Clientes agregados : ' + process_time.toFixed(0) + ' %'), process_time / 100);

            }
            var object = _.find(this.model_lock, function (object_loaded) {
                return object_loaded.model == model;
            });
            if (object) {
                object.loaded(this, results, {})
            } else {
                console.error('Could not find model: ' + model + ' for restoring datas');
                return false;
            }
            this.load_datas_cache = true;
            this.db.set_last_write_date_by_model(model, results);
        },
        reload_pos: function () {
            location.reload();
        },
        api_install_datas: function (model_name) {
            var self = this;
            var model = _.find(this.model_lock, function (model) {
                return model.model == model_name;
            });
            var installed = new Promise(function (resolve, reject) {
                function installing_data(model_name, min_id, max_id) {
                    self.chrome.loading_message(_t('Installing Model: ' + model_name + ' from ID: ' + min_id + ' to ID: ' + max_id));
                    var domain = [['id', '>=', min_id], ['id', '<', max_id]];
                    var context = {};
                    if (model['model'] == 'product.product') {
                        domain.push(['available_in_pos', '=', true]);
                        var price_id = null;
                        if (self.pricelist) {
                            price_id = self.pricelist.id;
                        }
                        var stock_location_id = null;
                        if (self.config.stock_location_id) {
                            stock_location_id = self.config.stock_location_id[0]
                        }
                        context['location'] = stock_location_id;
                        context['pricelist'] = price_id;
                        context['display_default_code'] = false;
                    }
                    if (min_id == 0) {
                        max_id = self.max_load;
                    }
                    rpc.query({
                        model: 'pos.cache.database',
                        method: 'install_data',
                        args: [null, model_name, min_id, max_id]
                    }).then(function (results) {
                        min_id += self.next_load;
                        if (typeof results == "string") {
                            results = JSON.parse(results);
                        }
                        if (results.length > 0) {
                            max_id += self.next_load;
                            installing_data(model_name, min_id, max_id);
                            self.indexed_db.write(model_name, results);
                            self.save_results(model_name, results);
                        } else {
                            if (max_id < model['max_id']) {
                                max_id += self.next_load;
                                installing_data(model_name, min_id, max_id);
                            } else {
                                resolve()
                            }
                        }
                    }, function (error) {
                        console.error(error.message.message);
                        var db = self.session.db;
                        for (var i = 0; i <= 100; i++) {
                            indexedDB.deleteDatabase(db + '_' + i);
                        }
                        reject(error)
                    })
                }

                installing_data(model_name, 0, self.first_load);
            });
            return installed;
        },
        remove_indexed_db: function () {
            var dbName = this.session.db;
            for (var i = 0; i <= 50; i++) {
                indexedDB.deleteDatabase(dbName + '_' + i);
            }
            console.log('remove_indexed_db exitoso !')
        },
        update_turbo_database: function () {
            console.log('Comenzar la actualización automática de Turbo Cache');
            var self = this;
            this.load_server_data_without_loaded().then(function (results) {
                var cached = [];
                for (var model in self.cached) {
                    cached.push({
                        id: model,
                        value: self.cached[model]
                    });
                }
                if (cached.length) {
                    self.indexed_db.write('cached', cached, true);
                }
                self.cached = null;
            })
        },
        load_server_data_without_loaded: function () {
            // TODO: this method calling backend with params models but no call loaded function each object
            var self = this;
            var progress = 0;
            var progress_step = 1.0 / self.models.length;
            var tmp = {}; // this is used to share a temporary state between models loaders
            this.cached = {};
            var loaded = new Promise(function (resolve, reject) {
                function load_model(index) {
                    if (index >= self.models.length) {
                        resolve();
                    } else {
                        var model = self.models[index];
                        var cond = typeof model.condition === 'function' ? model.condition(self, tmp) : true;
                        if (!cond) {
                            load_model(index + 1);
                            return;
                        }
                        var fields = typeof model.fields === 'function' ? model.fields(self, tmp) : model.fields;
                        var domain = typeof model.domain === 'function' ? model.domain(self, tmp) : model.domain;
                        var context = typeof model.context === 'function' ? model.context(self, tmp) : model.context || {};
                        var ids = typeof model.ids === 'function' ? model.ids(self, tmp) : model.ids;
                        var order = typeof model.order === 'function' ? model.order(self, tmp) : model.order;
                        progress += progress_step;

                        if (model.model && ['res.partner', 'product.product'].indexOf(model.model) == -1) {
                            var params = {
                                model: model.model,
                                context: _.extend(context, session.user_context || {}),
                            };
                            if (model.ids) {
                                params.method = 'read';
                                params.args = [ids, fields];
                            } else {
                                params.method = 'search_read';
                                params.domain = domain;
                                params.fields = fields;
                                params.orderBy = order;
                            }
                            rpc.query(params, {
                                shadow: true,
                                timeout: 60000
                            }).then(function (result) {
                                var model = self.models[index];
                                if (model.model) {
                                    if (!self.cached[model.model]) {
                                        self.cached[model.model] = [result]
                                    } else {
                                        self.cached[model.model].push(result)
                                    }
                                }
                                load_model(index + 1);
                            }, function (err) {
                                reject(err);
                            });
                        } else {
                            load_model(index + 1);
                        }
                    }
                }
                try {
                    return load_model(0);
                } catch (err) {
                    return Promise.reject(err);
                }
            });
            return loaded;
        },
        load_server_data: function () {
            var self = this;
            return _super_PosModel.load_server_data.apply(this, arguments).then(function () {
                self.models = self.models.concat(self.model_lock);
                if (self.config.big_datas_sync_backend) {
                    // TODO: waiting chrome pos starting success pos session screen
                    setTimeout(function () {
                        self._bind_sync_backend()
                    }, 5000)
                }
                self.update_turbo_database()
            });
        },
    });
    db.include({
        init: function (options) {
            this._super(options);
            this.write_date_by_model = {};
            this.products_removed = [];
            this.partners_removed = [];
        },
        set_last_write_date_by_model: function (model, results) {
            /* TODO: this method overide method set_last_write_date_by_model of Databse.js
                We need to know last records updated (change by backend clients)
                And use field write_date compare datas of pos and datas of backend
                We are get best of write date and compare
             */
            for (var i = 0; i < results.length; i++) {
                var line = results[i];
                if (line.deleted) {
                    continue
                }
                if (!this.write_date_by_model[model]) {
                    this.write_date_by_model[model] = line.write_date;
                    continue;
                }
                if (this.write_date_by_model[model] != line.write_date && new Date(this.write_date_by_model[model]).getTime() < new Date(line.write_date).getTime()) {
                    this.write_date_by_model[model] = line.write_date;
                }
            }
        },
        search_product_in_category: function (category_id, query) {
            var self = this;
            var results = this._super(category_id, query);
            results = _.filter(results, function (product) {
                return self.products_removed.indexOf(product['id']) == -1
            });
            return results;
        },
        get_product_by_category: function (category_id) {
            var self = this;
            var results = this._super(category_id);
            results = _.filter(results, function (product) {
                return self.products_removed.indexOf(product['id']) == -1
            });
            return results;
        },
        search_partner: function (query) {
            var self = this;
            var results = this._super(query);
            results = _.filter(results, function (partner) {
                return self.partners_removed.indexOf(partner['id']) == -1
            });
            return results;
        },
        get_partners_sorted: function (max_count) {
            // TODO: improved performace to big data partners , default odoo get 1000 rows, but we only allow default render 20 rows
            if (max_count && max_count >= 20) {
                max_count = 20;
            }
            var self = this;
            var results = this._super(max_count);
            results = _.filter(results, function (partner) {
                return self.partners_removed.indexOf(partner['id']) == -1
            });
            return results;
        },
    });
    screens.ProductScreenWidget.include({
        remove_product_out_of_screen: function (product) {
            if (this.pos.session.server_version_info[0] != 10) {
                var current_pricelist = this.product_list_widget._get_active_pricelist();
                var cache_key = this.product_list_widget.calculate_cache_key(product, current_pricelist);
                this.product_list_widget.product_cache.cache[cache_key] = null;
                var contents = document.querySelector(".product-list " + "[data-product-id='" + product['id'] + "']");
                if (contents) {
                    contents.replaceWith()
                }
                this.pos.db.products_removed.push(product.id);
            }
        },
        do_update_products_cache: function (product_datas) {
            var self = this;
            console.warn('do_update_products_cache productos en total: ' + product_datas.length);
            this.pos.db.add_products(_.map(product_datas, function (product) {
                var using_company_currency = self.pos.config.currency_id[0] === self.pos.company.currency_id[0];
                if (self.pos.company_currency) {
                    var conversion_rate = self.pos.currency.rate / self.pos.company_currency.rate;
                } else {
                    var conversion_rate = 1;
                }
                if (!using_company_currency) {
                    product['lst_price'] = round_pr(product.lst_price * conversion_rate, self.pos.currency.rounding);
                }
                if (self.pos.db.stock_datas && self.pos.db.stock_datas[product['id']]) {
                    product['qty_available'] = self.pos.db.stock_datas[product['id']];
                }
                product['categ'] = _.findWhere(self.pos.product_categories, {'id': product['categ_id'][0]});
                product = new export_models.Product({}, product);
                var current_pricelist = self.product_list_widget._get_active_pricelist();
                var cache_key = self.product_list_widget.calculate_cache_key(product, current_pricelist);
                self.product_list_widget.product_cache.cache_node(cache_key, null);
                var product_node = self.product_list_widget.render_product(product);
                product_node.addEventListener('click', self.product_list_widget.click_product_handler);
                var contents = document.querySelector(".product-list " + "[data-product-id='" + product['id'] + "']");
                if (contents) {
                    contents.replaceWith(product_node)
                }
                self.pos.db.products_removed = _.filter(self.pos.db.products_removed, function (product_id) {
                    return product_id != product.id
                });
                return product;
            }));
        },
    });

    screens.ClientListScreenWidget.include({
        do_update_partners_cache: function (partners) {
            var reload_partner = null;
            for (var i = 0; i < partners.length; i++) {
                var partner = partners[i];
                console.warn('do_update_partners_cache: ' + partner.name);
                var clientline_html = QWeb.render('ClientLine', {widget: this, partner: partners[i]});
                clientline = document.createElement('tbody');
                clientline.innerHTML = clientline_html;
                clientline = clientline.childNodes[1];
                this.partner_cache.cache_node(partner.id, clientline);
                if (this.new_client && this.new_client.id == partner.id) {
                    reload_partner = partner;
                }
            }
            this.render_list(this._get_partners());
            if (reload_partner) {
                this.display_client_details('show', partner)
            }
        }
    });

    models.load_models([
        {
            label: 'Recargar Sesión',
            condition: function (self) {
                return self.pos_session.required_reinstall_cache;
            },
            loaded: function (self) {
                return new Promise(function (resolve, reject) {
                    rpc.query({
                        model: 'pos.session',
                        method: 'update_required_reinstall_cache',
                        args: [[self.pos_session.id]]
                    }, {
                        shadow: true,
                        timeout: 65000
                    }).then(function (state) {
                        self.remove_indexed_db();
                        self.reload_pos();
                        resolve(state);
                    }, function (err) {
                        self.remove_indexed_db();
                        self.reload_pos();
                        reject(err)
                    })
                });
            },
        },
    ], {
        after: 'pos.config'
    });

    models.load_models([
        {
            label: 'Productos : Inventario disponible',
            condition: function (self) {
                return self.config.display_onhand;
            },
            loaded: function (self) {
                var location_ids = [];
                if (self.config.multi_location) {
                    location_ids = location_ids.concat(self.config.stock_location_ids)
                }
                if (location_ids.indexOf(self.config.stock_location_id[0]) == -1) {
                    location_ids.push(self.config.stock_location_id[0])
                }
                return self._get_stock_on_hand_by_location_ids([], location_ids).then(function (stock_datas_by_location_id) {
                    self.db.stock_datas = stock_datas_by_location_id[self.config.stock_location_id[0]];
                    self.stock_datas_by_location_id = stock_datas_by_location_id;
                })
            },
            retail: true,
        },
        {
            label: 'Productos',
            installed: true,
            loaded: function (self) {
                return self.indexed_db.get_datas(self, 'product.product', self.session.model_ids['product.product']['max_id'] / 100000 + 1)
            }
        },
        {
            label: 'Instalando Productos',
            condition: function (self) {
                return self.total_products == 0;
            },
            loaded: function (self) {
                return self.api_install_datas('product.product')
            }
        },
        {
            label: 'Clientes',
            installed: true,
            loaded: function (self) {
                return self.indexed_db.get_datas(self, 'res.partner', self.session.model_ids['res.partner']['max_id'] / 100000 + 1)
            }
        },
        {
            label: 'Instalando Clientes',
            condition: function (self) {
                return self.total_clients == 0;
            },
            loaded: function (self) {
                return self.api_install_datas('res.partner')
            }
        },
        {
            label: 'POS Órdenes',
            model: 'pos.order',
            condition: function (self) {
                return self.config.pos_orders_management;
            },
            fields: [
                'create_date',
                'name',
                'date_order',
                'user_id',
                'amount_tax',
                'amount_total',
                'amount_paid',
                'amount_return',
                'pricelist_id',
                'partner_id',
                'sequence_number',
                'session_id',
                'state',
                'account_move',
                'picking_id',
                'picking_type_id',
                'location_id',
                'note',
                'nb_print',
                'pos_reference',
                'sale_journal',
                'fiscal_position_id',
                'ean13',
                'expire_date',
                'is_return',
                'is_returned',
                'voucher_id',
                'email',
                'write_date',
                'config_id',
                'is_paid_full',
                'partial_payment',
                'session_id',
                'shipping_id',
            ],
            domain: function (self) {
                var domain = [['config_id', '=', self.config.id]];
                var today = new Date();
                if (self.config.load_orders_type == 'load_all') {
                    return domain
                }
                if (self.config.load_orders_type == 'last_7_days') {
                    today.setDate(today.getDate() - 7);
                    domain.push(['create_date', '>=', time.date_to_str(today) + " " + time.time_to_str(today)]);
                    return domain;
                }
                if (self.config.load_orders_type == 'last_1_month') {
                    today.setDate(today.getDate() - 30);
                    domain.push(['create_date', '>=', time.date_to_str(today) + " " + time.time_to_str(today)]);
                    return domain;
                }
                if (self.config.load_orders_type == 'last_1_year') {
                    today.setDate(today.getDate() - 365);
                    domain.push(['create_date', '>=', time.date_to_str(today) + " " + time.time_to_str(today)]);
                    return domain;
                }
            },
            loaded: function (self, orders) {
                self.order_ids = [];
                for (var i = 0; i < orders.length; i++) {
                    var order = orders[i];
                    var create_date = field_utils.parse.datetime(order.create_date);
                    order.create_date = field_utils.format.datetime(create_date);
                    var date_order = field_utils.parse.datetime(order.date_order);
                    order.date_order = field_utils.format.datetime(date_order);
                    self.order_ids.push(order.id)
                }
                self.db.save_pos_orders(orders);
            }
        }, {
            label: 'POS Líneas de las Órdenes',
            model: 'pos.order.line',
            fields: [
                'name',
                'notice',
                'product_id',
                'price_unit',
                'qty',
                'price_subtotal',
                'price_subtotal_incl',
                'discount',
                'order_id',
                'plus_point',
                'redeem_point',
                'promotion',
                'promotion_reason',
                'is_return',
                'uom_id',
                'user_id',
                'note',
                'discount_reason',
                'create_uid',
                'write_date',
                'create_date',
                'config_id',
                'variant_ids',
                'returned_qty',
            ],
            domain: function (self) {
                return [['order_id', 'in', self.order_ids]]
            },
            condition: function (self) {
                return self.config.pos_orders_management;
            },
            loaded: function (self, order_lines) {
                self.db.save_pos_order_line(order_lines);
            }
        }, {
            label: 'Órdenes de Ventas',
            model: 'sale.order',
            fields: [
                'create_date',
                'pos_location_id',
                'name',
                'origin',
                'client_order_ref',
                'state',
                'date_order',
                'validity_date',
                'user_id',
                'partner_id',
                'pricelist_id',
                'invoice_ids',
                'partner_shipping_id',
                'payment_term_id',
                'note',
                'amount_tax',
                'amount_total',
                'picking_ids',
                'delivery_address',
                'delivery_date',
                'delivery_phone',
                'book_order',
                'payment_partial_amount',
                'payment_partial_method_id',
                'write_date',
                'ean13',
                'pos_order_id',
            ],
            domain: function (self) {
                var domain = [
                    '|',
                    ['pos_location_id', '=', self.config.stock_location_id[0]],
                    ['pos_location_id', '=', null],
                    // ['state', 'not in', ['done', 'cancel', 'booked']] // TODO: no need domain state, we need load all for cache write date (write date fro pos automatic sync with backend)
                ];
                var today = new Date();
                if (self.config.load_booked_orders_type == 'load_all') {
                    return domain
                }
                if (self.config.load_booked_orders_type == 'last_7_days') {
                    today.setDate(today.getDate() - 7);
                    domain.push(['create_date', '>=', time.date_to_str(today) + " " + time.time_to_str(today)]);
                    return domain;
                }
                if (self.config.load_booked_orders_type == 'last_1_month') {
                    today.setDate(today.getDate() - 30);
                    domain.push(['create_date', '>=', time.date_to_str(today) + " " + time.time_to_str(today)]);
                    return domain;
                }
                if (self.config.load_booked_orders_type == 'last_1_year') {
                    today.setDate(today.getDate() - 365);
                    domain.push(['create_date', '>=', time.date_to_str(today) + " " + time.time_to_str(today)]);
                    return domain;
                }
            },
            condition: function (self) {
                return self.config.booking_orders;
            },
            context: {'pos': true},
            loaded: function (self, orders) {
                self.booking_ids = [];
                for (var i = 0; i < orders.length; i++) {
                    self.booking_ids.push(orders[i].id)
                }
                self.db.save_sale_orders(orders);
            }
        }, {
            model: 'sale.order.line',
            fields: [
                'name',
                'discount',
                'product_id',
                'order_id',
                'price_unit',
                'price_subtotal',
                'price_tax',
                'price_total',
                'product_uom',
                'product_uom_qty',
                'qty_delivered',
                'qty_invoiced',
                'tax_id',
                'variant_ids',
                'state',
                'write_date'
            ],
            domain: function (self) {
                return [['order_id', 'in', self.booking_ids]]
            },
            condition: function (self) {
                return self.config.booking_orders;
            },
            context: {'pos': true},
            loaded: function (self, order_lines) {
                self.order_lines = order_lines;
                self.db.save_sale_order_lines(order_lines);
            }
        },
        {
            model: 'account.move',
            condition: function (self) {
                return self.config.management_invoice;
            },
            fields: [
                'create_date',
                'name',
                'date',
                'ref',
                'state',
                'type',
                'journal_id',
                'partner_id',
                'amount_tax',
                'amount_total',
                'amount_untaxed',
                'amount_residual',
                'invoice_user_id',
                'invoice_payment_state',
                'invoice_date',
                'invoice_date_due',
                'invoice_payment_term_id',
                'stock_move_id',
                'write_date',
                'currency_id',
            ],
            domain: function (self) {
                var domain = [['company_id', '=', self.company.id]];
                var today = new Date();
                if (self.config.load_invoices_type == 'load_all') {
                    return domain
                }
                if (self.config.load_invoices_type == 'last_7_days') {
                    today.setDate(today.getDate() - 7);
                    domain.push(['create_date', '>=', time.date_to_str(today) + " " + time.time_to_str(today)]);
                    return domain;
                }
                if (self.config.load_invoices_type == 'last_1_month') {
                    today.setDate(today.getDate() - 30);
                    domain.push(['create_date', '>=', time.date_to_str(today) + " " + time.time_to_str(today)]);
                    return domain;
                }
                if (self.config.load_invoices_type == 'last_1_year') {
                    today.setDate(today.getDate() - 365);
                    domain.push(['create_date', '>=', time.date_to_str(today) + " " + time.time_to_str(today)]);
                    return domain;
                }
            },
            context: {'pos': true},
            loaded: function (self, invoices) {
                self.invoice_ids = [];
                for (var i = 0; i < invoices.length; i++) {
                    self.invoice_ids.push(invoices[i]['id']);
                }
                self.db.save_invoices(invoices);
            },
            retail: true,
        },
        {
            model: 'account.move.line',
            condition: function (self) {
                return self.config.management_invoice;
            },
            fields: [
                'move_id',
                'move_name',
                'date',
                'ref',
                'journal_id',
                'account_id',
                'sequence',
                'name',
                'quantity',
                'price_unit',
                'discount',
                'debit',
                'credit',
                'balance',
                'price_subtotal',
                'price_total',
                'write_date'
            ],
            domain: function (self) {
                return [['move_id', 'in', self.invoice_ids]]
            },
            context: {'pos': true},
            loaded: function (self, invoice_lines) {
                self.db.save_invoice_lines(invoice_lines);
            },
            retail: true,
        },
    ]);

    var _super_Order = models.Order.prototype;
    models.Order = models.Order.extend({
        set_client: function (client) {
            if (client && client['id'] && this.pos.deleted['res.partner'] && this.pos.deleted['res.partner'].indexOf(client['id']) != -1) {
                client = null;
                return this.pos.gui.show_popup('confirm', {
                    title: _t('Advertencia'),
                    body: _t('Este cliente ha sido borrado del sistema')
                })
            }
            _super_Order.set_client.apply(this, arguments);
        },
    });
});
