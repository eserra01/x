# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import pytz
from odoo.exceptions import ValidationError
tz = pytz.timezone('America/Mexico_City')


class IiServicio(models.Model):
    _name = 'ii.servicio'

    name = fields.Char(string="Nombre")
    # [('pendiente', 'PENDIENTE'),
    # ('terminado', 'TERMINADO'),
    # ('cancelado', 'CANCELADO')],


class IiLlamada(models.Model):
    _name = 'ii.llamada'

    name = fields.Char(string="Nombre")
    # [('si', 'Si'),
    # ('no', 'No')],


class IiCertificamos(models.Model):
    _name = 'ii.certificamos'

    name = fields.Char(string="Nombre")
    # [('si', 'Si'),
    # ('no', 'No')],


class IiVistaPersonal(models.Model):
    _name = 'ii.vista.personal'

    name = fields.Char(string="Nombre")
    # [('si', 'Si'),
    # ('no', 'No')],


class IiServicio2(models.Model):
    _name = 'ii.servicio2'

    name = fields.Char(string="Nombre")
    # [('cremacion', 'Cremacion')],


class IiCausaFallecim(models.Model):
    _name = 'ii.causa.fallecim'

    name = fields.Char(string="Nombre")
    # [('insuficiencia_respiratoria', 'INSUFICIENCIA RESPIRATORIA')]


class CsServiConfirm(models.Model):
    _name = 'cs.servi.confirm'

    name = fields.Char(string="Nombre")

    # [('si', 'Si'),
    # ('no', 'No')],


class DsAtiendeServicio(models.Model):
    _name = 'ds.atiende.servicio'

    name = fields.Char(string="Nombre")

    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, default=lambda self: self.env.company)
    # [('0', 'ROBERTO GOMEZ PEREZ')],


class DsSucursalVelacion(models.Model):
    _name = 'ds.sucursal.velacion'

    name = fields.Char(string="Nombre")

    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, default=lambda self: self.env.company)
    # [('0', 'LOPEZ MATEOS')],


class DsTipoServicio(models.Model):
    _name = 'ds.tipo.servicio'

    name = fields.Char(string="Nombre")
    # [('0', 'PLAN')],


class DsCapilla(models.Model):
    _name = 'ds.capilla'

    name = fields.Char(string="Nombre")

    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, default=lambda self: self.env.company)
    # [('0', 'PROPIAS')],


class DsInterplaza(models.Model):
    _name = 'ds.interplaza'

    name = fields.Char(string="Nombre")
    # [('si', 'Si'),
    # ('no', 'No')],


class DsOrigen(models.Model):
    _name = 'ds.origen'

    name = fields.Char(string="Nombre")
    # [('0', 'JAL, PUERTO VALLARTA')],


class DsSucursalQEntregCenizas(models.Model):
    _name = 'ds.sucursal.qentreg.cenizas'

    name = fields.Char(string="Nombre")

    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, default=lambda self: self.env.company)
    # [('0', 'ACAPULCO')],


class DsAplicaSeguro(models.Model):
    _name = 'ds.aplica.seguro'

    name = fields.Char(string="Nombre")
    # [('si', 'Si'),
    # ('no', 'No')],


class DsAtaud(models.Model):
    _name = 'ds.ataud'

    name = fields.Char(string="Nombre")

    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, default=lambda self: self.env.company)
    # [('0', 'RAMIRO RENTERIA ROBLES')],


class DsUrna(models.Model):
    _name = 'ds.urna'

    name = fields.Char(string="Nombre")

    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, default=lambda self: self.env.company)
    # [('0', 'RAMIRO RENTERIA ROBLES')],


class RelacionConfinad(models.Model):
    _name = 'relacion.confinad'

    name = fields.Char(string="Nombre")
    # [('0', 'HIJO')],


class IvLugarVelacion(models.Model):
    _name = 'iv.lugar.velacion'

    name = fields.Char(string="Nombre")

    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, default=lambda self: self.env.company)
    # [('0', ' CAPILLA ')],


class IvNombreDeCapilla(models.Model):
    _name = 'iv.nombre.capilla'

    name = fields.Char(string="Nombre")

    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, default=lambda self: self.env.company)
    # [('0', 'ESPERANZA')],


class DcFormaPago(models.Model):
    _name = 'dc.forma.pago'

    name = fields.Char(string="Nombre")
    # [('0', 'SEMANAL')],


class IrOperativo(models.Model):
    _name = 'ir.operativo'

    name = fields.Char(string="Nombre")

    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, default=lambda self: self.env.company)
    # [('0', 'JUAN MONTES ROSALES')],


class Carroza(models.Model):
    _name = 'carroza'

    name = fields.Char(string="Nombre")

    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, default=lambda self: self.env.company)
    # [('0', 'JRA5643-300C-NEGRA')],


class IgEntregoRopa(models.Model):
    _name = 'ig.entrego.ropa'

    name = fields.Char(string="Nombre")
    # [('si', 'Si'),
    # ('no', 'No')],


class IgProveedorEmbalsama(models.Model):
    _name = 'ig.proveedor.embalsama'

    name = fields.Char(string="Nombre")


    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, default=lambda self: self.env.company)
    # [('0', 'REYNALDO')],


class IgTemplo(models.Model):
    _name = 'ig.templo'

    name = fields.Char(string="Nombre")

    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, default=lambda self: self.env.company)
    # [('0', 'PAULINA RODRIGUEZ GONZALEZ')],#

class PlaceOfCremation(models.Model):
    _name = 'mortuary.cremation'

    name = fields.Char(string='Nombre')

    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, default=lambda self: self.env.company)

class Mortuary(models.Model):
    _name = 'mortuary'
    _description = 'modulo de funeraria'
    _inherit = 'mail.thread'

    name = fields.Char(string="Bitácora", required=True)
    partner_id = fields.Many2one(comodel_name='res.partner',
        string='contacto')
    balance = fields.Float(string='Saldo',
        compute="_calc_balance")
    total_invoiced = fields.Float(string='Total',
        compute="_calc_total_invoiced")

    birthdate = fields.Date(string='Fecha de nacimiento')
    ii_servicio = fields.Many2one("ii.servicio", string="Servicio")
    ii_finado = fields.Char(string="Finado", required=True)
    ii_fecha_creacion = fields.Date(
        string="Fecha creacion", default=datetime.now(tz),
        copy=False)
    ii_hora_creacion = fields.Char(
        string="Hora creacion",
        tracking=True,
        copy=False)
    ii_llamada = fields.Many2one("ii.llamada", string="Llamada")
    ii_certificamos = fields.Many2one("ii.certificamos", string="Certificamos")
    ii_vista_personal = fields.Many2one("ii.vista.personal", string="Vista personal")
    ii_folio_certificad = fields.Char(string="Folio certificado")
    ii_servicio_2 = fields.Many2one("ii.servicio2", string="Servicio")
    ii_causa_fallecim = fields.Many2one(
        "ii.causa.fallecim", string="Causa de fallecimiento")
    ii_lugar_fallec = fields.Char(string="Lugar de fallecimiento")
    ii_direcc_fallecimiento = fields.Text(string="Direccion de fallecimiento")

    cs_servi_confirm = fields.Many2one("cs.servi.confirm", string="Servicio confirmado")
    cs_agente_confir = fields.Char(string="Agente que confirma")
    cs_cliente_confir = fields.Char(string="Cliente que confirma")
    cs_tel = fields.Char(string="Telefono")
    cs_fecha_confirm = fields.Date(string="Fecha de confirmacion")
    cs_hora_confirm = fields.Float(string="Hora de confirmacion", tracking=True)
    cs_observacions = fields.Text(string="Observaciones", compute="get_comentarios")
    cs_nuevo_comentario = fields.Text(string="Nuevo comentario")

    tc_no_contrato = fields.Char(string="Nùmero de contrato")
    tc_nomb_titular = fields.Char(string="Nombre de titular")

    ds_atiende_servicio = fields.Many2one(
        "ds.atiende.servicio", string="Atiende servicio")
    ds_sucursal_de_velacion = fields.Many2one(
        "ds.sucursal.velacion", string="Sucursal de velacion")
    ds_tipo_de_servicio = fields.Many2one("ds.tipo.servicio", string="Tipo de servicio")
    ds_capilla = fields.Many2one("ds.capilla", string="Capilla")
    ds_interplaza = fields.Many2one("ds.interplaza", string="Interplaza")
    ds_origen = fields.Many2one("ds.origen", string="Origen")
    ds_personas_autorizadas = fields.Char(string="Personas autorizadas")
    ds_fecha_entrega_cenizas = fields.Date(string="Fecha entrega cenizas")
    ds_sucursal_q_entreg_cenizas = fields.Many2one(
        "ds.sucursal.qentreg.cenizas", string="Sucursal que entrega cenizas")
    ds_aplica_seguro = fields.Many2one("ds.aplica.seguro", string="Aplica seguro")
    ds_fecha_de_falleci = fields.Date(string="Fecha de fallecimiento")
    ds_ataud = fields.Many2one("ds.ataud", string="Ataúd")
    ds_urna = fields.Many2one("ds.urna", string="Urna")

    psa_servi_adicionals = fields.Char(string="Servicios adicionales")
    psa_costo_paquete = fields.Float(string="Costo paquete")
    psa_ataud_o_cambio = fields.Float(string="Ataud o cambio")
    psa_cremacion = fields.Float(string="Cremación")
    psa_capilla_recinto = fields.Float(string="Capilla recinto")
    psa_traslado = fields.Float(string="Traslado ")
    psa_camion = fields.Float(string="Camión")
    psa_otros = fields.Float(string="Otros")
    psa_saldo_PABS = fields.Float(string="Saldo PABS")
    psa_embalsamado = fields.Float(string="Embalsamado")
    psa_capilla_domicilio = fields.Float(string="Capilla domicilio")
    psa_cafeteria = fields.Float(string="Cafetería")
    psa_tramites = fields.Float(string="Trámites")
    psa_certificado = fields.Float(string="Certificado")

    contact_1_nomb = fields.Char(string="Nombre")
    contact_1_tel = fields.Char(string="Teléfono")
    contact_1_relacion_confinad = fields.Many2one(
        "relacion.confinad", string="Relación con finado")
    contact_2_nomb = fields.Char(string="Nombre")
    contact_2_tel = fields.Char(string="Teléfono")
    contact_2_relacion_confinad = fields.Many2one(
        "relacion.confinad", string="Relación con finado")
    podp_nomb = fields.Char(string="Nombre")
    # podp_municipio = fields.Char(string="municipio")
    podp_municipio_id = fields.Many2one('res.locality', string="Municipio", ondelete='restrict')
    # podp_colonia = fields.Many2one("colonias", string="Colonia")
    podp_colonia_id = fields.Many2one(
        'colonias',
        string="Colonia",
        ondelete='restrict',
        domain="[('municipality_id', '=', podp_municipio_id)]"
    )
    podp_calle_y_number = fields.Char(string="Calle y #")
    podp_tel = fields.Char(string="Teléfono")
    podp_relacion_confinad = fields.Many2one(
        "relacion.confinad", string="Relación con finado")

    iv_lugar_de_velacion = fields.Many2one(
        "iv.lugar.velacion", string="Lugar de velación")
    iv_nombre_de_capilla = fields.Many2one(
        "iv.nombre.capilla", string="Nombre de capilla")
    iv_fecha_de_inicio = fields.Date(string="Fecha de inicio")
    iv_hora_de_inicio = fields.Float(string="Hora de inicio")
    iv_direccion = fields.Text(string="Dirección")

    dc_saldo_conveniado = fields.Float(string="Saldo conveniado")
    dc_fecha_de_inicio = fields.Date(string="Fecha de inicio")
    dc_realiza_convenio = fields.Many2one(
        "ds.atiende.servicio", string="Realiza convenio")
    dc_cantidad_de_pagos = fields.Integer(string="Cantidad de pagos")
    dc_forma_de_pago = fields.Many2one("dc.forma.pago", string="Forma de pago")

    ir_operativo_1 = fields.Many2one("ir.operativo", string="Operativo 1")
    ir_operativo_2 = fields.Many2one("ir.operativo", string="Operativo 2")
    ir_carroza = fields.Many2one("carroza", string="Carroza")
    ir_fecha_de_inicio = fields.Date(string="Fecha de inicio")
    ir_hora_de_inicio = fields.Float(string="Hora de inicio")
    ir_fecha_de_fin = fields.Date(string="Fecha de fin")
    ir_hora_de_fin = fields.Float(string="Hora de fin")

    ic_operativo_1 = fields.Many2one("ir.operativo", string="Operativo 1")
    ic_operativo_2 = fields.Many2one("ir.operativo", string="Operativo 2")
    ic_carroza = fields.Many2one("carroza", string="Carroza")
    ic_fecha_de_inicio = fields.Date(string="Fecha de inicio")
    ic_hora_de_inicio = fields.Float(string="Hora de inicio")
    ic_fecha_de_fin = fields.Date(string="Fecha de fin")
    ic_hora_de_fin = fields.Float(string="Hora de fin")

    ii_operativo_1 = fields.Many2one("ir.operativo", string="Operativo 1")
    ii_operativo_2 = fields.Many2one("ir.operativo", string="Operativo 2")
    ii_carroza = fields.Many2one("carroza", string="Carroza")
    ii_fecha_de_inicio = fields.Date(string="Fecha de inicio")
    ii_hora_de_inicio = fields.Float(string="Hora de inicio")
    ii_fecha_de_fin = fields.Date(string="Fecha de fin")
    ii_hora_de_fin = fields.Float(string="Hora de fin")

    ig_entrego_ropa = fields.Many2one("ig.entrego.ropa", string="Entregó ropa")
    ig_proveedor_embalsama = fields.Many2one(
        "ig.proveedor.embalsama", string="Proveedor embalsama")
    ig_templo = fields.Many2one("ig.templo", string="Templo")
    ig_hora_de_misa = fields.Float(string="Hora de misa")
    ig_acta_de_defuncion = fields.Char(string="Acta de defunción")
    ig_panteon = fields.Char(string="Panteón")

    cremation_id = fields.Many2one(comodel_name='mortuary.cremation',
        string='Lugar de Cremación')

    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, default=lambda self: self.env.company)
    revisado = fields.Many2one("ii.llamada", string="Llamada")

    revisado_admin = fields.Selection([
        ('si', 'SI'),
        ('no', 'NO'),
    ],
        string='Revisado por administración',
    )

    employee_id = fields.Many2one(
        'hr.employee',
        string='Cobrador',
        domain=[
            ('job_id.name', '=ilike', 'cobrador'),
        ]
    )

    currency_id = fields.Many2one(string='Moneda', 
        readonly=True,
        related='company_id.currency_id')

    id_contrato = fields.Many2one(comodel_name="pabs.contract", string="Contrato PABS")

    # Al seleccionar un contrato por ID actualiza los campos "numero de contrato" y "nombre de titular"
    @api.onchange('id_contrato')
    def _onchange_tc_no_contrato(self):
        for rec in self:
            if rec.id_contrato:
                rec.tc_no_contrato = rec.id_contrato.name
                rec.tc_nomb_titular = rec.id_contrato.full_name

    def _calc_balance(self):
        move_obj = self.env['account.move']
        for rec in self:
            move_ids = move_obj.search([
                ('state','=','posted'),
                ('type','=','out_invoice'),
                ('mortuary_id','=',rec.id)])
            balance = sum(move_ids.mapped('amount_residual'))
            rec.balance = balance

    def _calc_total_invoiced(self):
        move_obj = self.env['account.move']
        for rec in self:
            move_ids = move_obj.search([
                ('type','=','out_invoice'),
                ('mortuary_id','=',rec.id)])
            total_invoiced = sum(move_ids.mapped('amount_total'))
            rec.total_invoiced = total_invoiced

    def action_get_invoices(self):
        context = dict(self.env.context or {})
        context.update({'default_partner_id' : self.partner_id})
        context.update(create=False)
        act_window = self.env.ref('account.action_move_out_invoice_type').read()[0]
        act_window.update({
            'domain' : [('mortuary_id','=',self.id)],
            'context' : context})
        return act_window
        """raise ValidationError("valor : {}".format(act_window))
        return {
            'name': 'Consulta de Facturas',
            'type': 'ir.actions.act_window',
            'view_type': 'tree,form',
            'view_mode': 'form',
            'res_model': 'account.move',
            'view_id': self.env.ref('account.view_invoice_tree').id,
            'domain' : [('mortuary_id','=',self.id)],
            'context' : context
        }"""


    @api.constrains('cs_tel', 'contact_1_tel', 'contact_2_tel', 'podp_tel')
    def check_phone_number(self):
        print('------------------------------check_phone_number---------------------------------')
        for obj in self:
            if obj.cs_tel:
                if obj.cs_tel.isdigit() is False:
                    raise UserError(_("El campo teléfono debe de ser numérico"))

            if obj.contact_1_tel:
                if obj.contact_1_tel.isdigit() is False:
                    raise UserError(_("El campo teléfono debe de ser numérico"))

            if obj.contact_2_tel:
                if obj.contact_2_tel.isdigit() is False:
                    raise UserError(_("El campo teléfono debe de ser numérico"))

            if obj.podp_tel:
                if obj.podp_tel.isdigit() is False:
                    raise UserError(_("El campo teléfono debe de ser numérico"))

    @api.model
    def create(self, vals):
        partner_obj = self.env['res.partner']
        vals['ii_hora_creacion'] = datetime.now(tz).strftime('%H:%M')
        if vals['name']:
            partner_id = partner_obj.create({'name' : vals['name']})
            ### BUSCAMOS LA CUENTA CONTABLE PARA LAS BITACORAS
            account_id = self.env.company.mortuary_account_id
            ### SI EXISTE LA CUENTA CONFIGURADA EN LA COMPAÑIA
            if account_id:
                ### SOBREESCRIBIMOS AL CLIENTE POR LA CUENTA DE LAS BITACORAS
                partner_id.write({
                    'property_account_receivable_id' : account_id.id or False
                })
            vals.update({'partner_id' : partner_id.id})
        result = super(Mortuary, self).create(vals)
        return result

    def btn_edo_cuenta(self):
        return {
            'type': 'ir.actions.report',
            'report_type': 'qweb-pdf',
            'report_name': 'mortuary.estado_cuenta2',
            'report_file': 'mortuary.estado_cuenta2',
        }

    def btn_tarjeta(self):
        return {
            'type': 'ir.actions.report',
            'report_type': 'qweb-pdf',
            'report_name': 'mortuary.carnet_pago2',
            'report_file': 'mortuary.carnet_pago2',
        }

    def btn_cgs(self):
        return {
            'type': 'ir.actions.report',
            'report_type': 'qweb-pdf',
            'report_name': 'mortuary.cgs',
            'report_file': 'mortuary.cgs',
        }

    def btn_convenio(self):
        self.ensure_one()
        form_view_id = self.env.ref(
            'mortuary.wizard_view_form').id
        model_convenio = self.env['convenio'].search(
            [('bitacora_id', '=', self.id)], limit=1)
        if len(model_convenio) == 1:
            action = {
                'type': 'ir.actions.act_window',
                'views':
                [
                    (form_view_id, 'form'),
                ],
                'view_mode': 'form',
                'name': 'Convenio de bitacora',
                'view_type': 'form',
                'res_model': 'convenio',
                'target': "new",
                'res_id': model_convenio.id
            }
            return action
        else:
            action = {
                'type': 'ir.actions.act_window',
                'views':
                [
                    (form_view_id, 'form'),
                ],
                'view_mode': 'form',
                'name': 'Convenio de bitacora',
                'view_type': 'form',
                'res_model': 'convenio',
                'target': "new",
                'context': {
                    'default_bitacora_id': self.id,
                },
            }
            return action

    def btn_bsf(self):
        return {
            'type': 'ir.actions.report',
            'report_type': 'qweb-pdf',
            'report_name': 'mortuary.bsf',
            'report_file': 'mortuary.bsf',
        }
        # var action = {
        #     'type': 'ir.actions.report',
        #     'report_type': 'qweb-pdf',
        #     'report_name': this.report_name,
        #     'report_file': this.report_file,
        #     'data': this.data,
        #     'context': this.context,
        #     'display_name': this.title,
        # };

    # def btn_servic_pendiet(self):
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': 'Bitacoras pendientes',
    #         'view_mode': 'tree,form',
    #         'res_model': 'mortuary',
    #         'domain': [('ii_servicio', '=', 'PENDIENTE')],
    #         'context': "{'create': False}"
    #     }

    def get_convenio_pagos(self):
        for rec in self:
            model_pagos = self.env['convenio.pagos.line'].search(
                [('bitacor_id', '=', rec.id)])
            return model_pagos

    @api.onchange('podp_municipio_id')
    def _onchange_podp_municipio_id(self):
        if self.podp_municipio_id and self.podp_municipio_id != self.podp_colonia_id.municipality_id:
            self.podp_colonia_id = False

    def btn_add_nuev_coment(self):
        # cs_observacions
        if self.cs_nuevo_comentario:
            dicc = {
                'name': self.cs_nuevo_comentario,
                'bitacor_id': self.id,
                'hora_creacion': "{}:{}".format(datetime.now().hour - 6, datetime.now().minute)
            }
            self.env['observaciones'].create(dicc)
            self.cs_nuevo_comentario = ''

    def get_comentarios(self):
        for rec in self:
            comentarios = ''
            model_comnetarios = self.env['observaciones'].search(
                [('bitacor_id', '=', rec.id)], order='create_date desc')
            for com in model_comnetarios:
                comentarios += "{} {} {}: {} {}".format(com.fecha_creacion, com.hora_creacion, com.id_user.name, com.name, '\n')
            rec.cs_observacions = comentarios

    def btn_create_facturas(self):
        ctx = {
            'default_type': 'out_invoice',
            'default_company_id' : self.env.company.id,
            'default_mortuary_id' : self.id}
        if self.partner_id:
            ctx.update({'default_partner_id' : self.partner_id.id})
        return {
            'name': 'Crear Factura',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'account.move',
            'view_id': self.env.ref('account.view_move_form').id,
            'context': ctx
        }

    def btn_create_pagos(self):
        journal_id = self.env.company.mortuary_journal
        if journal_id:
            journal_name = journal_id.id
        else:
            journal_name = False
        return {
            'name': 'Crear pagos',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'account.payment',
            'view_id': self.env.ref('pabs_custom.mortuary_account_payment_form_view').id,
            'context': {
                'default_balance_binnacle' : self.balance,
                'default_date_of_death' : self.ds_fecha_de_falleci,
                'default_place_of_death' : self.ii_lugar_fallec,
                'default_journal_id' : journal_name,
                'default_binnacle' : self.id,
                'default_partner_id' : self.partner_id.id,
                'default_reference' : 'payment_mortuary',
                'default_payment_type': 'inbound',
            }
        }

    def get_invoiced_services(self):
        move_obj = self.env['account.move']
        data = []
        move_ids = move_obj.search([
            ('type','=','out_invoice'),
            ('mortuary_id','=',self.id)])
        for move_id in move_ids:
            for line in move_id.invoice_line_ids:
                data.append({
                    'pricelist' : "${:,.2f}".format(line.price_subtotal),
                    'name' : line.name,
                })
        return data

    def get_payments(self):
        payment_obj = self.env['account.payment']
        move_obj = self.env['account.move']
        data = []
        payment_ids = payment_obj = payment_obj.search([
            ('state','in',('posted','sent','reconciled')),
            ('binnacle','=',self.id)])
        move_ids = move_obj.search([
            ('type','=','out_refund'),
            ('mortuary_id','=',self.id)])
        for payment_id in payment_ids:
            data.append({
                'date' : payment_id.payment_date,
                'name' : payment_id.ecobro_receipt or payment_id.name or '',
                'amount' : "${:,.2f}".format(payment_id.amount or 0),
                'collector' : payment_id.debt_collector_code.name_get() or '',
                'ref' : '',
            })
        for move_id in move_ids:
            data.append({
                'date' : move_id.invoice_date,
                'name' : move_id.name or '',
                'amount' : "${:,.2f}".format(move_id.amount_total or 0),
                'collector' : '',
                'ref' : '',
            })
        data = sorted(data, key=lambda r: r['date'])
        return data

    def write(self, vals):
        ### DECLARACIÓN DE OBJETOS.
        servicio_obj = self.env['ii.servicio']
        contract_obj = self.env['pabs.contract']
        status_obj = self.env['pabs.contract.status']
        reason_obj = self.env['pabs.contract.status.reason']
        ### SI SE MODIFICO EL SERVICIO
        if vals.get('ii_servicio'):
            ### INSTANCIAMOS EL OBJETO
            servicio_id = servicio_obj.browse(vals.get('ii_servicio'))
            ### SI EL SERVICIO ESTA EN ESTATUS TERMINADO
            if servicio_id.name == 'TERMINADO':
                ### BUSCAMOS EL CONTRATO YA SEA SI SE MODIFICO O NO
                contract_name = vals.get('tc_no_contrato') or self.tc_no_contrato or False
                ### SI EXISTE UN CONTRATO
                if contract_name:
                    ### INSTANCIAMOS EL CONTRATO
                    contract_id = contract_obj.search([
                        ('name','=',contract_name)])
                    ### SI NO HAY CONTRATO
                    if not contract_id:
                        ### ENVIAMOS MENSAJE DE ERROR
                        raise ValidationError("No se encontró el contrato: {}".format(contract_name))
                    ### SI EL SALDO DEL CONTRATO ES MAYOR QUE 0
                    if contract_id.balance > 0:
                        ### BUSCAMOS EL ESTATUS ACTIVO
                        status_id = status_obj.search([
                            ('status','=','ACTIVO')])
                        ### BUSCAMOS EL MOTIVO DE REALIZADO POR COBRAR
                        reason_id = reason_obj.search([
                            ('status_id','=',status_id.id),
                            ('reason','=','REALIZADO POR COBRAR')])
                        ### ESCRIBIMOS LOS VALORES EN EL CONTRATO
                        contract_id.write({
                            'contract_status_item' : status_id.id,
                            'contract_status_reason' : reason_id.id,
                            'service_detail' : 'made_receivable',
                        })
                    ### SI NO TIENE SALDO
                    else:
                        ### BUSCAMOS EL ESTATUS REALIZADO
                        status_id = status_obj.search([
                            ('status','=','REALIZADO')])
                        ### BUSCAMOS EL MOTIVO DE REALIZADO POR COBRAR
                        reason_id = reason_obj.search([
                            ('status_id','=',status_id.id),
                            ('reason','=','REALIZADO')])
                        ### ESCRIBIMOS LOS VALORES EN EL CONTRATO
                        contract_id.write({
                            'contract_status_item' : status_id.id,
                            'contract_status_reason' : reason_id.id,
                            'service_detail' : 'realized',
                        })
        return super(Mortuary, self).write(vals)

    _sql_constraints = [
        (
            'unique_mortuary_record',
            'UNIQUE(name, company_id)',
            'No se puede crear el registro: ya existe esta bitacora -> [name, company_id]'
        ),
    ]


class Observaciones(models.Model):
    _name = 'observaciones'

    name = fields.Text(string="Nuevo comentario")
    bitacor_id = fields.Many2one(
        "mortuary", string='Bitacora', readonly=True)
    id_user = fields.Many2one(
        'res.users', string='Usuario', default=lambda self: self.env.user.id)
    fecha_creacion = fields.Date(
        string="Fecha creacion", readonly=True, default=fields.Date.today,
        copy=False)
    hora_creacion = fields.Char(
        string="Hora creacion",
        tracking=True,
        readonly=True,
        copy=False)

class AccountMove(models.Model):
    _inherit = 'account.move'

    mortuary_id = fields.Many2one(comodel_name='mortuary',
        name='Bitacora')

class ResCompany(models.Model):
    _inherit = 'res.company'

    legal_representative = fields.Char(string='Apoderado Legal')

    mortuary_journal = fields.Many2one(comodel_name='account.journal',
        string='Diario para funeraria')

    mortuary_account_id = fields.Many2one(comodel_name='account.account',
        string='Cuenta de bitacoras')