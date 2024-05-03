# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError,UserError
from . import selections
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta


class PabsCompensation(models.Model):
    _name = 'pabs.compensation'
    _decription = 'Compesaciones PABS'  
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin'] 
        
    name = fields.Char("Compensación", default = '/',tracking=True)
    warehouse_id = fields.Many2one(string="Oficina", comodel_name="stock.warehouse", required =True,tracking=True)       
    start_date = fields.Date(string="Fecha inicial",tracking=True)
    end_date = fields.Date(string="Fecha final",tracking=True)
    line_ids = fields.One2many(comodel_name='pabs.compensation.line', inverse_name='compensation_id', string="Compensación", tracking=True)    
    company_id = fields.Many2one(comodel_name="res.company",string="Compañia",default=lambda self: self.env.company, copy=True, required=True,tracking=True) 
            
    def get_compensations(self,start=False,company_id=False):
        #         
        template_obj = self.env['pabs.comission.template']
        pricelist_obj = self.env['product.pricelist.item']
        
        # 0.- Se buscan los puestos de GERENTE DE OFICINA,COORDINADOR, BONO GERENTE Y BONO COORDINADOR
        manager_job_id = self.env['hr.job'].search(
        [
            ('name','=','GERENTE DE OFICINA'),
            ('company_id','=',company_id)
        ], limit=1)
        if not manager_job_id:
            raise UserError("No se encuentra el puesto de GERENTE DE OFICINA")
        coordinator_job_id = self.env['hr.job'].search(
        [
            ('name','=','COORDINADOR'),
            ('company_id','=',company_id)
        ], limit=1)
        if not coordinator_job_id:
            raise UserError("No se encuentra el puesto de COORDINADOR")       
                    
        # 1.- Se toman los contratos del mes previo a la fecha en que se ejecuta el método
        if start:
            today = datetime.strptime(start, "%Y-%m-%d")
        else:
            today = date.today()
        #
        last_month_date = today - relativedelta(months=1)
        start_date = last_month_date.replace(day=1)
        end_date = last_month_date.replace(day=1) + relativedelta(months=1) - relativedelta(days=1)
        
        # Se obtienen las oficinas de la lista de gerentes y oficinas
        office_manager_ids = self.env['pabs.office.manager'].search([('company_id','=',company_id)])
        office_ids = office_manager_ids.mapped('warehouse_id')
        
        # Se obtiene la producción mensual de las oficinas especificadas en la tabla
        contract_ids = self.env['pabs.contract'].search(
        [
            ('company_id','=',company_id),
            ('invoice_date','>=',start_date),
            ('invoice_date','<=',end_date),
            ('state','=','contract'), 
            # ('lot_id.warehouse_id','in',office_ids.ids)           
        ])
        # 2.- Se obtienen las oficinas a partir de los contratos       
        warehouse_ids = contract_ids.mapped('lot_id.warehouse_id')
            
        # Para cada oficina
        for warehouse_id in warehouse_ids:
            line_ids = []
            # Se obtienen datos por oficina: Eficiencia, Producción, Cancelados            
            office_data = self.get_office_data(months=4,warehouse_id=warehouse_id,start=start,company_id=company_id)
            
            # Se obtienen los AS's a partir de los contratos
            as_ids = office_data.get('period_contract_ids').mapped('sale_employee_id')               
            # Se obtienen los planes a partir de los contratos
            plan_ids = pricelist_obj.search([('product_id','in',office_data.get('period_contract_ids').mapped('name_service').ids)])         
            
            # Se obtienen las plantillas de los AS's
            template_ids = template_obj.search(
            [
                ('employee_id','in',as_ids.ids),
                ('plan_id','in',plan_ids.ids),
                ('company_id','=',company_id)
            ])   
            
            # Se obtienen los: GERENTES DE OFICINA (activos) a partir de los AS de los contratos y de las plantillas                
            manager_ids = template_ids.filtered(lambda r: r.job_id.id == manager_job_id.id and r.comission_agent_id.employee_status.name == 'ACTIVO').mapped('comission_agent_id')
        
            # Se obtienen los: COORDINADORES (activos) a partir de los AS de los contratos y de las plantillas
            coordinator_ids = template_ids.filtered(lambda r: r.job_id.id == coordinator_job_id.id and r.comission_agent_id.employee_status.name == 'ACTIVO').mapped('comission_agent_id')
                                
            
            #################################################### CALCULO DEL BONO: GERENTES Y COORDINADORES ###################################################
            
            # GERENTES                                
            for manager_id in manager_ids:                
                #
                manager_contract_ids = self.env['pabs.contract']
                for contract_id in office_data.get('period_contract_ids'):
                    # Se busca si el gerente está en el árbol del contrato
                    for node in contract_id.commission_tree:
                        if node.comission_agent_id.id == manager_id.id and node.job_id.id == manager_job_id.id:
                            manager_contract_ids += contract_id
                            break
                
                # Bono Gerente                       
                bonus_manager_amount = self.get_compensation_amount('manager','bonus',office_data.get('period_production'),company_id)              
                
                # Se calcula el monto del bono si el gerente está en la tabla de gerente y oficina
                amount = 0
                office_manager_id = self.env['pabs.office.manager'].search(
                [
                    ('warehouse_id','=',warehouse_id.id),
                    ('employee_id','=',manager_id.id),
                    ('company_id','=',company_id),
                ],limit=1)
                #
                if office_manager_id:                    
                    amount = bonus_manager_amount * office_data.get('period_production') * office_data.get('efficiency')
                #    
                vals = {                  
                    'employee_id':manager_id.id,
                    'type':'manager',
                    'compensation_type':'bonus',
                    'amount': amount,
                    'bonus': bonus_manager_amount,
                    'personal_production':len(manager_contract_ids),                    
                    'period_production':office_data.get('period_production'),
                    'period_canceled':office_data.get('period_cancelled'),
                    'period_efficiency':office_data.get('period_efficiency') * 100,                    
                    'production':office_data.get('efficiency_production'),
                    'canceled': office_data.get('efficiency_cancelled'),
                    'efficiency':office_data.get('efficiency') * 100,                                                    
                }
                #
                line_ids.append((0,0,vals))

            # COORDINADORES
            for coordinator_id in coordinator_ids:
                #
                team_data = self.get_team_data(4,warehouse_id,coordinator_id,coordinator_job_id,start)
                team_efficiency = team_data.get('team_efficiency')
                team_production = team_data.get('team_production')
                team_cancelled = team_data.get('team_cancelled')
                #               
                coordinator_contract_ids = self.env['pabs.contract']
                for contract_id in office_data.get('period_contract_ids'):
                    # Se busca si el coordinador está en el árbol del contrato
                    for node in contract_id.commission_tree:
                        if node.comission_agent_id.id == coordinator_id.id and node.job_id.id == coordinator_job_id.id:
                            coordinator_contract_ids += contract_id
                            break

                #                        
                month_team_production = len(coordinator_contract_ids)
                # Bono Coordinador                       
                bonus_coordinator_amount = self.get_compensation_amount('coordinator','bonus',len(coordinator_contract_ids),company_id)
                vals = {
                    'employee_id': coordinator_id.id,
                    'type':'coordinator',
                    'compensation_type':'bonus',
                    'amount': bonus_coordinator_amount * month_team_production * team_efficiency,
                    'bonus': bonus_coordinator_amount,                    
                    'personal_production':month_team_production,
                    'period_production':office_data.get('period_production'),
                    'period_canceled':office_data.get('period_cancelled'),
                    'period_efficiency':office_data.get('period_efficiency') * 100,   
                    'production': team_production,
                    'canceled': team_cancelled,
                    'efficiency': team_efficiency * 100,                                                                            
                }
                #
                line_ids.append((0,0,vals))                          
        
            # Se crea la compensación        
            if line_ids and warehouse_id.id in office_ids.ids:
                compensation_vals = {
                    'name': f"Bono - {self.search_count([])+1}",
                    'warehouse_id':warehouse_id.id,                                            
                    'start_date':start_date,
                    'end_date':end_date,                
                    'line_ids': line_ids,
                }
                compensation_id = self.create(compensation_vals)
        #
        return True
            
    def get_compensation_amount(self,type,compensation_type,production,company_id):
        amount = 0
        amount_id = self.env['pabs.compensation.amount'].search(
        [
            ('company_id','=',company_id),
            ('type','=',type),
            ('compensation_type','=',compensation_type),
            ('min_production','<=',production),
            ('max_production','>=',production),
        ],limit=1)
        #
        if amount_id:
            amount = amount_id[0].amount
        #
        return amount
    
    def get_office_data(self,months=0,warehouse_id=False,start=False,company_id=False):        
        # Se obtienen las fechas inicial y final 
        if start:
            today = datetime.strptime(start, "%Y-%m-%d")
        else:
            today = date.today()                
        #       
        prev_month_date = today - relativedelta(months=months)        
        start_date = prev_month_date.replace(day=1)
        end_date = today.replace(day=1) - relativedelta(days=1)   
    
        # Producción para la eficiencia
        efficiency_contract_ids = self.env['pabs.contract'].search(
        [
            ('company_id','=',company_id),
            ('invoice_date','>=',start_date),
            ('invoice_date','<=',end_date),
            ('lot_id.warehouse_id','=',warehouse_id.id),          
            ('state','=','contract')
        ])        
        # Cancelados para la eficiencia
        efficiency_cancel_contract_ids = efficiency_contract_ids.filtered(lambda rec: rec.contract_status_item.status in ['SUSP. PARA CANCELAR','CANCELADO','VERIFICACION SC'])        
        # Eficiencia
        efficiency = (len(efficiency_contract_ids) - len(efficiency_cancel_contract_ids)) / len(efficiency_contract_ids) if len(efficiency_contract_ids) > 0 else 0      
        
        # Se obtienen las fechas inicial y final para la producción mensual
        last_month_date = today - relativedelta(months=1)
        start_date = last_month_date.replace(day=1)
        end_date = last_month_date.replace(day=1) + relativedelta(months=1) - relativedelta(days=1)
    
        # Producción mensual
        period_contract_ids = self.env['pabs.contract'].search(
        [
            ('company_id','=',company_id),
            ('invoice_date','>=',start_date),
            ('invoice_date','<=',end_date),
            ('lot_id.warehouse_id','=',warehouse_id.id),          
            ('state','=','contract')
        ])   
        period_cancel_contract_ids = period_contract_ids.filtered(lambda rec: rec.contract_status_item.status in ['SUSP. PARA CANCELAR','CANCELADO','VERIFICACION SC'])        
        period_efficiency = (len(period_contract_ids) - len(period_cancel_contract_ids)) / len(period_contract_ids) if len(period_contract_ids) > 0 else 0      
        
        # Se crea el dicionario de datos
        office_data = {}
        office_data.update(
        {
            'efficiency_production': len(efficiency_contract_ids),
            'efficiency_cancelled': len(efficiency_cancel_contract_ids),
            'efficiency': efficiency,
            'period_production': len(period_contract_ids),
            'period_cancelled': len(period_cancel_contract_ids),
            'period_efficiency': period_efficiency,
            'period_contract_ids': period_contract_ids
        })
        return office_data
        
    def get_team_data(self,months=0,warehouse_id=False,coordinator_id=False,job_id=False,start=False,company_id=False):      
        # Se obtienen las fechas inicial y final 
        if start:
            today = datetime.strptime(start, "%Y-%m-%d")
        else:
            today = date.today()
        #       
        prev_month_date = today - relativedelta(months=months)        
        start_date = prev_month_date.replace(day=1)
        end_date = today.replace(day=1) - relativedelta(days=1)      
        
        #       
        contract_ids = self.env['pabs.contract'].search(
        [
            ('company_id','=',company_id),
            ('invoice_date','>=',start_date),
            ('invoice_date','<=',end_date),
            ('lot_id.warehouse_id','=',warehouse_id.id),          
            ('state','=','contract')
        ])
        
        team_contract_ids = self.env['pabs.contract']
        # Se obtienen los contratos del equipo del coordinador
        for contract_id in contract_ids:            
            # Se analiza el árbol del contrato
            for node in contract_id.commission_tree:
                # Si el coordinador figura en el contrato
                if node.comission_agent_id.id == coordinator_id.id and node.job_id.id == job_id.id:                  
                    # Si la oficina del coordinador es la misma que la del AS del contrato
                    if coordinator_id.warehouse_id.id == contract_id.sale_employee_id.warehouse_id.id:
                        team_contract_ids += contract_id                        
                    break

        # Se obtienen los cancelados del equipo del coordinador
        cancel_team_contract_ids = team_contract_ids.filtered(lambda rec: rec.contract_status_item.status in ['SUSP. PARA CANCELAR','CANCELADO','VERIFICACION SC'])
        # Se calcula la eficiencia del equipo del coordinador
        efficiency = (len(team_contract_ids) - len(cancel_team_contract_ids)) / len(team_contract_ids) if len(team_contract_ids) > 0 else 0        
        #
        data = {
            'team_efficiency': efficiency,
            'team_production':len(team_contract_ids),
            'team_cancelled': len(cancel_team_contract_ids)
        }        
        return data
    

class PabsCompensationLine(models.Model):
    _name = 'pabs.compensation.line'
    _decription = 'Detalle de Compesaciones PABS'
    _inherit = 'mail.thread'       

    compensation_id = fields.Many2one(string="Compensación", comodel_name="pabs.compensation", required =True,tracking=True,ondelete='cascade')  
    warehouse_id = fields.Many2one(string="Oficina", comodel_name="stock.warehouse", related='compensation_id.warehouse_id')       
    employee_id = fields.Many2one(string="Empleado", comodel_name="hr.employee", required =True,tracking=True)      
    type = fields.Selection(selections.TYPES, string="Tipo", required =True,tracking=True)
    compensation_type = fields.Selection(selections.COMPENSATIONS, string="Tipo compensación", required =True,tracking=True)
    amount = fields.Float(string="Monto bono",tracking=True)
    bonus = fields.Float(string="Bono",tracking=True)
    
    personal_production = fields.Integer(string="Producción grupo",tracking=True)

    period_production = fields.Integer(string="Producción oficina",tracking=True)
    period_canceled = fields.Integer(string="Cancelados oficina",tracking=True)
    period_efficiency = fields.Float(string="Efectividad oficina",tracking=True) 
    
    production = fields.Integer(string="Producción",tracking=True)
    canceled = fields.Integer(string="Cancelados",tracking=True)
    efficiency = fields.Float(string="Efectividad",tracking=True)           
    company_id = fields.Many2one(comodel_name="res.company",string="Compañia",default=lambda self: self.env.company, copy=True, required=True,tracking=True)




