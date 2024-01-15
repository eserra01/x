# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, tools
from odoo.exceptions import UserError

class ShowDigitalImagesWizard(models.TransientModel):
    _name = "show.digital.images.wizard"
    _description = "Imagenes contrato digital"
       
    url_ine = fields.Char(string="INE")
    url_comprobante_domicilio = fields.Char(string="Comprobante domicilio")
    url_fachada_domicilio = fields.Char(string="Fachada domicilio")
    url_contrato_reafiliacion = fields.Char(string="Contrato reafilicación")    