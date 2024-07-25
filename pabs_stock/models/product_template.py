# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_compare, float_is_zero, float_round

class ProductTemplate(models.Model):
    _inherit = 'product.template'


    def write(self, vals):
        #
        for key in vals.keys():
            if key == 'standard_price':
                val = {
                    'cost': vals.get('standard_price'),
                    'product_id': self.id
                }
                self.env['pabs.history.cost'].create(val)                
        return super(ProductTemplate, self).write(vals)

    def _get_virtual_stock(self):
        for rec in self:
            # Si es un kit
            if rec.is_kit:
                qtys = []
                # Para cada producto del kit
                for line in rec.kit_line_ids:
                    qtys.append((line.product_id.qty_available / line.qty) if line.qty > 0 else 0)
                #
                if qtys:
                    sorted_qtys = sorted(qtys)
                    rec.virtual_stock = sorted_qtys[0]
                else:
                    rec.virtual_stock = 0
            else:
                rec.virtual_stock = 0
    
    def virtual2stock(self):  
        #
        if self.virtual_stock_qty <= 0:
            raise ValidationError("Especifique una cantidad mayor que 0 para hacer la conversión del kit.")
        #
        if self.virtual_stock_qty > self.virtual_stock:
            raise ValidationError("Especifique una cantidad menor a la cantidad virtual para hacer la conversión del kit.")
        #
        config_id = self.env['pabs.stock.config'].search(
            [
                ('company_id','=',self.env.company.id),
                ('config_type','=','primary')
            ], limit=1)
        if not config_id:                    
            raise ValidationError('No existe una configuración para el control de almacén.')
        if not config_id.kits_sequence_id:
            raise ValidationError('No se ha especificado la secuencia para la serie de los kits en la configuración primaria.')                  

        # Se valida  que todos los productos tengan existencia en el ORIGEN
        for line in self.kit_line_ids:            
            qty_available= line.product_id.with_context({'location':config_id.central_location_id.id}).qty_available
            if qty_available < line.qty*self.virtual_stock_qty:
                raise ValidationError('El producto {} no tiene existencias suficientes en el origen, solo pueden considerarse {} unidades.'.format(line.product_id.name,qty_available))
            
        # Se obtienen los valores para decrementar existencias de los productos del kit en el ORIGEN
        prod_ids = []
        for p in self.kit_line_ids:
            prod_id = self.env['product.product'].search([('product_tmpl_id','=',p.product_id.id)])
            prod_ids.append(prod_id.id)

        vals  = {
            'name': 'Conversión {} kit de productos ({}) - Decremento'.format(self.env['stock.inventory'].search_count([]) + 1, self.name),
            'location_ids': [(6,0,[config_id.central_location_id.id])],
            'product_ids': [(6,0,prod_ids)],
            'company_id': self.env.company.id
        }   
        inventory_id = self.env['stock.inventory'].create(vals)  
        #  Se agregan los productos con las cantidades     
        for line in self.kit_line_ids:
            prod_id = self.env['product.product'].search([('product_tmpl_id','=',line.product_id.id)])
            prod_ids.append(prod_id.id)
            self.env['stock.inventory.line'].create(
            {
                'inventory_id': inventory_id.id, 
                'product_id':  prod_id.id, 
                'product_qty': prod_id.with_context({'location': config_id.central_location_id.id}).qty_available - line.qty * self.virtual_stock_qty,                    
                'prod_lot_id': False,
                'location_id': config_id.central_location_id.id
            })   
        # Se valida el inventario ORIGEN
        inventory_id.action_start()
        inventory_id.action_validate()

        # Se obtienen los valores para incrementar existencias del kit en el ORIGEN  
        prod_ids = []
        for p in self:
            prod_id = self.env['product.product'].search([('product_tmpl_id','=',p.id)])
            prod_ids.append(prod_id.id)    

        vals  = {
            'name': 'Conversión {} kit de productos ({}) - Incremento'.format(self.env['stock.inventory'].search_count([]) + 1, self.name),
            'location_ids': [(6,0,[config_id.central_location_id.id])],
            'product_ids': [(6,0,prod_ids)],
            'company_id': self.env.company.id
        }   

        # Se crea el inventario   
        inventory_id = self.env['stock.inventory'].create(vals)  
        #  Se agregan los productos con las cantidades     
        spl_obj = self.env['stock.production.lot']       
        prod_id = self.env['product.product'].search([('product_tmpl_id','=',self.id)])
        #
        for i in range(self.virtual_stock_qty):          
            # Se crea el lote 
            lot_id = spl_obj.create({'name':config_id.kits_sequence_id._next(),'product_id':prod_id.id,'company_id': self.env.company.id})
            self.env['stock.inventory.line'].create(
            {
                'inventory_id': inventory_id.id, 
                'product_id':   prod_id.id, 
                'product_qty': 1,
                'prod_lot_id': lot_id.id,
                'location_id': config_id.central_location_id.id
            })   
        # Se valida el inventario ORIGEN
        inventory_id.action_start()
        inventory_id.action_validate()
        self.virtual_stock_qty = 0
        return True

    pabs_stock_product = fields.Boolean(string='Control del almacén PABS')
    is_kit = fields.Boolean(string="Es un kit")
    virtual_stock = fields.Integer(string="Cantidad virtual",compute=_get_virtual_stock)
    virtual_stock_qty = fields.Integer(string="Cantidad a convertir", )
    kit_line_ids = fields.One2many(string="Productos del kit", comodel_name='pabs.product.kit', inverse_name='product_product_id')
    history_cost_ids = fields.One2many(string="Hisotrial de costo", comodel_name='pabs.history.cost', inverse_name='product_id')
    

class PabsProductKit(models.Model):
    _name = 'pabs.product.kit'
    _description = "Kits"

    product_id = fields.Many2one(string="Producto", comodel_name='product.template', required=True, domain="[('type','=','product'),('pabs_stock_product','=',True),('is_kit','=',False)]")
    qty = fields.Float(string='Cantidad', default=1)
    product_product_id = fields.Many2one(string="Producto", comodel_name='product.template')
    company_id = fields.Many2one(comodel_name="res.company",string="Compañia",default=lambda self: self.env.company, copy=True, required=True) 

class PabsHistoryCost(models.Model):
    _name = 'pabs.history.cost'
    _description = "Historial de costo"

    product_id = fields.Many2one(string="Producto", comodel_name='product.template', required=True,)
    cost = fields.Float(string='Costo')    


