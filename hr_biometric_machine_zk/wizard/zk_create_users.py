# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

from odoo.addons.hr_biometric_machine_zk.models import const
from odoo.addons.hr_biometric_machine_zk.models.base import ZK

class zkCreateUser(models.TransientModel):
    _name = "zk.create.user"
    _description = "Create user in machine Zk"
    
    def _default_machine(self):
        machine=self.env['zk.machine'].search([('id','in',self.env.context.get('active_ids', []))])
        return machine
    
    machine_id = fields.Many2one("zk.machine", string='Machine', default=_default_machine, readonly=False, copy=False, required=True)
    employee_ids = fields.Many2many("hr.employee", string='Employees', readonly=False, copy=False, required=True)
    type =  fields.Selection([('USER_DEFAULT','USER_DEFAULT'),('USER_ADMIN','USER_ADMIN')], 'Type', default='USER_DEFAULT', required=True)
                
    
        
    @api.onchange('machine_id')
    def onchange_machine_id_warning(self):
        employees = self.env.context.get('employees_ids')
        if len(employees):
            employees = employees[0][2]
            
        domain = {'employee_ids': [('id', 'not in', employees)]}
        return {'domain': domain}
        
    def create_users_zk(self):
        machine_ip = self.machine_id.name
        port = self.machine_id.port
        zk = ZK(machine_ip, port=port, timeout=10, password=0, force_udp=False, ommit_ping=False)
        conn = ''
        employee_location_line=self.env['zk.employee.location.line']
        for employee in self.employee_ids:
            if not employee.zknumber:
                raise UserError('Number zk no defined in employee %s' % (employee.name))
        try:
            conn = zk.connect()
            conn.disable_device()
            users = conn.get_users()
            list_users=[]
            uid_numbers = 0
            for user in users:
                list_users.append(user.user_id)
                if uid_numbers<user.uid:
                    uid_numbers=user.uid
            for employee in self.employee_ids:
                if not employee.zknumber in list_users:
                    uid_numbers += 1
                    conn.set_user(uid=uid_numbers, 
                                  name=employee.name,
                                  privilege=self.type, 
                                  password=employee.zknumber, 
                                  group_id='', 
                                  user_id=employee.zknumber, 
                                  card=0)
                    employee_location_line.create({'employee_id':employee.id,
                                                   'zk_num':employee.zknumber,
                                                   'machine_id':self.machine_id.id,
                                                   'uid':uid_numbers,
                                                   'location_id':self.machine_id.location_id.id})
                    self.machine_id.employee_ids += employee
                else:
                    for u in users:
                        if employee.zknumber == u.user_id:
                            employee_location_line.create({'employee_id':employee.id,
                                                   'zk_num':employee.zknumber,
                                                   'machine_id':self.machine_id.id,
                                                   'uid':u.uid,
                                                   'location_id':self.machine_id.location_id.id})
                            self.machine_id.employee_ids += employee
        except Exception as e:
            raise UserError('Unable to complete user registration %s' % (e))
        finally:
            if conn != '':
                conn.enable_device()
                conn.disconnect()
        return True
        
    
    
        
