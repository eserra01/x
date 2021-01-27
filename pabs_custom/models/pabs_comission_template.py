# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError

class ComissionTemplate(models.Model):
    """Modelo que contiene las plantillas de árbol de comisión de los asistentes"""
    _name = "pabs.comission.template"
    _description = "Plantilla de árboles de comision"

    #Al eliminar el empleado se eliminan sus plantillas de comisiones
    employee_id = fields.Many2one(string="Asistente", comodel_name="hr.employee", required=True, readonly=True, ondelete="cascade")

    plan_id = fields.Many2one(string="Plan", comodel_name="product.pricelist.item", required=True, readonly=True)

    pay_order = fields.Integer(string="Prioridad", required = True, readonly=True)

    job_id = fields.Many2one(string="Cargo", comodel_name="hr.job", required=True, tracking=True, readonly=True)

    comission_agent_id = fields.Many2one(string="Comisionista", comodel_name="hr.employee", tracking=True)

    comission_amount = fields.Float(string="Monto", default = 0, tracking=True)

    start_date = fields.Date(string="Fecha de inicio", default=fields.Date.today(), tracking=True)

    ### 100%: No permitir registrar dos cargos en el mismo árbol de comisión (la llave se compone de id_empleado, id_plan, id_cargo)
    _sql_constraints = [
        ('unique_comission_entry',
        'UNIQUE(employee_id,plan_id,job_id)',
        'No se puede crear el registro: ya existe una fila con los mismos datos -> [empleado, plan, cargo]')
    ]

    ### 100%: Al crear el empleado se crean los registros en este modelo automáticamente. ver modelo de empleado
    # Para cada plan se crean los siguientes registros: 1 Papeleria, 2 Recomendado, 3 Asistente, 4 Coordinador, 5 Gerente, 6 Fideicomiso
    # Construye el diccionario para insertar un arbol por cada plan
    # {'employee_id' : A, 'plan_id' : B, 'pay_order' : C, 'job_id' : D, 'comission_agent_id' : E, 'comission_amount' : F}
    def build_comission_dictionary(self, myEmployee_id):

        comission_list = []

        #Obtener los registros que están activos en la tabla plantilla de plantillas
        template = self.env['pabs.comission.template.of.templates'].search([('active','=',True)])

        for row in template:
            #Obtener el nombre del cargo
            job_name = self.env['hr.job'].search([('id', '=', row['job_id'].id)]).name

            if job_name == "Papeleria":
                #Obtener el monto de papeleria
                stationery = self.env['product.pricelist.item'].search([('id', '=', row['plan_id'].id)]).stationery
                #Obtener el id del empleado asignado como "Papeleria"
                employee_id = self.env['hr.employee'].search([('job_id', '=', row['job_id'].id)], limit = 1).id

                new_comission = {'employee_id' : myEmployee_id, 'plan_id' : row['plan_id'].id, 'pay_order' : row['pay_order'], 'job_id' : row['job_id'].id, 'comission_agent_id' : employee_id, 'comission_amount' : stationery}
                comission_list.append(new_comission)

            elif job_name == "Fideicomiso":
                #Calcular el monto del fideicomiso = costo - papeleria
                pricelist = self.env['product.pricelist.item'].search([('id', '=', row['plan_id'].id)])
                stationery = pricelist.stationery
                fixed_price = pricelist.fixed_price
                comission_amount = fixed_price - stationery

                #Obtener el id del empleado asignado como "Papeleria"
                employee_id = self.env['hr.employee'].search([('job_id', '=', row['job_id'].id)], limit = 1).id

                new_comission = {'employee_id' : myEmployee_id, 'plan_id' : row['plan_id'].id, 'pay_order' : row['pay_order'], 'job_id' : row['job_id'].id, 'comission_agent_id' : employee_id, 'comission_amount' : comission_amount}
                comission_list.append(new_comission)

            elif job_name == "Asistente Social":
                #Asignar por defecto el asistente con comisión 0
                new_comission = {'employee_id' : myEmployee_id, 'plan_id' : row['plan_id'].id, 'pay_order' : row['pay_order'], 'job_id' : row['job_id'].id, 'comission_agent_id' : myEmployee_id, 'comission_amount' : 0}
                comission_list.append(new_comission)

            else:
                #Asignar sin personal y con comision 0
                new_comission = {'employee_id' : myEmployee_id, 'plan_id' : row['plan_id'].id, 'pay_order' : row['pay_order'], 'job_id' : row['job_id'].id, 'comission_agent_id' : '', 'comission_amount' : 0}
                comission_list.append(new_comission)

        return comission_list

    # Crea la plantilla de comisiones
    def create_comission_template(self, myEmployee_id):
        comission_template_val = self.build_comission_dictionary(myEmployee_id)
        self.create(comission_template_val)


    #100% Al editar calcular el fideicomiso automaticamente
    def write(self, vals):

        # Validar datos antes de trabajar con ellos. Si no se envian en los nuevos valores se toman de los valores existentes.
        if not vals.get('employee_id'):
            employee_id = self.employee_id.id
        else:
            employee_id = vals.get('employee_id')
        
        if not vals.get('plan_id'):
            plan_id = self.plan_id.id
        else:
            plan_id = vals.get('plan_id')

        if not vals.get('job_id'):
            job_id = self.job_id.id
        else:
            job_id = vals.get('job_id')
            
        #Obtener el nombre del cargo a actualizar
        job_name = self.env['hr.job'].search([('id', '=', job_id)]).name
            
        ### Si cambio la comisión de algun empleado calcular el fideicomiso ###
        if job_name != "Fideicomiso" and vals.get('comission_amount') != None:
            #Obtener el id del cargo fideicomiso
            fideicomiso_id = self.env['hr.job'].search([('name', '=', 'Fideicomiso')]).id

            #Obtener la plantilla que se está modificando excepto la linea de fideicomiso
            template = self.env['pabs.comission.template'].search([
                '&',('employee_id', '=', employee_id),
                '&',('plan_id', '=', plan_id),
                ('job_id','!=', fideicomiso_id)])

            #Calcular la suma de comisiones asignadas
            total_comission = 0
            for row in template:

                #Utilizar el monto del registro a modificar en vez del de la plantilla
                if row.job_id.id == job_id:
                    total_comission = total_comission + vals.get('comission_amount')
                else:
                    total_comission = total_comission + row.comission_amount

            #Calcular el monto del fideicomiso = costo - total de comisiones
            fixed_price = self.env['product.pricelist.item'].search([('id', '=',plan_id)]).fixed_price
            fideicomiso_amount = fixed_price - total_comission

            # 100% Al editar no permitir que el total de las comisiones sea mayor al costo
            if total_comission > fixed_price:
                raise ValidationError("No se puede asignar un monto de comisiones mayor al costo del servicio")
            else:
                #Actualizar el registro actual
                res = super(ComissionTemplate, self).write(vals)

                #Obtener registro a modificar
                fideicomiso_row = self.search([
                    '&',('employee_id', '=', employee_id),
                    '&',('plan_id', '=', plan_id),
                    ('job_id', '=', fideicomiso_id)], limit=1)

                ### PENDIENTE: FALTA QUE SE ACTUALICE VISUALMENTE EL MONTO DEL FIDEICOMISO [ETAPA 2]
                if fideicomiso_row:
                    fideicomiso_row.comission_amount = fideicomiso_amount
                else:
                    raise ValidationError("No se pudo realizar la actualización del fideicomiso")

                return res

        return super(ComissionTemplate, self).write(vals)
    
    # 100% Al editar verificar que si tiene monto tenga forzosamente un empleado @api.constraints
    @api.constrains('comission_agent_id','comission_amount')
    def check_agent_if_amount(self):
        for row in self:
            if row.comission_amount != 0 and not row.comission_agent_id:
                raise ValidationError("Elija un empleado antes de asignar un monto")
            
    # 50/100% Solamente crear plantillas de los empleados con X CONDICIONES ||| 50% se creó condición ||| Falta definir quienes (X)
    # 0% No permitir agregar líneas


    ### 100%: Solo permitir modificar el empleado, el monto y la fecha de alta
    ### 100%: Agregar vista pivote

    # 50/100%: Al seleccionar un empleado mostrar los registros agrupados por plan y desplegada
    # 50%: Ya se muestra agrupado, falta la expansión
    # probar módulo https://apps.odoo.com/apps/modules/13.0/web_groupby_expand/