import xmlrpclib
import time
import logging

__logger = logging.getLogger(__name__)

start_time = time.time()

database = '13_retail'
login = 'admin'
password = 'admin'
url = 'http://localhost:8069'

common = xmlrpclib.ServerProxy('{}/xmlrpc/2/common'.format(url))
uid = common.authenticate(database, login, password, {})

models = xmlrpclib.ServerProxy(url + '/xmlrpc/object')

for i in range(0, 100):
    vals = {
        'street': u'255 Bui Huu Nghia, Tan Van',
        'city': u'Bien Hoa',
        'name': 'Turbo_customer_%s' % str(i),
        'zip': u'False',
        'mobile': u'0909888888',
        'country_id': 233,
        'email': u'customer_big_data@gmail.com',
    }
    partner_id = models.execute_kw(database, uid, password, 'res.partner', 'create', [vals])
    print i


