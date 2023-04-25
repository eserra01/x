# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError

class IrActionsReport(models.Model):
  _inherit = 'ir.actions.report'

  def render_any_docs(self, res_ids=None, data=None):

    ### Almacenar campo de monto atrasado del contrato
    if "pabs.contract" in str(self.env[self.model]) and 'atraso' in str(self.report_name):
      con = self.env['pabs.contract'].browse(res_ids[0])
      con.write({'late_amount_stored': con.late_amount})

    return super(IrActionsReport, self).render_any_docs(res_ids, data)