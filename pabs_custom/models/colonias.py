# -*- coding: utf-8 -*-
from odoo import models, fields, api


class Colonias(models.Model):
    _name = 'colonias'
    _description = 'colonias'

    name = fields.Char(
        string="Nombre",
        required=True
    )

    municipality_id = fields.Many2one(
        'res.locality',
        string="Municipio",
        required=True
    )
