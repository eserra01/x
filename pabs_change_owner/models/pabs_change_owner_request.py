# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError,UserError

SATATES = [
    ('draft','Borrador'),
    ('approved','Aprobado'),
    ('done','Realizado'),
    ('cancel','Cancelado'),
]

class PabsChangeOwnerRequest(models.Model):
    _name = 'pabs.change.owner.request'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']  
    _decription = 'Solicitudes de cambio de titular'

    @api.depends('partner_name','partner_fname','partner_mname')
    def _get_full_name(self):
        for rec in self:
            rec.full_name = f"{rec.partner_name or ''} {rec.partner_fname or ''} {rec.partner_mname or ''}"
    
    @api.onchange('contract_id')
    def _onchange_contract_id(self):
        #
        res = {}
        if self.contract_id:
            self.last_full_name = self.contract_id.full_name
            self.partner_name = False
            self.partner_fname = False
            self.partner_mname = False
            res = {}     
        return res
    
    name = fields.Char(string="Número solicitud", required=True,tracking=True, readonly=True,default="/")
    state = fields.Selection(SATATES, string="Estatus", default='draft', tracking=True)
    approve_user_id = fields.Many2one(string="Aprueba", comodel_name="res.users",readonly=True,states={'draft':[('readonly',False)]},tracking=True)
    done_user_id = fields.Many2one(string="Realiza", comodel_name="res.users",readonly=True,states={'draft':[('readonly',False)]},tracking=True)
    contract_id = fields.Many2one(comodel_name='pabs.contract',string="Contrato",readonly=True,states={'draft':[('readonly',False)]}, tracking=True,required=True)
    last_full_name = fields.Char(string='Titular actual', readonly=True,)
    partner_name = fields.Char(string='Nombre', readonly=True,states={'draft':[('readonly',False)]},tracking=True,required=True)
    partner_fname = fields.Char(string='Apellido paterno', readonly=True,states={'draft':[('readonly',False)]},tracking=True,required=True)
    partner_mname = fields.Char(string='Apellido materno', readonly=True,states={'draft':[('readonly',False)]},tracking=True,required=True)
    full_name = fields.Char(string='Nuevo titular', compute='_get_full_name',store=True)
    approve_date = fields.Datetime(string="Fecha aprobación", readonly=True, tracking=True)
    done_date = fields.Datetime(string="Fecha realizado", readonly=True, tracking=True)
    cancel_date = fields.Datetime(string="Fecha cancelado", readonly=True, tracking=True)
    notes = fields.Text(string="Notas",readonly=True,states={'draft':[('readonly',False)]}, tracking=True)
    company_id = fields.Many2one(comodel_name="res.company",string="Compañia",default=lambda self: self.env.company, copy=True, required=True) 

    @api.model
    def create(self, vals):  
        res = super(PabsChangeOwnerRequest, self).create(vals)
        next = "REQ-{}".format(str(self.search_count([])).zfill(5))          
        res.write({'name':next})
        return res 
    
    def approve_action(self):
        # Se actualiza el esatatus y la fecha de aprobación
        self.write({'state':'approved','approve_date':fields.Datetime.now(),'approve_user_id':self.env.user.id})
        return True
    
    def done_action(self):
        # Se realiza el cambio de titular
        # Se estructura el mensaje del log
        msg = ""
        msg += f"<p><strong>Cambio de titular</strong></p>"
        msg += f"<p><strong>Contrato: {self.contract_id.name}</strong></p>"
        msg += f"<p>{self.contract_id.partner_name}<strong>&rarr;</strong>{self.partner_name}</p>"
        msg += f"<p>{self.contract_id.partner_fname}<strong>&rarr;</strong>{self.partner_fname}</p>"
        msg += f"<p>{self.contract_id.partner_mname}<strong>&rarr;</strong>{self.partner_mname}</p>"
        # Se hace el cambio de titular en el contrato
        self.contract_id.write({'partner_name':self.partner_name,'partner_fname':self.partner_fname,'partner_mname':self.partner_mname})
        # Se actualiza el registro
        msg += f"<p>Realizado por: {self.env.user.login} - {self.env.user.name}</p>"
        self.write({'state':'done','done_date': fields.Datetime.now(),'done_user_id':self.env.user.id})
        self.message_post(body=msg)  
        return True
    
    def cancel_action(self):
        # Se actualiza el esatatus y la fecha de cancelación
        self.write({'state':'cancel','cancel_date':fields.Datetime.now()})
        return True
    