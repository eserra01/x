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

class CreateMoveEbitaWizard(models.TransientModel):
    _name = 'create.move.ebita.wizard'
    _description = 'Generar póliza de urnas y ataúdes'

    def _default_date(self):
        return fields.Date.context_today(self)
  
    sync_date = fields.Date(string="Fecha", default=_default_date)
    info = fields.Char(string="", default="")
    flag = fields.Boolean(string="")
    line_ids = fields.One2many(string="Existencias en Ebita", comodel_name='create.move.ebita.wizard.line', inverse_name='wizard_id')

    @api.onchange('sync_date')
    def _onchange_sync_date(self):
        if self.sync_date:
            self.line_ids = False
            self.flag = False
        

    def get_lines(self):
        #
        try:    
            company_id = self.env.company             
            # Abre conexion con la base de datos
            db = pymysql.connect(host=company_id.mysql_ip_ebita, port=int(company_id.mysql_port_ebita), db=company_id.mysql_db_ebita, 
            user=company_id.mysql_user_ebita, password=company_id.mysql_pass_ebita, autocommit=True)
            cursor = db.cursor()
                    
            start_date = (self.sync_date).strftime('%Y-%m-%d 00:00:00')
            end_date = (self.sync_date).strftime('%Y-%m-%d 23:59:59')            
            #                  
            # qry = """
            # SELECT * FROM salidas_de_articulos_de_inventario_odoo 
            # WHERE fecha_de_captura BETWEEN '{}' AND '{}'   
            # ORDER BY codigo ASC;
            # """.format(start_date,end_date)

            qry = """
            SELECT * FROM salidas_de_articulos_de_inventario_odoo 
            WHERE fecha_de_captura < '{}' 
            ORDER BY codigo ASC;
            """.format(end_date)

            cursor.execute(qry)
            rows = cursor.fetchall()
            #
            self.line_ids = False
            for row in rows:
                vals = {
                    'id_doc': row[0],
                    'bitacora': row[2],
                    'codigo': row[3],
                    'serie': row[4],
                    'fecha': row[5],
                    'cod_almacen': row[6],
                    'almacen': row[7],
                    'servicio': row[9],
                    'wizard_id': self.id,
                }    
                self.env['create.move.ebita.wizard.line'].create(vals)
     
        except OperationalError as e:
            raise UserError(str(e))
        except ProgrammingError as e:             
            db.close()
            raise UserError(str(e))
        
        # Se devuelven los resultados 
        if rows:
            self.info = "<span style='color:blue;'/>Se encontraron los siguientes registros en EBITA para procesar.</span>"
            self.flag = True
        else:
            self.info = "<span style='color:red;'/>No encontraron registros en EBITA para procesar.</span>"
            self.flag = False
        return {
                'name':"Registros en EBITA",
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': False,
                'res_model': 'create.move.ebita.wizard',
                'domain': [],
                'type': 'ir.actions.act_window',
                'target': 'new',
                'res_id': self.id,
        }
        return

    def create_move(self):        
        # Se eejcuta el método para la craeción de pólizas
        self.env.company.create_account_move_ebita(self.env.company.id, self.sync_date)
        #
        log_id = self.env['sync.ebita.log'].search([], order='id desc', limit=1)
        if log_id:
            self.info = 'Fecha: ' + str(log_id.create_date)[0:19] + '<br/><br/>' + log_id.description
            self.flag = False
            self.line_ids = False
        else:    
            self.info = 'No se encontraron registros.'        
            self.line_ids = False

        return {        
                'name': (""),                        
                'view_type': 'form',        
                'view_mode': 'form',        
                'res_model': 'create.move.ebita.wizard', 
                'res_id': self.id,
                'views': [(False, 'form')],        
                'type': 'ir.actions.act_window',        
                'target': 'new',                    
            }

class CreateMoveEbitaWizardLine(models.TransientModel):
    _name = 'create.move.ebita.wizard.line'
    _description = 'Líneas de urnas y ataúdes'

    id_doc = fields.Char(string="")
    bitacora = fields.Char(string="")
    codigo = fields.Char(string="")
    serie = fields.Char(string="")
    fecha = fields.Char(string="")
    cod_almacen = fields.Char(string="")
    almacen = fields.Char(string="")
    servicio = fields.Char(string="")   
    wizard_id = fields.Many2one(string="wizard", comodel_name='create.move.ebita.wizard') 


    
    