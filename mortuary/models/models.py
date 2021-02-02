# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import models, fields, api
from datetime import timedelta
# from odoo.exceptions import ValidationError


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
    # [('0', 'ROBERTO GOMEZ PEREZ')],


class DsSucursalVelacion(models.Model):
    _name = 'ds.sucursal.velacion'

    name = fields.Char(string="Nombre")
    # [('0', 'LOPEZ MATEOS')],


class DsTipoServicio(models.Model):
    _name = 'ds.tipo.servicio'

    name = fields.Char(string="Nombre")
    # [('0', 'PLAN')],


class DsCapilla(models.Model):
    _name = 'ds.capilla'

    name = fields.Char(string="Nombre")
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
    # [('0', 'ACAPULCO')],


class DsAplicaSeguro(models.Model):
    _name = 'ds.aplica.seguro'

    name = fields.Char(string="Nombre")
    # [('si', 'Si'),
    # ('no', 'No')],


class DsAtaud(models.Model):
    _name = 'ds.ataud'

    name = fields.Char(string="Nombre")
    # [('0', 'RAMIRO RENTERIA ROBLES')],


class DsUrna(models.Model):
    _name = 'ds.urna'

    name = fields.Char(string="Nombre")
    # [('0', 'RAMIRO RENTERIA ROBLES')],


class RelacionConfinad(models.Model):
    _name = 'relacion.confinad'

    name = fields.Char(string="Nombre")
    # [('0', 'HIJO')],


class PodpCalleYNumber(models.Model):
    _name = 'podp.calle.ynumber'

    name = fields.Char(string="Nombre")
    # [('0', 'MARIANO BARCENA 45')],


class IvLugarVelacion(models.Model):
    _name = 'iv.lugar.velacion'

    name = fields.Char(string="Nombre")
    # [('0', ' CAPILLA ')],


class IvNombreDeCapilla(models.Model):
    _name = 'iv.nombre.capilla'

    name = fields.Char(string="Nombre")
    # [('0', 'ESPERANZA')],


class DcFormaPago(models.Model):
    _name = 'dc.forma.pago'

    name = fields.Char(string="Nombre")
    # [('0', 'SEMANAL')],


class IrOperativo(models.Model):
    _name = 'ir.operativo'

    name = fields.Char(string="Nombre")
    # [('0', 'JUAN MONTES ROSALES')],


class Carroza(models.Model):
    _name = 'carroza'

    name = fields.Char(string="Nombre")
    # [('0', 'JRA5643-300C-NEGRA')],


class IgEntregoRopa(models.Model):
    _name = 'ig.entrego.ropa'

    name = fields.Char(string="Nombre")
    # [('si', 'Si'),
    # ('no', 'No')],


class IgProveedorEmbalsama(models.Model):
    _name = 'ig.proveedor.embalsama'

    name = fields.Char(string="Nombre")
    # [('0', 'REYNALDO')],


class IgTemplo(models.Model):
    _name = 'ig.templo'

    name = fields.Char(string="Nombre")
    # [('0', 'PAULINA RODRIGUEZ GONZALEZ')],#


class IgPanteon(models.Model):
    _name = 'ig.panteon'

    name = fields.Char(string="Nombre")
    # [('0', 'PANTEON MUNICIPAL DE ATOTONILCO')],


class Mortuary(models.Model):
    _name = 'mortuary'
    _description = 'modulo de funeraria'
    _inherit = 'mail.thread'

    name = fields.Char(string="Bitácora", required=True)
    ii_servicio = fields.Many2one("ii.servicio", string="Servicio")
    ii_finado = fields.Char(string="Finado", required=True)
    ii_fecha_creacion = fields.Date(
        string="Fecha creacion", readonly=True, default=fields.Date.today,
        copy=False)
    ii_hora_creacion = fields.Char(
        string="Hora creacion",
        tracking=True,
        readonly=True,
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
    podp_calle_y_number = fields.Many2one("podp.calle.ynumber", string="Calle y #")
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
    ig_panteon = fields.Many2one("ig.panteon", string="Panteón ")

    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, default=lambda self: self.env.company)
    revisado = fields.Many2one("ii.llamada", string="Llamada")
    partner_id = fields.Many2one(comodel_name='res.partner',
        string='Finado')
    balance = fields.Float(string="Saldo", compute="_calc_balance")

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

    @api.model
    def create(self, vals):
        today = fields.Datetime.now() - timedelta(hours=6)
        hours = today.hour
        minutes = today.minute
        vals['ii_hora_creacion'] = "{}:{}".format(hours,minutes)
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
            model_comnetarios = self.env['observaciones'].search(
                [('bitacor_id', '=', self.id)])
            comentarios = ''
            for com in model_comnetarios:
                comentarios += "{} {} {}: {} {}".format(com.fecha_creacion, com.hora_creacion, com.id_user.name, com.name, '\n')
            self.cs_nuevo_comentario = ''
            self.cs_observacions = comentarios

    def get_comentarios(self):
        comentarios = ''
        for rec in self:
            model_comnetarios = self.env['observaciones'].search(
                [('bitacor_id', '=', rec.id)])
            for com in model_comnetarios:
                comentarios += "{} {} {}: {} {}".format(com.fecha_creacion, com.hora_creacion, com.id_user.name, com.name, '\n')
            rec.cs_observacions = comentarios

    def btn_create_facturas(self):
        partner_obj = self.env['res.partner']
        account_obj = self.env['account.move']
        bitacora_name = self.name
        partner_prev = partner_obj.search([
            ('name','=',bitacora_name)])
        if partner_prev:
            partner_id = partner_prev
        else:
            partner_id = partner_obj.create({
                'name' : bitacora_name,
                'ref' : self.ii_finado,
                })
        self.partner_id = partner_id.id
        return {
            'name': 'Crear Factura',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'account.move',
            'view_id': self.env.ref('account.view_move_form').id,
            'context': {
                'default_type': 'out_invoice',
                'default_ref' : self.ii_finado,
                'default_bitacora_id' : self.id,
                'default_partner_id' : partner_id.id,
            }
        }

    def btn_create_pagos(self):
        return {
            'name': 'Crear pagos',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'account.payment',
            'view_id': self.env.ref('account.view_account_payment_form').id,
            'context': {
                'default_payment_type': 'inbound',
            }
        }

    #Obtiene el saldo del contrato sumando el monto pendiente de las facturas
    def _calc_balance(self):
        invoice_obj = self.env['account.move']
        for rec in self:
            invoice_ids = invoice_obj.search([('type','=','out_invoice'),('bitacora_id','=',rec.id)])
            result = sum(invoice_ids.mapped('amount_residual'))
            rec.balance = result


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

    bitacora_id = fields.Many2one(comodel_name='mortuary',
        string='Bitacora')
