# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError,UserError
from . import selections
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta


class PabsTrimestralCommission(models.Model):
    _name = 'pabs.trimestral.commission'
    _decription = 'Comisiones Trimestrales PABS'  
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin'] 
        
    name = fields.Char("Comisión trimestral", default = '/',tracking=True)
    warehouse_id = fields.Many2one(string="Oficina", comodel_name="stock.warehouse", required =True,tracking=True)      
    start_date = fields.Date(string="Fecha inicial",tracking=True)
    end_date = fields.Date(string="Fecha final",tracking=True)
    trimester_id = fields.Many2one(string="Trimestre", comodel_name="pabs.trimester", required =True,tracking=True)    
    line_ids = fields.One2many(comodel_name='pabs.trimestral.commission.line', inverse_name='commission_id', string="Comisión", tracking=True)    
    company_id = fields.Many2one(comodel_name="res.company",string="Compañia",default=lambda self: self.env.company, copy=True, required=True,tracking=True) 
            
    
    def get_commissions(self,start=False,company_id=False):
        #################################################### CALCULO COMISIONES: GERENTES Y COORDINADORES ###################################################
        template_obj = self.env['pabs.comission.template']
        pricelist_obj = self.env['product.pricelist.item']         
        # Si corresponde evaluar el trismetre en base a la fecha dada 
        trimester_id = self.trimester_flag(start=start,company_id=company_id)       
        if trimester_id:
            # Se buscan los puestos de GERENTE DE OFICIN Y COORDINADOR
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
        
            # Obtenemos las fechas del trimestre
            if start:
                today = datetime.strptime(start, "%Y-%m-%d")
            else:
                today = date.today()   
            # Si es el primer trimestre se tiene que considerar el año anterior
            if trimester_id.month == 3:
                start_date = datetime(today.year - 1, trimester_id.first_month, 1)
                last_month_date = datetime(today.year, trimester_id.last_month, 1)
                end_date = last_month_date.replace(day=1) + relativedelta(months=1) - relativedelta(days=1)
            else:
                start_date = datetime(today.year, trimester_id.first_month, 1)
                last_month_date = datetime(today.year, trimester_id.last_month, 1)
                end_date = last_month_date.replace(day=1) + relativedelta(months=1) - relativedelta(days=1)
            
            # Se obtienen las oficinas de la lista de gerentes y oficinas
            office_manager_ids = self.env['pabs.office.manager'].search([('company_id','=',company_id)])
            office_ids = office_manager_ids.mapped('warehouse_id')

            # Se obtiene la producción trimestral de las oficinas especificadas en la tabla
            contract_ids = self.env['pabs.contract'].search(
            [
                ('company_id','=',company_id),
                ('invoice_date','>=',start_date),
                ('invoice_date','<=',end_date),
                ('state','=','contract'),
                # ('lot_id.warehouse_id','in',office_ids.ids)                  
            ])
            
            # Se obtienen las oficinas a partir de los contratos            
            warehouse_ids = contract_ids.mapped('lot_id.warehouse_id')
            # Para cada oficina
            for warehouse_id in warehouse_ids:  
                #
                line_ids = []
                # Producción trimestral por oficina
                trimester_contract_ids = contract_ids.filtered(lambda rec: rec.lot_id.warehouse_id.id == warehouse_id.id)                                                       
                # Se obtienen los AS's a partir de los contratos
                as_ids = trimester_contract_ids.mapped('sale_employee_id')               
                # Se obtienen los planes a partir de los contratos
                plan_ids = pricelist_obj.search(
                [
                    ('product_id','in',trimester_contract_ids.mapped('name_service').ids),
                    ('company_id','=',company_id)
                ])                         
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
        
                # GERENTES                
                # Se obtienen los contratos del gerente
                for manager_id in manager_ids:
                    manager_contract_ids = self.env['pabs.contract']
                    for contract_id in trimester_contract_ids:
                        # Se busca si el gerente está en el árbol del contrato
                        for node in contract_id.commission_tree:
                            if node.comission_agent_id.id == manager_id.id and node.job_id.id == manager_job_id.id:
                                manager_contract_ids += contract_id
                                break

                    # Comisión Gerente                       
                    commission_manager_amount = self.get_compensation_amount('manager','commission',int(len(manager_contract_ids)/3),company_id)
                    vals = {                  
                        'employee_id':manager_id.id,
                        'type':'manager',
                        'commission_type':'commission',                        
                        'bonus': commission_manager_amount,
                        'production':len(trimester_contract_ids),
                        'personal_production':len(manager_contract_ids),                                            
                        'avg_production': int(len(manager_contract_ids)/3),                                                                     
                    }                  
                    #
                    line_ids.append((0,0,vals))
                    # Se actualizan las plantillas de los AS de los contratos
                    if warehouse_id.id in office_ids.ids:
                        self.update_templates(warehouse_id=warehouse_id,job_id=manager_job_id,comission_agent_id=manager_id,amount=commission_manager_amount)
                
                # COORDINADORES                
                # Se obtienen los contratos del gerente
                for coordinator_id in coordinator_ids:
                    coordinator_contract_ids = self.env['pabs.contract']            
                    for contract_id in trimester_contract_ids:
                        # Se busca si el coordinador está en el árbol del contrato
                        for node in contract_id.commission_tree:
                            if node.comission_agent_id.id == coordinator_id.id and node.job_id.id == coordinator_job_id.id:
                                coordinator_contract_ids += contract_id
                                break

                    # Comisión coordinador                       
                    commission_coordinator_amount = self.get_compensation_amount('coordinator','commission',int(len(coordinator_contract_ids)/3),company_id)
                    vals = {                  
                        'employee_id':coordinator_id.id,
                        'type':'coordinator',
                        'commission_type':'commission',                        
                        'bonus': commission_coordinator_amount,
                        'production':len(trimester_contract_ids),
                        'personal_production':len(coordinator_contract_ids),                                            
                        'avg_production': int(len(coordinator_contract_ids)/3),                                                                     
                    }                  
                    #
                    line_ids.append((0,0,vals))
                    # Se actualizan las plantillas de los AS de los contratos
                    if warehouse_id.id in office_ids.ids:
                        self.update_templates(warehouse_id=warehouse_id,job_id=coordinator_job_id,comission_agent_id=coordinator_id,amount=commission_coordinator_amount,company_id=company_id)
                
                # Se crea la comisión        
                if line_ids and warehouse_id.id in office_ids.ids:
                    commission_vals = {
                        'name': f"Comisión trimestral - {self.search_count([])+1}",
                        'warehouse_id':warehouse_id.id,                                            
                        'start_date':start_date,
                        'end_date':end_date,  
                        'trimester_id': trimester_id.id,                     
                        'line_ids': line_ids,
                    }
                    commision_id = self.create(commission_vals)
            
            # Se actualiza el trimestre
            trimester_id.write({'last_done_date':datetime.today()})    
        return
    
    def trimester_flag(self,start=False,company_id=False):        
        #
        if start:
            today = datetime.strptime(start, "%Y-%m-%d")
        else:
            today = date.today()        
        # Se busca un trimestre que corresponda al mes a evaluar y que no esté calculado        
        trimester_id = self.env['pabs.trimester'].search(
        [
            ('month','=',today.month),          
            ('company_id','=',company_id),
        ])      
        #
        return trimester_id

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

    def update_templates(self,warehouse_id=False,job_id=False,comission_agent_id=False,amount=0,company_id=False):
        # Si está activa la configuración para actualizar plantillas de AS
        if self.env.company.update_templates:                          
            # Se obtienen los AS's activos de la oficina
            employee_ids =self.env['hr.employee'].search(
            [
                ('company_id','=',company_id),
                ('warehouse_id','=',warehouse_id.id),
                ('employee_status.name','=','ACTIVO'),
                ('job_id.name','=','ASISTENTE SOCIAL'),                
            ])

            # Se buscan las plantillas en donde aparezcan todos los employee_ids
            temp_ids = self.env['pabs.comission.template'].search(
            [
                ('employee_id','in',employee_ids.ids),
                ('company_id','=',company_id),
            ])  
            # Se filtran los templates a actualizar
            template_ids = temp_ids.filtered(lambda rec: rec.job_id.id == job_id.id and rec.comission_agent_id.id == comission_agent_id.id)
            
            # Se actualiza el monto del comission_agent_id            
            if template_ids:
                ids = ""
                for id in template_ids:
                    ids += str(id.id) + ','
                ids = ids[:-1]
                qry = f"""
                UPDATE pabs_comission_template SET comission_amount = {amount} 
                WHERE id IN ({ids});
                """            
                self._cr.execute(qry)
            
        return
    
class PabsTrimestralCommisionLine(models.Model):
    _name = 'pabs.trimestral.commission.line'
    _decription = 'Detalle de comisiones trimestrales PABS'
    _inherit = 'mail.thread'    

    commission_id = fields.Many2one(string="Comisión", comodel_name="pabs.trimestral.commission", required =True,tracking=True,ondelete='cascade')  
    employee_id = fields.Many2one(string="Empleado", comodel_name="hr.employee", required =True,tracking=True)      
    type = fields.Selection(selections.TYPES, string="Tipo", required =True,tracking=True)
    commission_type = fields.Selection(selections.COMPENSATIONS, string="Tipo comissión", required =True,tracking=True)   
    bonus = fields.Float(string="Comisión",tracking=True)           
    production = fields.Integer(string="Producción oficina ",tracking=True)    
    personal_production = fields.Integer(string="Producción grupo ",tracking=True)    
    avg_production = fields.Integer(string="Producción promedio",tracking=True)    
    company_id = fields.Many2one(comodel_name="res.company",string="Compañia",default=lambda self: self.env.company, copy=True, required=True,tracking=True)




