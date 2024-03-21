# -*- coding: utf-8 -*-

from xml.dom import ValidationErr
from odoo import fields, models, api
from odoo.exceptions import ValidationError



class SetLotsWizard(models.TransientModel):
    _name = 'set.lots.wizard'
    _description = 'Especificar lotes'
  
    product_id = fields.Many2one(string="Producto", comodel_name='product.product',)
    start_serie  = fields.Many2one(comodel_name= 'stock.production.lot', string='Serie inicial', )
    end_serie  = fields.Many2one(comodel_name= 'stock.production.lot', string='Serie final', )  
    qty = fields.Float(string='Cantidad')
    pabs_stock_picking_line_id = fields.Many2one(comodel_name="pabs.stock.picking.line")
    msg = fields.Char(string="")
    
    @api.onchange('start_serie','end_serie')
    def onchange_start_serie(self):
        #             
        for rec in self:                
            if rec.start_serie and rec.end_serie:
                qty = int(rec.end_serie.name) - int(rec.start_serie.name)
                if qty < 0:
                    rec.start_serie = rec.end_serie = False
                    rec.qty = 0                
                else:
                    if qty < rec.pabs_stock_picking_line_id.qty:
                        rec.qty = qty + 1
                        rec.msg = False
                    else:
                        rec.end_serie = False
                        rec.qty = 0      
                        rec.msg = "Seleccione una serie que no rebase la cantidad solicitada."  
    
    def set_lots(self):
        # Validar que la linea agregada no tenga las mismas series que los ya agregados
        for i,line in enumerate(self.pabs_stock_picking_line_id.pabs_picking_id.line_ids,1):        
            if line.product_id.id == self.product_id.id and self.pabs_stock_picking_line_id.id != line.id:                
                #
                for m in range(int(self.start_serie.name),int(self.end_serie.name)+1,1):
                    lotm = str(m).zfill(12)                    
                    for n in range(int(line.start_serie.name),int(line.end_serie.name)+1,1):                        
                        lotn = str(n).zfill(12)
                        if lotm == lotn:
                            raise ValidationError("La serie {} ya fue seleccionada previamente en el producto {} de linea {}.".format(lotn,line.product_id.name,i))
        #
        self.pabs_stock_picking_line_id.qty_done = self.qty
        self.pabs_stock_picking_line_id.start_serie = self.start_serie
        self.pabs_stock_picking_line_id.end_serie = self.end_serie
        return True
   