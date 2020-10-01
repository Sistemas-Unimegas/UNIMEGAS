# -*- coding: utf-8 -*-

from odoo import models,fields,api,exceptions,SUPERUSER_ID,_
from odoo.exceptions import UserError
import datetime
from datetime import timedelta
import pytz
import time
from . import const
from .base import ZK

from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

import logging
_logger = logging.getLogger(__name__)

class zkMachineLocation(models.Model):
    _name= 'zk.machine.location'
    name = fields.Char("Location",required=True)


class zkMachine(models.Model):
    _name= 'zk.machine'
    
    name =  fields.Char("Machine IP")
    state =  fields.Selection([('draft','Draft'),('done','Done')], 'State', default='draft')
    location_id =  fields.Many2one('zk.machine.location', string="Location")
    port =  fields.Integer("Port Number")
    employee_ids = fields.Many2many("hr.employee", 'zk_machine_employee_rel', 'employee_id', 'machine_id',string='Employees', readonly=True, copy=False, required=False)
    
    
    def try_connection(self):
        for r in self:
            machine_ip = r.name
            port = r.port
            zk = ZK(machine_ip, port=port, timeout=50, password=0, force_udp=False, ommit_ping=False)
            conn = ''
            try:
                conn = zk.connect()
                users = conn.get_users()
            except Exception as e:
                raise UserError('The connection has not been achieved: %s' % (e)) 
            finally:
                if conn:
                    conn.disconnect()
                    raise UserError(_('Successful connection:  "%s".') %
                            (users))
                    
    
    def restart(self):
        for r in self:
            machine_ip = r.name
            port = r.port
            zk = ZK(machine_ip, port=port, timeout=5, password=0, force_udp=False, ommit_ping=False)
            conn = ''
            try:
                conn = zk.connect()
                conn.restart()
            except Exception as e:
                raise UserError('The connection has not been achieved: %s' % (e))
            finally:
                raise UserError('Successful')
                    
    
    def synchronize(self):
        for r in self:
            employee  = self.env['hr.employee']
            employee_location_line=self.env['zk.employee.location.line']
            employee_list = []
            machine_ip = r.name
            port = r.port
            zk = ZK(machine_ip, port=port, timeout=5, password=0, force_udp=False, ommit_ping=False)
            conn = ''
            try:
                conn = zk.connect()
                conn.disable_device()
                users = conn.get_users()
                for user in users:
                    employee_id=employee.search([('zknumber','=',user.user_id)])
                    if len(employee_id) > 1:
                        raise UserError('There is more than one employee with the same son-in-law zk')
                    if employee_id:
                        employee_list.append(employee_id)
                        if employee_id not in r.employee_ids:
                            r.employee_ids += employee_id
                            employee_location_line.create({'employee_id':employee_id.id,
                                                           'zk_num':employee_id.zknumber,
                                                           'machine_id':r.id,
                                                           'uid':user.uid,
                                                           'location_id':r.location_id.id})
                for emp in employee_list:
                    employee+=emp
                employees_unlink = r.employee_ids - employee
                for emp1 in employees_unlink:
                    employee_location_line_id = employee_location_line.search([('employee_id','=',emp1.id),('machine_id','=',r.id)])
                    employee_location_line_id.unlink()
                r.employee_ids = employee
            except Exception as e:
                raise UserError('The connection has not been achieved: %s' % (e))
            finally:
                if conn:
                    conn.disconnect()
                    
    
    def clear_attendance(self):
        for r in self:
            machine_ip = r.name
            port = r.port
            zk = ZK(machine_ip, port=port, timeout=5, password=0, force_udp=False, ommit_ping=False)
            conn = ''
            try:
                conn = zk.connect()
                conn.disable_device()
                conn.clear_attendance()
            except Exception as e:
                raise UserError('The connection has not been achieved: %s' % (e))
            finally:
                if conn:
                    conn.enable_device()
                    conn.disconnect()
    
    def download_attendance2(self):
        users  = self.env['res.users']
        attendance_obj =  self.env["hr.attendance"]
        employee_location_line_obj = self.env["zk.employee.location.line"]
        user = self.env.user
        if not user.partner_id.tz:
            raise exceptions.ValidationError("Timezone is not defined on this %s user." % user.name)
        tz = pytz.timezone(user.partner_id.tz) or False
        for machine in self:
            machine_ip = machine.name
            port = machine.port
            zk = ZK(machine_ip, port=port, timeout=50, password=0, force_udp=False, ommit_ping=False)
            conn = ''
            try:
                conn = zk.connect()
                attendances = conn.get_attendance()
            except Exception as e:
                print (e)
                raise UserError('The connection has not been achieved: %s' % (e))
            finally:
                if conn:
                    conn.disconnect()
                    raise UserError(_('Successful connection:  "%s".') %
                            (attendances))
    
    
    def download_attendance(self):
        users  = self.env['res.users']
        attendance_obj =  self.env["hr.attendance"]
        employee_location_line_obj = self.env["zk.employee.location.line"]
        user = self.env.user
        if not user.partner_id.tz:
            raise exceptions.ValidationError("Timezone is not defined on this %s user." % user.name)
        tz = pytz.timezone(user.partner_id.tz) or False
        for machine in self:
            machine_ip = machine.name
            port = machine.port
            zk = ZK(machine_ip, port=port, timeout=10, password=0, force_udp=False, ommit_ping=False)
            conn = ''
            try:
                conn = zk.connect()
                conn.disable_device()
                attendances = conn.get_attendance()
                for attendance in attendances:
                    employee_location_line = employee_location_line_obj.search([("zk_num", "=", int(attendance.user_id)),('location_id','=',machine.location_id.id),('machine_id','=',machine.id)])
                    if employee_location_line:
                        employee_id = employee_location_line.employee_id
                        date = attendance.timestamp
                        date1 =datetime.datetime.strptime(str(date), DEFAULT_SERVER_DATETIME_FORMAT)
                        date = tz.normalize(tz.localize(date1)).astimezone(pytz.utc).strftime ("%Y-%m-%d %H:%M:%S")
                        if attendance.punch == 0:
                            attendance_id = attendance_obj.search([('employee_id','=',employee_id.id),('check_in','=',str(date))])
                            if not attendance_id:
                                attendance_obj.create({'check_in':date,'employee_id':employee_id.id})
                        if attendance.punch == 1:
                            attendance_id = attendance_obj.search([('employee_id','=',employee_id.id),('check_out','=',str(date))])
                            if not attendance_id:
                                attendance_ids = attendance_obj.search([('employee_id','=',employee_id.id),('check_in','<',str(date)),('check_out','=',False)],order='check_in desc',limit=1)
                                attendance_last = attendance_obj.search([('employee_id','=',employee_id.id),('check_in','!=',False)],order='check_in desc',limit=1)
                                if (attendance_last.check_in and attendance_ids.check_in and attendance_ids.check_in >= attendance_last.check_in) or not attendance_last.check_in or not attendance_ids.check_in:
                                    if attendance_ids:
                                        attendance_ids.write({'check_out':date})
                                    else:
                                        attendance_obj.create({'check_out':date,'employee_id':employee_id.id})
                                else:
                                    attendance_obj.create({'check_out':date,'employee_id':employee_id.id})
            except Exception as e:
                raise UserError('The connection has not been achieved: %s' % (e))
            finally:
                if conn:
                    conn.enable_device()
                    conn.disconnect()
            
                    
                
class HrAttendance(models.Model):
    _inherit = "hr.attendance"
    
    check_in = fields.Datetime(string="Check In", default='', required=False)
    
    
    def name_get(self):
        result = []
        for attendance in self:
            if not attendance.check_out:
                result.append((attendance.id, _("%(empl_name)s from %(check_in)s") % {
                    'empl_name': attendance.employee_id.name,
                    'check_in': fields.Datetime.to_string(fields.Datetime.context_timestamp(attendance, fields.Datetime.from_string(attendance.check_in))),
                }))
            else:
                if attendance.check_in:
                    result.append((attendance.id, _("%(empl_name)s from %(check_in)s to %(check_out)s") % {
                        'empl_name': attendance.employee_id.name,
                        'check_in': fields.Datetime.to_string(fields.Datetime.context_timestamp(attendance, fields.Datetime.from_string(attendance.check_in))),
                        'check_out': fields.Datetime.to_string(fields.Datetime.context_timestamp(attendance, fields.Datetime.from_string(attendance.check_out))),
                    }))
                else:
                    result.append((attendance.id, _("%(empl_name)s from %(check_in)s to %(check_out)s") % {
                        'empl_name': attendance.employee_id.name,
                        'check_in': 'Undefined',
                        'check_out': fields.Datetime.to_string(fields.Datetime.context_timestamp(attendance, fields.Datetime.from_string(attendance.check_out))),
                    }))
        return result
    
    
    @api.depends('check_in', 'check_out')
    def _compute_worked_hours(self):
        for attendance in self:
            if attendance.check_in and attendance.check_out:
                delta = attendance.check_out - attendance.check_in
                attendance.worked_hours = delta.total_seconds() / 3600.0
    
    @api.constrains('check_in', 'check_out', 'employee_id')
    def _check_validity(self):
        """ Verifies the validity of the attendance record compared to the others from the same employee.
            For the same employee we must have :
                * maximum 1 "open" attendance record (without check_out)
                * no overlapping time slices with previous employee records
        """
        for attendance in self:
            # we take the latest attendance before our check_in time and check it doesn't overlap with ours
            last_attendance_before_check_in = self.env['hr.attendance'].search([
                ('employee_id', '=', attendance.employee_id.id),
                ('check_in', '<=', attendance.check_in),
                ('id', '!=', attendance.id),
            ], order='check_in desc', limit=1)
            if last_attendance_before_check_in and last_attendance_before_check_in.check_out and last_attendance_before_check_in.check_out > attendance.check_in:
                raise exceptions.ValidationError(_("Cannot create new attendance record for %(empl_name)s, the employee was already checked in on %(datetime)s") % {
                    'empl_name': attendance.employee_id.name,
                    'datetime': fields.Datetime.to_string(fields.Datetime.context_timestamp(self, fields.Datetime.from_string(attendance.check_in))),
                })

            if not attendance.check_out:
                # if our attendance is "open" (no check_out), we verify there is no other "open" attendance
                no_check_out_attendances = self.env['hr.attendance'].search([
                    ('employee_id', '=', attendance.employee_id.id),
                    ('check_out', '=', False),
                    ('id', '!=', attendance.id),
                ])
                # ~ if no_check_out_attendances:
                    # ~ raise exceptions.ValidationError(_("Cannot create new attendance record for %(empl_name)s, the employee hasn't checked out since %(datetime)s") % {
                        # ~ 'empl_name': attendance.employee_id.name_related,
                        # ~ 'datetime': fields.Datetime.to_string(fields.Datetime.context_timestamp(self, fields.Datetime.from_string(no_check_out_attendances.check_in))),
                    # ~ })
            # ~ else:
                # ~ # we verify that the latest attendance with check_in time before our check_out time
                # ~ # is the same as the one before our check_in time computed before, otherwise it overlaps
                # ~ last_attendance_before_check_out = self.env['hr.attendance'].search([
                    # ~ ('employee_id', '=', attendance.employee_id.id),
                    # ~ ('check_in', '<', attendance.check_out),
                    # ~ ('id', '!=', attendance.id),
                # ~ ], order='check_in desc', limit=1)
                # ~ if last_attendance_before_check_out and last_attendance_before_check_in != last_attendance_before_check_out:
                    # ~ raise exceptions.ValidationError(_("Cannot create new attendance record for %(empl_name)s, the employee was already checked in on %(datetime)s") % {
                        # ~ 'empl_name': attendance.employee_id.name,
                        # ~ 'datetime': fields.Datetime.to_string(fields.Datetime.context_timestamp(self, fields.Datetime.from_string(last_attendance_before_check_out.check_in))),
                    # ~ })                     



class hrEmployee(models.Model):
    _inherit = 'hr.employee'
    
    zk_location_line_ids = fields.One2many('zk.employee.location.line','employee_id',string='Locations')
    zknumber =  fields.Char("Number zk")
    
    def delete_employee_zk(self):
        machine_id = self.env['zk.machine'].search([('id','=',int(self.env.context.get('machine_id')))])
        machine_ip = machine_id.name
        port = machine_id.port
        zk = ZK(machine_ip, port=port, timeout=10, password=0, force_udp=False, ommit_ping=False)
        conn = ''
        try:
            conn = zk.connect()
            conn.disable_device()
            employee_location_line = self.env['zk.employee.location.line'].search([('employee_id','=',self.id),('machine_id','=',machine_id.id)])
            conn.delete_user(uid=employee_location_line.uid)
            machine_id.employee_ids = machine_id.employee_ids - self
            employee_location_line.unlink()
        except Exception as e:
            raise UserError('Unable to complete user registration')
        finally:
            if conn != '':
                conn.enable_device()
                conn.disconnect()
        return True
    
    def disassociate_employee_zk(self):
        machine_id = self.env['zk.machine'].search([('id','=',int(self.env.context.get('machine_id')))])
        employee_location_line = self.env['zk.employee.location.line'].search([('employee_id','=',self.id),('machine_id','=',machine_id.id)])
        machine_id.employee_ids = machine_id.employee_ids - self
        employee_location_line.unlink()
        return True


class hrZkEmployeeLocationLine(models.Model):
    _name = 'zk.employee.location.line'

    employee_id = fields.Many2one('hr.employee',string="Employee")
    zk_num = fields.Integer(string="ZKSoftware Number", help="ZK Attendance User Code",required=True)
    machine_id = fields.Many2one('zk.machine',string="Machine",required=True)
    location_id =  fields.Many2one('zk.machine.location',related='machine_id.location_id', string="Location")
    uid =  fields.Integer('Uid')
    
    _sql_constraints = [('unique_location_emp', 'unique(employee_id,location_id)', 'There is a record of this employee for this location.')]
    
