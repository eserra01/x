# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

class PabsEleanorMove(models.Model):
    _name = 'pabs.eleanor.move'
    _description = 'Movimientos' 

    def get_period(self, period_type=False):  
        if not period_type:
            period_type = self.env.context.get('period_type')         
        period_id = self.env['pabs.eleanor.period'].search([('state','=','open'),('period_type','=',period_type)],limit=1)
        return period_id
        
    period_id = fields.Many2one(comodel_name="pabs.eleanor.period", string="Periodo", required=True, default=get_period)
    move_type = fields.Selection([('perception','Percepcion'),('deduction','Deducción')], string="Tipo movimiento", required=True)
    concept_id = fields.Many2one(comodel_name="pabs.eleanor.concept", string="Concepto", required=True, domain="[('id', '=', 0)]") ### No mostrar lista de conceptos si no se ha elegido un tipo
    employee_id = fields.Many2one(comodel_name="hr.employee", string="Empleado", required=True)
    area_id = fields.Many2one(comodel_name="pabs.eleanor.area", string="Área", required=True)
    warehouse_id = fields.Many2one(comodel_name="stock.warehouse", string="Oficina")
    department_id = fields.Many2one(comodel_name="hr.department", string="Departamento")
    job_id = fields.Many2one(comodel_name="hr.job", string="Puesto", required=True )
    amount = fields.Float(string="Importe")
    company_id = fields.Many2one(comodel_name="res.company",string="Compañia",default=lambda self: self.env.company, copy=True, required=True,) 

    concept_type = fields.Selection([('perception','Percepcion'),('deduction','Deducción')], string="Tipo concepto", related='concept_id.concept_type')
    concept_allow_load = fields.Boolean(string="Permitir carga", related="concept_id.allow_load")

    state = fields.Selection([('open','Abierto'),('close','Cerrado')], string="Estatus", related='period_id.state')
    period_type = fields.Selection([('weekly','Semanal'),('biweekly','Quincenal')], string="Tipo periodo", related='period_id.period_type')
    week_number = fields.Integer(string="Número de periodo", related='period_id.week_number')
    date_start = fields.Date(string="Fecha inicio", related='period_id.date_start')

    # 
    @api.model
    def create(self,values):
        # 
        res = super(PabsEleanorMove,self).create(values)

        ### No generar bitácora en la migracion
        if self.env.context.get('migration'):
            return res
        
        if self.env.context.get('masive'):
            values.update({'action_type':'create','mode':'masive','user_id': self.env.user.id})
        else:
            values.update({'action_type':'create','mode':'form','user_id': self.env.user.id})
            
        self.env['pabs.eleanor.move.binnacle'].create(values)
        return res
    #   
    def write(self,values):
        # 
        res = super(PabsEleanorMove,self).write(values)
        #        
        vals = {
            'period_id': self.period_id.id,
            'move_type': self.move_type,
            'concept_id': self.concept_id.id,
            'employee_id': self.employee_id.id,
            'area_id': self.area_id.id,
            'warehouse_id': self.warehouse_id.id,
            'department_id': self.department_id.id,
            'job_id': self.job_id.id,
            'amount': self.amount,
            'action_type': 'edit',
            'mode':'form',
            'user_id': self.env.user.id

        }
        for key,value in values.items():            
            dic = eval("{" + "'{}':'{}'".format(str(key),str(value)) + "}")            
            vals.update(dic)
        self.env['pabs.eleanor.move.binnacle'].create(vals)
        return res
    
    #    
    def unlink(self):
        for rec in self:
            if not self.env.context.get('byfile'):                
                vals = {
                    'period_id': rec.period_id.id,
                    'move_type': rec.move_type,
                    'concept_id': rec.concept_id.id,
                    'employee_id': rec.employee_id.id,
                    'area_id': rec.area_id.id,
                    'warehouse_id': rec.warehouse_id.id,
                    'department_id': rec.department_id.id,
                    'job_id': rec.job_id.id,
                    'amount': rec.amount,
                    'action_type': 'delete',
                    'mode':'form',
                    'user_id': self.env.user.id
                }       
                self.env['pabs.eleanor.move.binnacle'].create(vals)
        #
        res = super(PabsEleanorMove,self).unlink()        
        return res

    @api.constrains('concept_id')
    def _check_concept(self):       
        for record in self:  
            move_id = self.search(
                [
                    ('id','!=',record.id),
                    ('period_id','=',record.period_id.id),
                    ('concept_id','=',record.concept_id.id),
                    ('employee_id','=',record.employee_id.id),
                    ('company_id','=',self.env.company.id)
                ])
            if move_id:
                raise ValidationError("Ya existe un registro con el periodo,concepto y empleado seleccionados")
   
    @api.onchange('move_type')
    def _onchange_move_type(self):
        for rec in self:
            if rec.move_type:
                self.concept_id = None

                ids = []
                for concept_id in self.env['pabs.eleanor.concept'].search([('concept_type','=',rec.move_type), ('allow_load', '=', True)]):                    
                    if concept_id.id not in ids:
                        ids.append(concept_id.id)
              
                return {
                    'domain':
                    {
                        'concept_id': [('id','in',ids)],                                           
                    }
                } 
    
    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        for rec in self:
            if rec.employee_id:

                ### Verificar que el empleado pertenezca al tipo de periodo
                tipo_periodo = self.env.context.get('period_type')

                if rec.employee_id.period_type != tipo_periodo:
                    raise ValidationError("El empleado no pertenece a este tipo de periodo")

                ### Verificar acceso al empleado
                ids_departamentos = []
                ids_oficinas = []
                all_employees_allowed = self.env.user.all_employees

                if not all_employees_allowed:
                    accesos = self.env['pabs.eleanor.user.access'].search([
                        ('company_id', '=', self.env.company.id),
                        ('user_id', '=', self.env.user.id)
                    ])

                    ids_departamentos = accesos.mapped('department_id').ids
                    ids_oficinas = accesos.mapped('warehouse_id').ids

                    access_id = False
                    lugar = ""
                    if rec.employee_id.warehouse_id:
                        if rec.employee_id.warehouse_id.id in ids_oficinas:
                            access_id = True
                        else:
                            lugar = "a la oficina {}".format(rec.employee_id.warehouse_id.name)
                    elif rec.employee_id.department_id:
                        if rec.employee_id.department_id.id in ids_departamentos:
                            access_id = True
                        else:
                            lugar = "al departamento {}".format(rec.employee_id.department_id.name)
                        
                    if not access_id:
                        raise ValidationError("No puedes crear movimientos para el empleado {}-{} porque no tienes acceso {}".format(rec.employee_id.barcode, rec.employee_id.name, lugar))

                ### Calcular datos del empleado
                rec.area_id = rec.employee_id.pabs_eleanor_area_id.id
                rec.warehouse_id = rec.employee_id.warehouse_id.id
                rec.department_id = rec.employee_id.department_id.id
                rec.job_id = rec.employee_id.job_id.id
                

    def show_weekly_movs(self):
        ### Obtener permisos de acceso del usuario ###
        ids_departamentos = []
        ids_oficinas = []
        all_employees_allowed = self.env.user.all_employees

        domain = []
        if all_employees_allowed:
            domain = [
                ('company_id', '=', self.env.company.id),
                ('period_type','=','weekly'),
                ('state','=','open'),
                ('concept_allow_load','=',True)
            ]
        else:
            accesos = self.env['pabs.eleanor.user.access'].search([
                ('company_id', '=', self.env.company.id),
                ('user_id', '=', self.env.user.id)
            ])

            ids_departamentos = accesos.mapped('department_id').ids
            ids_oficinas = accesos.mapped('warehouse_id').ids

            domain = [
                ('company_id', '=', self.env.company.id),
                ('period_type','=','weekly'),
                ('state','=','open'),
                ('concept_allow_load','=',True),
                '|', ('employee_id.department_id.id', 'in', ids_departamentos),
                ('employee_id.warehouse_id.id', 'in', ids_oficinas)
            ]

        name = "Movimientos semanales"
        period_id = self.get_period('weekly')
        if period_id:
            name = "Tipo: semanal, semana {}, periodo del {} al {}".format(period_id.week_number, str(period_id.date_start), str(period_id.date_end))
        return {
            'type': 'ir.actions.act_window',
            'name': name,        
            'res_model': 'pabs.eleanor.move',
            'view_type': 'form',
            'view_mode': 'tree',
            'view_id'      : self.env.ref('pabs_eleanor.pabs_eleanor_weekly_move_tree_view').id,
            'target': 'main',
            'context': {'period_type': 'weekly'},
            'domain': domain
        }  

    def show_biweekly_movs(self):
        ### Obtener permisos de acceso del usuario ###
        ids_departamentos = []
        ids_oficinas = []
        all_employees_allowed = self.env.user.all_employees

        domain = []
        if all_employees_allowed:
            domain = [
                ('company_id', '=', self.env.company.id),
                ('period_type','=','biweekly'),
                ('state','=','open'),
                ('concept_allow_load','=',True)
            ]
        else:
            accesos = self.env['pabs.eleanor.user.access'].search([
                ('company_id', '=', self.env.company.id),
                ('user_id', '=', self.env.user.id)
            ])

            ids_departamentos = accesos.mapped('department_id').ids
            ids_oficinas = accesos.mapped('warehouse_id').ids

            domain = [
                ('company_id', '=', self.env.company.id),
                ('period_type','=','biweekly'),
                ('state','=','open'),
                ('concept_allow_load','=',True),
                '|', ('employee_id.department_id.id', 'in', ids_departamentos),
                ('employee_id.warehouse_id.id', 'in', ids_oficinas)
            ]

        name = "Movimientos quincenales"
        period_id = self.get_period('biweekly')
        if period_id:
            name = "Tipo: Quincenal, semana {}, periodo del {} al {}".format(period_id.week_number, str(period_id.date_start), str(period_id.date_end))
        return {
            'type': 'ir.actions.act_window',
            'name': name,        
            'res_model': 'pabs.eleanor.move',
            'view_type': 'form',
            'view_mode': 'tree',
            'view_id'      : self.env.ref('pabs_eleanor.pabs_eleanor_biweekly_move_tree_view').id,
            'target': 'main',
            'context': {'period_type': 'biweekly'},
            'domain': domain
        }

    def show_all_movs(self):       
        return {
            'type': 'ir.actions.act_window',
            'name': "Movimientos (todos)",        
            'res_model': 'pabs.eleanor.move',
            'view_type': 'form',
            'view_mode': 'tree', 
            'view_id'      : self.env.ref('pabs_eleanor.pabs_eleanor_all_move_tree_view').id,         
            'target': 'main',
            'context': {'period_type': 'all'},
            'domain': "[]"
        }
    
    def show_comissions_movs(self):
        ### Obtener permisos de acceso del usuario ###
        domain = [
            ('company_id', '=', self.env.company.id),
            ('period_type','=','weekly'),
            ('state','=','open'),
            ('concept_allow_load','=',False)
        ]

        name = "Movimientos semanales"
        period_id = self.get_period('weekly')
        if period_id:
            name = "Comisiones semana {}, periodo del {} al {}".format(period_id.week_number, str(period_id.date_start), str(period_id.date_end))
        return {
            'type': 'ir.actions.act_window',
            'name': name,        
            'res_model': 'pabs.eleanor.move',
            'view_type': 'form',
            'view_mode': 'tree',
            'view_id'      : self.env.ref('pabs_eleanor.pabs_eleanor_comissions_move_tree_view').id,
            'target': 'main',
            'context': {'period_type': 'weekly'},
            'domain': domain
        }