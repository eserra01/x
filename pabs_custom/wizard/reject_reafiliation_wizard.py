from odoo import models, fields, api
from odoo.exceptions import UserError

class RejectReafiliationWizard(models.TransientModel):
    _name = 'reject.reafiliation.wizard'   
    _description = 'Agregar commentario a solicitud'

    lot_id = fields.Many2one(string="Solicitud",comodel_name="stock.production.lot",required=True)
    comments = fields.Char(string="Comentarios", required=True)

    def add_comment(self):
        # Se busca el contrato 
        contract_id = self.env['pabs.contract'].search(
        [
            ('lot_id','=',self.lot_id.id),
            ('company_id','=',self.env.company.id)
        ])
        if not contract_id:
            raise UserError(f"No se encuentra ningún registro asociado a la solicitud {self.lot_id.name}")
        #
        contract_id.comments = contract_id.comments + ' / ' + self.comments if contract_id.comments else self.comments
        return