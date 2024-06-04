# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError,UserError
# from sms_api.altiria_client import *
import random
import string
import logging

_logger = logging.getLogger(__name__)

OPERATIONS = [
('salc','Alta de comisiones - Comisión'),
('salcs','Alta de comisiones - Sueldo'),
('sauc','Aumento de comisión'),
('scao','Cambios de oficina'),
('scaesc','Cambios de esquema de Sueldo a Comisión'),
('scaecs','Cambios de esquema de Comisión a Sueldo'),
('squca','Eliminar coordinador actual'),
('sagc','Agregar coordinador'),
('scac','Cambio de coordinador'),
('sreas','Reingreso de Asistente social'),
('scop','Coordinador a prueba'),
('scag','Cambio de gerente'),
('sagpr','Agregar persona que recomienda'),
('srbas','Reemplazar bono de Asistente social'),
('scat','Cambio de titular'),
]

SATATES = [
  ('draft','Borrador'),
  ('approved','Aprobado'),
  ('done','Realizado'),
  ('cancel','Cancelado'),
]

class PabsChangesFormat(models.Model):
  _name = 'pabs.changes.format'
  _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
  _description = 'Formato de cambios'
  _order = 'id desc'

  def _get_readonly(self):
    #
    for rec in self:
      readonly = False
      #
      if self.env.user.has_group('pabs_custom.edit_only_at_draft') and self.state != 'draft':
        readonly = True
      #
      rec.readonly = readonly
  
  
  @api.depends('partner_name','partner_fname','partner_mname')
  def _get_full_name(self):
    for rec in self:
      rec.full_name = f"{rec.partner_name or ''} {rec.partner_fname or ''} {rec.partner_mname or ''}"


  name = fields.Char(string="Número", default="/",readonly=True,)
  operation = fields.Selection(OPERATIONS, string="Tipo de operación", required=True,readonly=True,states={'draft':[('readonly',False)]}, tracking=True)
  operation_id = fields.Many2one(comodel_name='pabs.changes.format.operation', string="Tipo de operación", required=True,readonly=True,states={'draft':[('readonly',False)]}, tracking=True)
  state = fields.Selection(SATATES, string="Estatus", default='draft', tracking=True)
  password = fields.Char(string="Cotraseña", readonly=True)
  approve_date = fields.Datetime(string="Fecha aprobación", readonly=True, tracking=True)
  done_date = fields.Datetime(string="Fecha realizado", readonly=True, tracking=True)
  cancel_date = fields.Datetime(string="Fecha cancelado", readonly=True, tracking=True)
  notes = fields.Text(string="Notas",readonly=True,states={'draft':[('readonly',False)]}, tracking=True)
  #
  promoter_id = fields.Many2one(comodel_name='hr.employee',string="A.S",readonly=True,
    states={'draft':[('readonly',False)]}, tracking=True, domain="[('job_id.name','=','ASISTENTE SOCIAL')]")  
  company_type_id = fields.Many2one(comodel_name='type.company',string="Tipo de compañía",related='promoter_id.company_type_id')
  approver_id = fields.Many2one(comodel_name='pabs.changes.format.approver',string="Aprobador",readonly=True,required=True,
    states={'draft':[('readonly',False)]}, tracking=True,domain="[('id','=',0)]")
  #
  office_id = fields.Many2one(comodel_name='stock.warehouse',string="Oficina",readonly=True,
    states={'draft':[('readonly',False)],'approved':[('readonly',False)]}, tracking=True, domain="[('lot_stock_id.office_location','=',True)]")
  manager_id = fields.Many2one(comodel_name='hr.employee',string="Gerente",readonly=True,
    states={'draft':[('readonly',False)],'approved':[('readonly',False)]}, tracking=True, domain="[('job_id.name','=','GERENTE DE OFICINA')]")  
  manager_amount = fields.Float(string="Monto gerente", tracking=True, readonly=True, 
    states={'draft':[('readonly',False)],'approved':[('readonly',False)]})
  coordinator_id = fields.Many2one(comodel_name='hr.employee',string="Coordinador",readonly=True,
    states={'draft':[('readonly',False)],'approved':[('readonly',False)]}, tracking=True, domain="[('job_id.name','in',['COORDINADOR','COORDINADOR A PRUEBA'])]")    
  coordinator_amount = fields.Float(string="Monto coordinador", tracking=True, readonly=True, 
    states={'draft':[('readonly',False)],'approved':[('readonly',False)]})
  recommender_id = fields.Many2one(comodel_name='hr.employee',string="Recomendador",readonly=True,
    states={'draft':[('readonly',False)],'approved':[('readonly',False)]}, tracking=True)
  recommender_amount = fields.Float(string="Monto recomendador", tracking=True, readonly=True, 
    states={'draft':[('readonly',False)],'approved':[('readonly',False)]}, default=100)
  amount_ids = fields.One2many(string='Montos de AS',comodel_name='pabs.changes.format.amount', inverse_name='format_id', tracking=True, 
    states={'draft':[('readonly',False)],'approved':[('readonly',False)]}) 
  promoter_ids = fields.One2many(string='AS',comodel_name='pabs.changes.format.promoter', inverse_name='format_id', tracking=True, 
    states={'draft':[('readonly',False)],'approved':[('readonly',False)]}) 
  bonusas_ids = fields.One2many(string='Bonos de AS',comodel_name='pabs.changes.format.bonusas', inverse_name='format_id', tracking=True, 
    states={'draft':[('readonly',False)],'approved':[('readonly',False)]}) 
  readonly = fields.Boolean(string="Solo lectura", compute='_get_readonly')
  contract_id = fields.Many2one(comodel_name='pabs.contract',string="Contrato",readonly=True,states={'draft':[('readonly',False)]}, tracking=True,)
  last_full_name = fields.Char(string='Titular actual', readonly=True,)
  partner_name = fields.Char(tracking=True, string='Nombre', readonly=True,states={'draft':[('readonly',False)]})
  partner_fname = fields.Char(tracking=True, string='Apellido paterno', readonly=True,states={'draft':[('readonly',False)]})
  partner_mname = fields.Char(tracking=True, string='Apellido materno', readonly=True,states={'draft':[('readonly',False)]})
  full_name = fields.Char(string='Nuevo titular', compute='_get_full_name',store=True)
  company_id = fields.Many2one(comodel_name='res.company', string='Compañia', required=True, default=lambda s: s.env.company.id,tracking=True)
      
  @api.onchange('operation_id')
  def _onchange_operation_id(self):
    #
    res = {}
    if self.operation_id:
      #      
      self.operation = self.operation_id.code 
      
      # Se valida si el usuario tiene permimso para crear el tipo de operación
      if self.operation_id.id not in self.env.user.operation_ids.ids:
        self.operation_id = False
        self.operation = False
        return res    
      #
      if self.operation in ['scop','srbas','scat']:
        #           
        approver_ids = self.env['pabs.changes.format.approver'].search([])      
        # Filtramos los aprobadores que tengan los permisos para el tipo de operación
        approver_ids = approver_ids.filtered(lambda x: self.operation_id.id in x.operation_ids.ids)       
        #      
        if approver_ids:                      
          # Seleccionamos al azar un aprobador
          self.approver_id = approver_ids[random.randint(0,len(approver_ids)-1)]
        else:
          self.approver_id = False
        #
        domain = {'approver_id': [('id','in',approver_ids.ids)]}
        return {'domain': domain}
          
      self.promoter_id = False
      self.approver_id = False            
    #
    return res
    
  @api.onchange('manager_id')
  def _onchange_manager_id(self):
    #
    if self.manager_id:
      res = {}     
      return res
    else:
      self.manager_amount = 0

  @api.onchange('coordinator_id')
  def _onchange_coordinator_id(self):
    #
    if self.coordinator_id:
      res = {}     
      return res
    else:
      self.coordinator_amount = 0

  @api.onchange('promoter_id')
  def _onchange_promoter(self):
    #
    if self.promoter_id:
      #
      if self.operation in ['sreas','salc','salcs','sauc','scaesc','scaecs'] and self.state == 'approved':
        # Se actualiza el promotor en todas las lineas de montos 
        for amount_id in self.amount_ids:
          amount_id.promoter_id = self.promoter_id.id
        
        # No se permite el cammbio de AS
        # self.promoter_id = self._origin.promoter_id.id
        return {}
      #           
      approver_ids = self.env['pabs.changes.format.approver'].search([])      
      # Filtramos los aprobadores que tengan los permisos para el tipo de operación
      approver_ids = approver_ids.filtered(lambda x: self.operation_id.id in x.operation_ids.ids) 
      # Filtramos los aprobadores que tengan los permisos de oficina
      approver_ids = approver_ids.filtered(lambda x: self.promoter_id.warehouse_id.id in x.office_ids.ids) 
      #      
      if approver_ids:                      
        # Seleccionamos al azar un aprobador
        self.approver_id = approver_ids[random.randint(0,len(approver_ids)-1)]
      else:
        self.approver_id = False
      #
      domain = {'approver_id': [('id','in',approver_ids.ids)]}      
      
      # Se buscan los COORDINADORES DE LA PLANTILLA DEL PROMOTOR
      if self.operation in ['squca']:        
        # Se busca el puesto de coordinador
        coordinator_job_id = self.env['hr.job'].search([('name','=','COORDINADOR')], limit=1)
        if not coordinator_job_id:
          raise UserError("No se encuentra el puesto de COORDINADOR.")
        # Se buscan los coordinadores de la plantilla del promotor (AS)        
        line_ids = self.env['pabs.comission.template'].search(
        [
          ('employee_id','=',self.promoter_id.id),
          ('company_id','=',self.env.company.id)
        ])           
        # Se buscan el puesto de COORDINADOR
        coords = []
        for line_id in line_ids:
          # COORDINADOR
          if line_id.job_id.id == coordinator_job_id.id:
            coords.append(line_id.comission_agent_id.id)
        domain['coordinator_id'] = [('id','in',coords)]      
      #       
      return {'domain': domain}
    else:
      self.approver_id = False
    
  @api.onchange('contract_id')
  def _onchange_contract_id(self):
    #
    res = {}
    if self.contract_id:
      self.last_full_name = self.contract_id.full_name
      res = {}     
    return res
    
      
  @api.model
  def create(self, vals):  
    res = super(PabsChangesFormat, self).create(vals)
    next = "OPR-{}".format(str(self.search_count([])).zfill(5))    
    password = self.random_alphanumeric_string(8)
    res.write({'name':next,'password': password})

    return res 
  
  def random_alphanumeric_string(self,length):
    return ''.join(
        random.choices(
            string.ascii_letters + string.digits,
            k=length
        )
    )
  
  # Devuelve el wizard para especificar password
  def password_action(self):
      vals = {
        'format_id': self.id,        
      }
      wizard_id = self.env['pabs.changes.format.approve.wizard'].create(vals) 
      return {        
              'name': "Especificar contraseña para aprobar solicitud",
              # 'context': {'show_info': False},    
              'view_type': 'form',        
              'view_mode': 'form',        
              'res_model': 'pabs.changes.format.approve.wizard', 
              'res_id': wizard_id.id,
              'views': [(False, 'form')],            
              'type': 'ir.actions.act_window',        
              'target': 'new',    
          }

  def import_xls_action(self):
    # Se regresa el action del wizard
    action_id = self.env["ir.actions.actions"]._for_xml_id("pabs_custom.import_bonusas_wizard_action")   
    return action_id  
  
  def approve_action(self):
    # CAMBIO DE OFICINA
    if self.operation in ['scao','scop','scaecs']:      
      # Se revisa el número de adjuntos
      attachments = self.env['ir.attachment'].sudo().search_count(
        [
          ('res_model','=','pabs.changes.format'),
          ('res_id','=',self.id),
          ('company_id','=',self.env.company.id)
        ])
      if attachments == 0:
        raise UserError("No se puede aprobar la operación sin un archivo adjunto.")
    
    # REINGRESO DE ASISTENTE SOCIAL y ALTA DE COMISIONES 
    if self.operation in ['sreas','salc','salcs']:
      # Se busca el puesto de fideicomiso
      fide_job_id = self.env['hr.job'].search([('name','=','FIDEICOMISO')], limit=1)
      if not fide_job_id:
        raise UserError("No se encuentra el puesto de FIDEICOMISO.")
      # Se busca el puesto de coordinador
      coordinator_job_id = self.env['hr.job'].search([('name','=','COORDINADOR')], limit=1)
      if not coordinator_job_id:
        raise UserError("No se encuentra el puesto de COORDINADOR.")
      # Se busca el puesto de gerente de oficina
      manager_job_id = self.env['hr.job'].search([('name','=','GERENTE DE OFICINA')], limit=1)
      if not manager_job_id:
        raise UserError("No se encuentra el puesto de GERENTE DE OFICINA")
      # Se busca el puesto de recomendado
      recommender_job_id = self.env['hr.job'].search([('name','=','RECOMENDADO')], limit=1)
      if not recommender_job_id:
        raise UserError("No se encuentra el puesto de RECOMENDADO")
      # Se busca el puesto de PAPELERIA
      stationery_job_id = self.env['hr.job'].search([('name','=','PAPELERIA')], limit=1)
      if not stationery_job_id:
        raise UserError("No se encuentra el puesto de PAPELERIA")
      # Se busca el puesto de ASSITENTE SOCIAL
      promoter_job_id = self.env['hr.job'].search([('name','=','ASISTENTE SOCIAL')], limit=1)
      if not promoter_job_id:
        raise UserError("No se encuentra el puesto de ASISTENTE SOCIAL")
      #
      fide_id = self.env['hr.employee'].search([('barcode','=','FIDE')],limit=1)
      if not fide_id:
        raise UserError("No se encuentra el empleado FIDEICOMISO")
      #
      stationery_id = self.env['hr.employee'].search([('barcode','=','PAPE')],limit=1)
      if not stationery_id:
        raise UserError("No se encuentra el EMPLEADO PAPELERIA")
      
      # Se buscan todas las lineas de la plantilla del promotor (AS)
      line_ids = self.env['pabs.comission.template'].search(
      [
        ('employee_id','=',self.promoter_id.id),
        ('company_id','=',self.env.company.id)
      ])
      # Se borran todos los registros de la plantilla del AS
      qry = f"""DELETE FROM pabs_comission_template WHERE employee_id = {self.promoter_id.id};"""
      self.env.cr.execute(qry)       
      # Se borran la tabla de montos
      self.amount_ids = False
      # Se genera la nueva plantilla
      temps = []
      template_ids = self.env['pabs.comission.template.of.templates'].search([])
      for template_id in template_ids:
        #
        vals = {
          'employee_id': self.promoter_id.id,
          'code': self.promoter_id.barcode,
          'plan_id': template_id.plan_id.id,
          'pay_order': template_id.pay_order,
          'job_id': template_id.job_id.id,
          'comission_agent_id': stationery_id.id,
          'comission_amount': 1,
        }
        temps.append(vals)
      self.env['pabs.comission.template'].create(temps)
      
      # Se buscan todas las lineas de la plantilla del promotor (AS)
      line_ids = self.env['pabs.comission.template'].search(
      [
        ('employee_id','=',self.promoter_id.id),
        ('company_id','=',self.env.company.id)
      ])
      plan_ids = line_ids.mapped('plan_id')
      # Se actualizan los comisionistas y montos: PAPELERIA, COORDINADOR, GERENTE DE OFICINA, RECOMENDADOR     
      for line in line_ids:
        # PAPELERIA
        if line.job_id.id == stationery_job_id.id:
          #         
          line.write({'comission_agent_id':stationery_id.id,'comission_amount':line.plan_id.stationery})                                   
        # COORDINADOR
        elif line.job_id.id == coordinator_job_id.id and self.coordinator_id:                          
          line.write({'comission_agent_id':self.coordinator_id.id,'comission_amount':self.coordinator_amount})                           
        # GERENTE
        elif line.job_id.id == manager_job_id.id and self.manager_id:                             
          line.write({'comission_agent_id':self.manager_id.id,'comission_amount':self.manager_amount}) 
        # RECOMENDADOR
        elif line.job_id.id == recommender_job_id.id and self.recommender_id:                             
          line.write({'comission_agent_id':self.recommender_id.id,'comission_amount':self.recommender_amount})
        # FIDEICOMISO
        elif line.job_id.id == fide_job_id.id:
          line.write({'comission_agent_id':fide_id.id})                               
        else:
          qry = f"""UPDATE pabs_comission_template set comission_agent_id = NULL,comission_amount=0 
          WHERE id = {line.id};"""
          self.env.cr.execute(qry)          
      
      # Se generan los montos del promotor por plan
      amounts = []
      for plan_id in plan_ids:
        # Se agregan solo los planes que correspondan con el tipo de empresa del AS
        if plan_id.type_company.id == self.promoter_id.company_type_id.id:
          vals = {
            'format_id': self.id,
            'promoter_id': self.promoter_id.id,
            'plan_id': plan_id.id,
          }
          amounts.append((0,0,vals))
      self.amount_ids = amounts
    
    # AUMENTO DE COMISIONES, CAMBIO DE ESQUEMA DE SUELDO A COMISIÓN, CAMBIO DE ESQUEMA COMISIÓN A SUELDO
    if self.operation in ['sauc','scaesc','scaecs']:
      # Se busca el puesto de ASSITENTE SOCIAL
      promoter_job_id = self.env['hr.job'].search([('name','=','ASISTENTE SOCIAL')], limit=1)
      if not promoter_job_id:
        raise UserError("No se encuentra el puesto de ASISTENTE SOCIAL")
      
      # Se buscan todas las lineas de la plantilla del promotor y el puesto AS
      line_ids = self.env['pabs.comission.template'].search(
      [
        ('employee_id','=',self.promoter_id.id),
        ('company_id','=',self.env.company.id),
        ('job_id','=',promoter_job_id.id)
      ])
      plan_ids = line_ids.mapped('plan_id')
      # Se generan los montos del promotor por plan
      amounts = []
      for plan_id in plan_ids:
        # Se agregan solo los planes que correspondan con el tipo de empresa del AS
        if plan_id.type_company.id == self.promoter_id.company_type_id.id:
          vals = {
            'format_id': self.id,
            'promoter_id': self.promoter_id.id,
            'plan_id': plan_id.id,
            'amount': 900 if self.operation == 'scaecs' else 0
          }
          amounts.append((0,0,vals))
      self.amount_ids = amounts
      
    # REEMPLAZO DE BONO DE AS
    if self.operation == 'srbas':
      # Se busca el puesto de BONO ASISTENTE
      bonusas_job_id = self.env['hr.job'].search([('name','=','BONO ASISTENTE')], limit=1)
      if not bonusas_job_id:
        raise UserError("No se encuentra el puesto de BONO ASISTENTE")
      # Se revisa que existan registros en los bonos de AS
      if not self.bonusas_ids:
        raise UserError("No se han cargado registros de bonos de AS para reemplazar.")
      
    # Se actualiza el registro
    self.write({'state':'approved','approve_date': fields.Datetime.now()})
    return True
      
  def cancel_action(self):
    # Se actualiza el registro
    self.write({'state':'cancel','cancel_date': fields.Datetime.now()})
    return True
  
  def done_action(self):
    msg = ""
    # CAMBIO DE TITULAR
    if self.operation == 'scat':
      # Se estructura el mensaje del log
      msg += f"<p><strong>{(self.operation_id.name).upper()}</strong></p>"
      msg += f"<p><strong>Contrato: {self.contract_id.name}</strong></p>"
      msg += f"<p>{self.contract_id.partner_name}<strong>&rarr;</strong>{self.partner_name}</p>"
      msg += f"<p>{self.contract_id.partner_fname}<strong>&rarr;</strong>{self.partner_fname}</p>"
      msg += f"<p>{self.contract_id.partner_mname}<strong>&rarr;</strong>{self.partner_mname}</p>"
      
      # Se hace el cambio de titular en el contrato
      self.contract_id.write({'partner_name':self.partner_name,'partner_fname':self.partner_fname,'partner_mname':self.partner_mname})
      
      # Se actualiza el registro
      msg += f"<p>Realizado por: {self.env.user.login} - {self.env.user.name}</p>"
      self.write({'state':'done','done_date': fields.Datetime.now()})
      self.message_post(body=msg)        
      #
      return True
      

    # Se busca el puesto de coordinador
    coordinator_job_id = self.env['hr.job'].search([('name','=','COORDINADOR')], limit=1)
    if not coordinator_job_id:
      raise UserError("No se encuentra el puesto de COORDINADOR.")
    # Se busca el puesto de gerente de oficina
    manager_job_id = self.env['hr.job'].search([('name','=','GERENTE DE OFICINA')], limit=1)
    if not manager_job_id:
      raise UserError("No se encuentra el puesto de GERENTE DE OFICINA")
    # Se busca el puesto de recomendado
    recommender_job_id = self.env['hr.job'].search([('name','=','RECOMENDADO')], limit=1)
    if not recommender_job_id:
      raise UserError("No se encuentra el puesto de RECOMENDADO")
    # Se busca el puesto de PAPELERIA
    stationery_job_id = self.env['hr.job'].search([('name','=','PAPELERIA')], limit=1)
    if not stationery_job_id:
      raise UserError("No se encuentra el puesto de PAPELERIA")
    # Se busca el puesto de ASSITENTE SOCIAL
    promoter_job_id = self.env['hr.job'].search([('name','=','ASISTENTE SOCIAL')], limit=1)
    if not promoter_job_id:
      raise UserError("No se encuentra el puesto de ASISTENTE SOCIAL")
    
    # Se buscan todas las lineas de la plantilla del promotor (AS)
    line_ids = self.env['pabs.comission.template'].search(
    [
      ('employee_id','=',self.promoter_id.id),
      ('company_id','=',self.env.company.id)
    ])
    plan_ids = line_ids.mapped('plan_id')
    
    # CAMBIO DE OFICINA
    if self.operation == 'scao':
      #
      if self.coordinator_id and self.coordinator_amount <=0:
        raise UserError("Especifique un monto del coordinador mayor a cero.")
      if self.manager_id and self.manager_amount <=0:
        raise UserError("Especifique un monto del gerente mayor a cero.")      
      
      # Se hace el cambio de oficina del AS
      msg += f"<p><strong>{(self.operation_id.name).upper()}</strong></p>"
      msg += f"<p>{self.promoter_id.name}: {self.promoter_id.warehouse_id.name}<strong>&rarr;</strong>{self.office_id.name}</p>"
      self.promoter_id.warehouse_id = self.office_id.id

      # Para cada plan
      _plan_ids = []
      for plan_id in plan_ids:
        # Se buscan todas las lineas de la plantilla del promotor con el puesto COORDINADOR
        line_ids = self.env['pabs.comission.template'].search(
        [
          ('employee_id','=',self.promoter_id.id),
          ('company_id','=',self.env.company.id),
          ('job_id','=',coordinator_job_id.id),
          ('plan_id','=',plan_id.id)
        ])
        #
        if line_ids:      
          # Se buscan los puestos de COORDINADOR para sustituirlos o crearlos      
          for line_id in line_ids:
            # COORDINADOR         
            msg += f"<p><strong>PLAN: {line_id.plan_id.name}</strong></p>"
            msg += f"<p>{line_id.comission_agent_id.name}<strong>&rarr;</strong> {self.coordinator_id.name}, MONTO:{self.coordinator_amount}, PUESTO:{coordinator_job_id.name}</p>"
            line_id.write({'comission_agent_id':self.coordinator_id.id, 'comission_amount': self.coordinator_amount})                                           
        # Para cada plan se crea el puesto COORDINADOR
        else:
          if plan_id not in _plan_ids:
            _plan_ids.append(plan_id)                 
  
      # Para cada plan en _plan_ids se crea la linea de COORDINADOR
      for plan_id in _plan_ids:
        # Se busca si existe un registro con prioridad 4        
        regs = self.env['pabs.comission.template'].search_count(
        [
          ('employee_id','=',self.promoter_id.id),
          ('company_id','=',self.env.company.id),
          ('pay_order','=',4),
          ('plan_id','=',plan_id.id)
        ])  
        if regs > 0:
          msg += f"<p><strong>PLAN: {plan_id.name}</strong></p>"
          msg += f"<p>No se puede crear el registro de COORDINADOR con la prioridad 4 dado que ya existe un comisionista con la misma prioridad. </p>"          
          continue
        vals = {
          'employee_id': self.promoter_id.id,
          'plan_id': plan_id.id,
          'pay_order': 4,
          'job_id': coordinator_job_id.id,
          'comission_agent_id': self.coordinator_id.id,
          'comission_amount': self.coordinator_amount,          
        }       
        self.env['pabs.comission.template'].create(vals)
        msg += f"<p><strong>PLAN: {plan_id.name}</strong></p>"
        msg += f"<p>Se creó el registro: {self.coordinator_id.name}, MONTO:{self.coordinator_amount}, PUESTO:{coordinator_job_id.name}</p>"        

      
      # Para cada plan
      _plan_ids = []
      for plan_id in plan_ids:
        # Se buscan todas las lineas de la plantilla del promotor con el puesto GERENTE
        line_ids = self.env['pabs.comission.template'].search(
        [
          ('employee_id','=',self.promoter_id.id),
          ('company_id','=',self.env.company.id),
          ('job_id','=',manager_job_id.id),
          ('plan_id','=',plan_id.id)
        ])
        #
        if line_ids:                             
          # Se buscan los puestos de COORDINADOR para sustituirlos o crearlos       
          for line_id in line_ids:                           
            # GERENTE DE OFICINA
            msg += f"<p><strong>PLAN: {line_id.plan_id.name}</strong></p>"          
            msg += f"<p>{line_id.comission_agent_id.name}<strong>&rarr;</strong> {self.manager_id.name}, MONTO:{self.manager_amount}, PUESTO:{manager_job_id.name}</p>"
            line_id.write({'comission_agent_id':self.manager_id.id, 'comission_amount': self.manager_amount})          
        # Para cada plean se crea el puesto GERENTE
        else:          
          if plan_id not in _plan_ids:
            _plan_ids.append(plan_id)
      
      # Para cada plan in _plan_ids               
      for plan_id in _plan_ids:
        # Se busca si existe un registro con prioridad 5        
        regs = self.env['pabs.comission.template'].search_count(
        [
          ('employee_id','=',self.promoter_id.id),
          ('company_id','=',self.env.company.id),
          ('pay_order','=',5),
          ('plan_id','=',plan_id.id)
        ])  
        if regs > 0:
          msg += f"<p><strong>PLAN: {plan_id.name}</strong></p>"
          msg += f"<p>No se puede crear el registro de GERENTE con la prioridad 5 dado que ya existe un comisionista con la misma prioridad. </p>"          
          continue
        vals = {
          'employee_id': self.promoter_id.id,
          'plan_id': plan_id.id,
          'pay_order': 5,
          'job_id': manager_job_id.id,
          'comission_agent_id': self.manager_id.id,
          'comission_amount': self.manager_amount
        }        
        self.env['pabs.comission.template'].create(vals)
        msg += f"<p><strong>PLAN: {plan_id.name}</strong></p>"
        msg += f"<p>Se creó el registro: {self.manager_id.name}, MONTO:{self.manager_amount}, PUESTO:{manager_job_id.name}</p>"
      
    # ELIMINAR COORDINADOR ACTUAL
    if self.operation == 'squca':
      # 
      msg += f"<p><strong>{(self.operation_id.name).upper()}</strong></p>"
      for plan_id in plan_ids:
        # Se buscan todas las lineas de la plantilla del promotor con el puesto COORDINADOR
        line_ids = self.env['pabs.comission.template'].search(
        [
          ('employee_id','=',self.promoter_id.id),
          ('company_id','=',self.env.company.id),
          ('job_id','=',coordinator_job_id.id),
          ('plan_id','=',plan_id.id)
        ])                
        # Se buscan los puestos de COORDINADOR 
        for line_id in line_ids:         
          #
          if line_id.comission_agent_id.id == self.coordinator_id.id:
            msg += f"<p><strong>PLAN: {line_id.plan_id.name}</strong></p>"
            msg += f"<p>{line_id.comission_agent_id.name}<strong>&rarr;</strong>{False}, MONTO:{0}, PUESTO:{coordinator_job_id.name}</p>"
            line_id.write({'comission_agent_id':False, 'comission_amount': 0})          
    
    # AGREGAR COORDINADOR
    if self.operation == 'sagc':
      #
      if self.coordinator_id and self.coordinator_amount <=0:
        raise UserError("Especifique un monto del coordinador mayor a cero.")
      
      msg += f"<p><strong>{(self.operation_id.name).upper()}</strong></p>"
      # Para cada plan
      _plan_ids = []
      for plan_id in plan_ids:            
        # Se buscan todas las lineas de la plantilla del promotor con el puesto COORDINADOR
        line_ids = self.env['pabs.comission.template'].search(
        [
          ('employee_id','=',self.promoter_id.id),
          ('company_id','=',self.env.company.id),
          ('job_id','=',coordinator_job_id.id),
          ('plan_id','=',plan_id.id)
        ])
        #
        if line_ids:               
          #   
          for line_id in line_ids:
            # COORDINADOR          
            msg += f"<p><strong>PLAN: {line_id.plan_id.name}</strong></p>"
            msg += f"<p>{line_id.comission_agent_id.name}<strong>&rarr;</strong> {self.coordinator_id.name}, MONTO:{self.coordinator_amount}, PUESTO:{coordinator_job_id.name}</p>"
            line_id.write({'comission_agent_id':self.coordinator_id.id, 'comission_amount': self.coordinator_amount})                          
        # Si no se encontró el puesto de coordinador se crea un registro por cada plan
        else:
          if plan_id not in _plan_ids:
            _plan_ids.append(plan_id)
            
      # Para cada plan
      for plan_id in _plan_ids:
        # Se busca si existe un registro con prioridad 4        
        regs = self.env['pabs.comission.template'].search_count(
        [
          ('employee_id','=',self.promoter_id.id),
          ('company_id','=',self.env.company.id),
          ('pay_order','=',4),
          ('plan_id','=',plan_id.id)
        ])  
        if regs > 0:
          msg += f"<p><strong>PLAN: {plan_id.name}</strong></p>"
          msg += f"<p>No se puede crear el registro de COORDINADOR con la prioridad 4 dado que ya existe un comisionista con la misma prioridad. </p>"          
          continue
        vals = {
          'employee_id': self.promoter_id.id,
          'plan_id': plan_id.id,
          'pay_order': 4,
          'job_id': coordinator_job_id.id,
          'comission_agent_id': self.coordinator_id.id,
          'comission_amount': self.coordinator_amount
        }
        self.env['pabs.comission.template'].create(vals)
        msg += f"<p><strong>PLAN: {plan_id.name}</strong></p>"
        msg += f"<p>Se creó el registro: {self.coordinator_id.name}, MONTO:{self.coordinator_amount}, PUESTO:{coordinator_job_id.name}</p>"

    # CAMBIO DE COORDINADOR
    if self.operation == 'scac':
      if not self.coordinator_id:
        raise UserError("Especifique un coordinador.")      
      if self.coordinator_id and self.coordinator_amount <=0:
        raise UserError("Especifique un monto del coordinador mayor a cero.")      
      msg += f"<p><strong>{(self.operation_id.name).upper()}</strong></p>"
      for plan_id in plan_ids:
        # Se buscan todas las lineas de la plantilla del promotor con el puesto COORDINADOR
        line_ids = self.env['pabs.comission.template'].search(
        [
          ('employee_id','=',self.promoter_id.id),
          ('company_id','=',self.env.company.id),
          ('job_id','=',coordinator_job_id.id),
          ('plan_id','=',plan_id.id)
        ])                
        # Se buscan los puestos de COORDINADOR         
        for line_id in line_ids:
          #         
          msg += f"<p><strong>PLAN: {line_id.plan_id.name}</strong></p>"
          msg += f"<p>{line_id.comission_agent_id.name}<strong>&rarr;</strong> {self.coordinator_id.name}, MONTO:{self.coordinator_amount}, PUESTO:{coordinator_job_id.name}</p>"
          line_id.write({'comission_agent_id':self.coordinator_id.id, 'comission_amount': self.coordinator_amount})                    
    
    # AGREGAR PERSONA QUE RECOMIENDA
    if self.operation == 'sagpr': 
      #
      if self.recommender_id and self.recommender_amount <=0:
        raise UserError("Especifique un monto del recomendaor mayor a cero.")
      #
      msg += f"<p><strong>{(self.operation_id.name).upper()}</strong></p>"
      msg += f"<p>Se actualizó el recomendador {self.recommender_id.name} en el promotor {self.promoter_id.name}</p>"
      self.promoter_id.recommended_id = self.recommender_id.name      
      # Para cada plan
      _plan_ids = []
      for plan_id in plan_ids:
        # Se buscan todas las lineas de la plantilla del promotor con el puesto RECOMENDADO
        line_ids = self.env['pabs.comission.template'].search(
        [
          ('employee_id','=',self.promoter_id.id),
          ('company_id','=',self.env.company.id),
          ('job_id','=',recommender_job_id.id),
          ('plan_id','=',plan_id.id)
        ])  
        #
        if line_ids:
          for line_id in line_ids:                   
            msg += f"<p><strong>PLAN: {line_id.plan_id.name}</strong></p>"
            msg += f"<p>{line_id.comission_agent_id.name}<strong>&rarr;</strong> {self.recommender_id.name}, MONTO:{self.recommender_amount}, PUESTO:{recommender_job_id.name}</p>"
            line_id.write({'comission_agent_id':self.recommender_id.id, 'comission_amount': self.recommender_amount})
        else:
          if plan_id not in _plan_ids:
            _plan_ids.append(plan_id)

      # Para cada plan
      for plan_id in _plan_ids:
        # Se busca si existe un registro con prioridad 2        
        regs = self.env['pabs.comission.template'].search_count(
        [
          ('employee_id','=',self.promoter_id.id),
          ('company_id','=',self.env.company.id),
          ('pay_order','=',2),
          ('plan_id','=',plan_id.id)
        ])  
        if regs > 0:
          msg += f"<p><strong>PLAN: {plan_id.name}</strong></p>"
          msg += f"<p>No se puede crear el registro de RECOMENDADOR con la prioridad 2 dado que ya existe un comisionista con la misma prioridad. </p>"          
          continue

        vals = {
          'employee_id': self.promoter_id.id,
          'plan_id': plan_id.id,
          'pay_order': 2,
          'job_id': recommender_job_id.id,
          'comission_agent_id': self.recommender_id.id,
          'comission_amount': self.recommender_amount
        }     
        self.env['pabs.comission.template'].create(vals)
        msg += f"<p><strong>PLAN: {plan_id.name}</strong></p>"
        msg += f"<p>Se creó el registro: {self.recommender_id.name}, MONTO:{self.recommender_amount}, PUESTO:{recommender_job_id.name}</p>"

    # REINGRESO DE ASISTENTE SOCIAL y ALTA DE COMISIONES
    if self.operation in ['sreas','salc','salcs']:
      if self.coordinator_id and self.coordinator_amount <=0:
        raise UserError("Especifique un monto del coordinador mayor a cero.")
      if self.manager_id and self.manager_amount <=0:
        raise UserError("Especifique un monto del gerente mayor a cero.") 
      if self.recommender_id and self.recommender_amount <=0:
        raise UserError("Especifique un monto del recomendador mayor a cero.")     

      # Se busca el puesto de ASSITENTE SOCIAL
      promoter_job_id = self.env['hr.job'].search([('name','=','ASISTENTE SOCIAL')], limit=1)
      if not promoter_job_id:
        raise UserError("No se encuentra el puesto de ASISTENTE SOCIAL")   
      
      # Se valida que ningun monto sea 0 en los montos del AS
      for line in self.amount_ids:
        if line.amount <= 0:
          raise UserError(f"Especifique un monto mayor a cero para el plan {line.plan_id.name}")
      
      # Se actualiza el monto del AS de cada plan 
      # Se buscan todas las lineas de la plantilla del promotor y el puesto AS
      line_ids = self.env['pabs.comission.template'].search(
      [
        ('employee_id','=',self.promoter_id.id),
        ('company_id','=',self.env.company.id),
        ('job_id','=',promoter_job_id.id)
      ])
      for amount_id in self.amount_ids:
        #
        for line_id in line_ids:
          #
          if line_id.plan_id.id == amount_id.plan_id.id:
            line_id.write({'comission_agent_id': amount_id.promoter_id.id,'comission_amount': amount_id.amount})
      
      # Se buscan todas las lineas de la plantilla del promotor (AS)
      line_ids = self.env['pabs.comission.template'].search(
      [
        ('employee_id','=',self.promoter_id.id),
        ('company_id','=',self.env.company.id)
      ])
      plan_ids = line_ids.mapped('plan_id')
      # Se actualizan los comisionistas y montos: COORDINADOR, GERENTE DE OFICINA, RECOMENDADOR     
      for line in line_ids:       
        # COORDINADOR
        if line.job_id.id == coordinator_job_id.id and self.coordinator_id:
          line.write({'comission_agent_id':self.coordinator_id.id,'comission_amount':self.coordinator_amount})                           
        # GERENTE
        elif line.job_id.id == manager_job_id.id and self.manager_id:
          line.write({'comission_agent_id':self.manager_id.id,'comission_amount':self.manager_amount}) 
        # RECOMENDADOR
        elif line.job_id.id == recommender_job_id.id and self.recommender_id:
          line.write({'comission_agent_id':self.recommender_id.id,'comission_amount':self.recommender_amount})
      
      
      # Se hace el cambio de oficina la oficina
      msg += f"<p><strong>{(self.operation_id.name).upper()}</strong></p>"
      msg += f"<p>Se actualizó la oficina: {self.promoter_id.name}: {self.promoter_id.warehouse_id.name}<strong>&rarr;</strong>{self.office_id.name}</p>"
      self.promoter_id.warehouse_id = self.office_id.id

      msg += f"<p>Se eliminó la plantilla de comisiones ...</p>"
      msg += f"<p>Se creó una nueva plantilla de comisiones ...</p>"

    # AUMENTO DE COMISIÓN, CAMBIO DE ESQUEMA DE SUELDO A COMISIÓN, CAMBIO DE ESQUEMA DE COMISIÓN A SUELDO
    if self.operation in ['sauc','scaesc','scaecs']:
      # Se busca el esquema de pago COMISION
      commision_scheme_id = self.env['pabs.payment.scheme'].search([('name','=','COMISION')])
      if not commision_scheme_id:
        raise UserError("No se encuentra el esquema de pago: COMISION")   
      # Se busca el esquema de pago SUELDO
      salary_scheme_id = self.env['pabs.payment.scheme'].search([('name','=','SUELDO')])
      if not salary_scheme_id:
        raise UserError("No se encuentra el esquema de pago: SUELDO")   

      # Se valida que ningun monto sea 0
      for line in self.amount_ids:
        if line.amount <= 0:
          raise UserError(f"Especifique un monto mayor a cero para el plan {line.plan_id.name}")
      
      msg += f"<p><strong>{(self.operation_id.name).upper()}</strong></p>"
      
      # Se cambia el esquema a comisión 
      if self.operation == 'scaesc':
        self.promoter_id.payment_scheme = commision_scheme_id.id
        msg += f"<p>Se actualizó el esquema de pago del AS {self.promoter_id.name} a {commision_scheme_id.name}</p>"
      
      # Se cambia el esquema a sueldo
      if self.operation == 'scaecs':
        self.promoter_id.payment_scheme = salary_scheme_id.id
        msg += f"<p>Se actualizó el esquema de pago del AS {self.promoter_id.name} a {salary_scheme_id.name}</p>"
            
      # Se buscan todas las lineas de la plantilla del promotor y el puesto AS
      line_ids = self.env['pabs.comission.template'].search(
      [
        ('employee_id','=',self.promoter_id.id),
        ('company_id','=',self.env.company.id),
        ('job_id','=',promoter_job_id.id)
      ])
      # Se actualiza el amount del AS en cada plan 
      for amount_id in self.amount_ids:
        #
        for line_id in line_ids:
          #
          if line_id.plan_id.id == amount_id.plan_id.id:
            msg += f"<p>Se actualizó la comisión en el plan {amount_id.plan_id.name} -> ${amount_id.amount}</p>"
            line_id.write({'comission_agent_id':amount_id.promoter_id.id,'comission_amount': amount_id.amount})
    
    # COORDINADOR A PRUEBA
    if self.operation == 'scop': 
      if not self.coordinator_id:
        raise UserError("Especifique un coordinador.")
      if self.coordinator_id and self.coordinator_amount <=0:
        raise UserError("Especifique un monto del coordinador mayor a cero.")                
      
      msg += f"<p><strong>{(self.operation_id.name).upper()}</strong></p>"
      # Para cada AS
      for promoter_id in self.promoter_ids:
        msg += f"<br/><p>Se actualizó el coordinador {self.coordinator_id.name} para el AS {promoter_id.promoter_id.name} en los siguientes planes:</p>"      
        # Se buscan todas las lineas de la plantilla del promotor y el puesto coordinador
        line_ids = self.env['pabs.comission.template'].search(
        [
          ('employee_id','=',promoter_id.promoter_id.id),
          ('company_id','=',self.env.company.id),
          ('job_id','=',coordinator_job_id.id)
        ])
        # Se actualiza el coodinador en cada linea
        for line_id in line_ids:
          msg += f"<p>{line_id.plan_id.name} - ${self.coordinator_amount}</p>"
          line_id.write({'comission_agent_id': self.coordinator_id.id, 'comission_amount': self.coordinator_amount})

    # REEMPLAZO DE BONO DE AS
    if self.operation == 'srbas':
      #
      template_obj = self.env['pabs.comission.template']
      pricelist_obj = self.env['product.pricelist.item']
        
      # Se busca el puesto de BONO ASISTENTE
      bonusas_job_id = self.env['hr.job'].search([('name','=','BONO ASISTENTE')], limit=1)
      if not bonusas_job_id:
          raise UserError("No se encuentra el puesto de BONO ASISTENTE")
      
      # Se borran todos los registros en donde exista el puesto BONO ASISTENTE
      qry = f"""
      DELETE FROM pabs_comission_template WHERE company_id = {self.env.company.id} AND job_id = {bonusas_job_id.id};
      """    
      self.env.cr.execute(qry)          

      # Para cada registro que se subió en el excel
      for line in self.bonusas_ids:       
        #
        templates = []
        # Para cada plan
        plan_ids = pricelist_obj.search(
        [
          ('company_id','=',self.env.company.id),
          ('active','=',True),
          ('product_id.default_code','not in',['PL-99999','PL-00001','PL-10001','PL-00002'])
        ])
        #
        for plan_id in plan_ids:
          vals = {
            'employee_id':line.promoter_id.id,
            'plan_id':plan_id.id,
            'pay_order':3,
            'job_id':bonusas_job_id.id,
            'comission_agent_id':line.promoter_id.id,
            'comission_amount':line.amount,           
          }
          templates.append(vals)
        # Se crean los bonos
        template_obj.create(templates)
          
  
    # Se actualiza el registro
    msg += f"<p>Realizado por: {self.env.user.login} - {self.env.user.name}</p>"
    self.write({'state':'done','done_date': fields.Datetime.now()})
    self.message_post(body=msg)        
    #
    return True

  def rejected_action(self):
    #
    for rec in self:
      rec.state = 'draft'


class PabsChangesFormatAmount(models.Model):
  _name = 'pabs.changes.format.amount'  
  _description = 'Montos de AS por plan'
  
  format_id = fields.Many2one(string="Formato", comodel_name="pabs.changes.format",)
  promoter_id = fields.Many2one(comodel_name='hr.employee',string="A.S")
  plan_id = fields.Many2one(string="Plan", comodel_name="product.pricelist.item", required=True)
  amount = fields.Float(string="Monto")  

class PabsChangesFormatPromoter(models.Model):
  _name = 'pabs.changes.format.promoter'  
  _description = 'A.S.'
  
  format_id = fields.Many2one(string="Formato", comodel_name="pabs.changes.format",)
  promoter_id = fields.Many2one(comodel_name='hr.employee',string="A.S")

class PabsChangesFormatBonusAS(models.Model):
  _name = 'pabs.changes.format.bonusas'  
  _description = 'Bonos AS'
  
  format_id = fields.Many2one(string="Formato", comodel_name="pabs.changes.format",)
  promoter_id = fields.Many2one(comodel_name='hr.employee',string="A.S")  
  amount = fields.Float(string="Monto")
