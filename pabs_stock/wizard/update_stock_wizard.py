# -*- coding: utf-8 -*-

from xml.dom import ValidationErr
from odoo import fields, models, api
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError
import pymysql
from pymysql.err import ProgrammingError
from pymysql.err import OperationalError
from pymysql.err import InternalError
from datetime import datetime, date, timedelta

class UpdateStockWizard(models.TransientModel):
    _name = 'update.stock.wizard'
    _description = 'Actualizar Stock de EBITA'
  
    location_id = fields.Many2one(string="Ubicación destino", comodel_name='stock.location', required=True)    
    company_id = fields.Many2one(comodel_name="res.company",string="Compañia",default=lambda self: self.env.company, copy=True, required=True) 
    msg = fields.Char(string="")
    bd_ebita = fields.Selection(
        [
            ('ebita_cue','Cuernavaca'),         

        ], string="Plaza")
    line_ids = fields.One2many(string="Productos", comodel_name='update.stock.wizard.line', inverse_name='wizard_id', )

    def get_stock(self):
        try:
            mysql_ip_ebita = '3.208.145.41'
            mysql_port_ebita = 3306
            mysql_db_ebita = self.bd_ebita
            mysql_user_ebita = 'ebita_consulta'
            mysql_pass_ebita = 'eB1*?a.c0nsul74'

            # Abre conexion con la base de datos
            db = pymysql.connect(host=mysql_ip_ebita, port=mysql_port_ebita, db=mysql_db_ebita, 
            user=mysql_user_ebita, password=mysql_pass_ebita)
            
            cursor = db.cursor()
            qry = """
            SELECT * FROM articulos_de_inventario_actual;
            """
            cursor.execute(qry)
            data = cursor.fetchall()
            line_obj = self.env['update.stock.wizard.line']
            product_obj = self.env['product.product']

            self.line_ids = False
            lines = []
            for d in data:
                # Se busca el producto
                product_id = product_obj.search([('default_code','=',d[1])])
                vals = {
                    'product_ebita': d[0],
                    'cod_ebita': d[1],
                    'lot_ebita': d[2],
                    'location_ebita': d[3],
                    'product_id': product_id.id if product_id else False,
                    'location_id': self.location_id.id,
                    'wizard_id': self.id
                }  
                line_obj.create(vals)
            db.close()
            return {        
                'name': (""),                        
                'view_type': 'form',        
                'view_mode': 'form',        
                'res_model': 'update.stock.wizard', 
                'res_id': self.id,
                'views': [(False, 'form')],        
                'type': 'ir.actions.act_window',        
                'target': 'new',
                'context': {'lines': len(self.line_ids)}    
            }
            # raise UserError(("Todo parece correcto. \nVersión de MySQL : {0}".format(data)))
        except OperationalError as e:
            raise UserError(_(str(e)))
        except ProgrammingError as e:
            raise UserError(_(str(e)))
        return True
    
    def create_stock(self):
        lot_obj = self.env['stock.production.lot']
        pabs_line_obj =  self.env['pabs.stock.picking.line']
        if not self.line_ids:
            raise UserError("No hay lineas para crear")
        #
        
        # Se crea el ajuste
        vals = {
            'picking_type': 'adjust',
            'origin_location_id': self.location_id.id,
            'company_id': self.env.company.id                
        }
        pabs_stock_id = self.env['pabs.stock.picking'].create(vals)
        for line in self.line_ids:
            # Se busca el lote 
            lot_id = lot_obj.search(
            [
                ('name','=',line.lot_ebita),
                ('product_id','=',line.product_id.id),
                ('company_id','=',self.env.company.id),
            ])
            if not lot_id:
                vals = {
                    'name': line.lot_ebita,
                    'product_id': line.product_id.id,  
                    'company_id': self.env.company.id                      
                }           
                # Se crea el lote            
                lot_id = lot_obj.create(vals)        

            # Se crean las lineas del ajuste                      
            pabs_line_obj.create(
            {
                'pabs_picking_id': pabs_stock_id.id, 
                'product_id': line.product_id.id, 
                'qty': 1,         
                'prod_lot_id': lot_id.id,                          
            })   
        # Se confirma el ajuste     
        # pabs_stock_id.action_done()
        return
    
class UpdateStockWizardLine(models.TransientModel):
    _name = 'update.stock.wizard.line'
    _description = 'Actualizar Stock de EBITA'
      
    product_ebita = fields.Char(string="Producto (EBITA)")
    cod_ebita = fields.Char(string="Código (EBITA)")
    lot_ebita = fields.Char(string="Serie (EBITA)")
    location_ebita = fields.Char(string="Ubicación (EBITA)")    
    product_id = fields.Many2one(string="Producto", comodel_name='product.product',)      
    lot_id = fields.Many2one(string="Serie", comodel_name='stock.production.lot',)   
    location_id = fields.Many2one(string="Ubicación", comodel_name='stock.location',)       
    wizard_id = fields.Many2one(comodel_name='update.stock.wizard')

    
    
   
    
   
   