# -*- encoding: utf-8 -*-
###########################################################################################
#
#   Author: PABS (pabsmr.org)
#   Coded by: Mauricio Ruiz (mauricio.ruiz@pabsmr.org)
#
###########################################################################################

from odoo import fields, models, _, api
from odoo.exceptions import UserError
import pymysql
from pymysql.err import ProgrammingError
from pymysql.err import OperationalError
from pymysql.err import InternalError
from datetime import datetime, date, timedelta
# sudo apt-get install python3-pymysql
# pip install PyMySQL


class ResCompany(models.Model):
  _inherit = 'res.company'

  mysql_ip_ebita = fields.Char(string='IP Ebita')
  mysql_port_ebita = fields.Char(string='Puerto Ebita', default='3306')
  mysql_db_ebita = fields.Char(string='BD Ebita')
  mysql_user_ebita = fields.Char(string='Usuario MySQL')
  mysql_pass_ebita = fields.Char(string='Contraseña MySQL')

  journal_id_ebita = fields.Many2one(string='Diario para pólizas de salidas', comodel_name='account.journal')
  coffin_cost_account_ebita = fields.Many2one(string='Cuenta de costos ataúdes', comodel_name='account.account')
  urn_cost_account_ebita = fields.Many2one(string='Cuenta de costos urnas', comodel_name='account.account')
  coffin_stock_account_ebita = fields.Many2one(string='Cuenta de inventario ataúdes', comodel_name='account.account')
  urn_stock_account_ebita = fields.Many2one(string='Cuenta de inventario urnas', comodel_name='account.account')
  analytic_cost_account_id = fields.Many2one(string='Cuenta analítica de costos', comodel_name='account.analytic.account')
  
  set_date = fields.Boolean(string="Especificar fecha", help="Permite especificar una fecha para la cual se creará la póliza, este campo solo debe seleccionarse cuando se ejecuta en modo manual; en modo automático debe permanecer sin seleccionarse.")
  sync_date = fields.Date(string="Fecha", default=fields.Date.today())  

  log_ids = fields.One2many(comodel_name='sync.ebita.log', inverse_name='company_id', string="Log sincronización EBITA", readonly=True)

  def test_mysql_ebita(self):
        try:
            # Abre conexion con la base de datos
            db = pymysql.connect(host=self.mysql_ip_ebita, port=int(self.mysql_port_ebita), db=self.mysql_db_ebita, 
            user=self.mysql_user_ebita, password=self.mysql_pass_ebita)
            cursor = db.cursor()
            cursor.execute("SELECT VERSION();")
            data = cursor.fetchone()
            db.close()
            raise UserError(_("Todo parece correcto. \nVersión de MySQL : {0}".format(data)))
        except OperationalError as e:
            raise UserError(_(str(e)))
        except ProgrammingError as e:
            raise UserError(_(str(e)))

  def create_account_move_ebita(self, company_id=False):
    if company_id:
      company_id = self.browse(company_id)
    else:
      company_id = self   
    #
    try:  
       # Se valida que estén todos los parámetros configurados
      if not company_id.coffin_stock_account_ebita or not company_id.coffin_cost_account_ebita or not company_id.urn_stock_account_ebita or not company_id.urn_cost_account_ebita or not company_id.analytic_cost_account_id or not company_id.journal_id_ebita:
        # Se crea el log con el error de la conexión a MySQL
        vals = {
          'description': "Se solicitó sincronización pero no se han definidio todos los parámetros para crear la póliza contable correctamente.",
          'company_id': company_id.id
        }
        self.env['sync.ebita.log'].create(vals)   
        return True
      # Abre conexion con la base de datos
      db = pymysql.connect(host=company_id.mysql_ip_ebita, port=int(company_id.mysql_port_ebita), db=company_id.mysql_db_ebita, 
      user=company_id.mysql_user_ebita, password=company_id.mysql_pass_ebita, autocommit=True)
      cursor = db.cursor()
      #
      if company_id.set_date:
        start_date = str(company_id.sync_date) + ' 00:00:00'
        end_date = str(company_id.sync_date) + ' 23:59:59'
      else:
        start_date = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d 00:00:00')
        end_date = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d 23:59:59')        
      #       
      cursor.execute("SELECT *,COUNT(id) AS qty FROM salidas_de_articulos_de_inventario WHERE fecha BETWEEN '"+start_date+"' AND '"+end_date+"' GROUP BY articulo ORDER BY articulo ASC;")
      rows = cursor.fetchall()
    except OperationalError as e:
      # Se crea el log con el error de la conexión a MySQL
      vals = {
        'description': str(e),
        'company_id': company_id.id
      }
      self.env['sync.ebita.log'].create(vals)   
      return True
    except ProgrammingError as e:    
      # Se crea el log con el error de la conexión a MySQL
      vals = {
        'description': str(e),
        'company_id': company_id.id
      }
      self.env['sync.ebita.log'].create(vals)     
      db.close()
      return True  
    
    # Si hay registros
    if rows:
      lines = []
        # Lineas de la póliza
      for row in rows:           
        # Si es un ataúd
        if 'AT-' in row[2]:      
          lines.append((0,0,{
            'name': _(''),
            'debit': 0.0,
            'credit': row[4] * row[10],
            'account_id': company_id.coffin_stock_account_ebita.id,
          }))
          lines.append((0,0,{
            'name': _(row[2] + ' (p.u. $' + str(row[4])+')'),
            'debit':  row[4] * row[10],
            'credit': 0.0,
            'account_id': company_id.coffin_cost_account_ebita.id,
            'analytic_account_id': company_id.analytic_cost_account_id.id
          }))
        # Si es una urna
        if 'UR-' in row[2]:
          lines.append((0,0,{
            'name': _(''),
            'debit': 0.0,
            'credit':  row[4] * row[10],
            'account_id': company_id.urn_stock_account_ebita.id,
          }))
          lines.append((0,0,{
            'name': _(row[2] + ' (p.u. $' + str(row[4])+')'),
            'debit':  row[4] * row[10],
            'credit': 0.0,
            'account_id': company_id.urn_cost_account_ebita.id,
            'analytic_account_id': company_id.analytic_cost_account_id.id
          }))   
        #         
      try:
        # Se crea la póliza
        move_row = self.env['account.move'].create({
            'journal_id': company_id.journal_id_ebita.id,
            'ref': 'Costo de venta',
            'line_ids': lines,
            'date': start_date[:10]
        })          
        # Se publica la póliza
        move_row.post()                  
        # Se obtienen los ids de EBITA y se actualizan 
        cursor.execute("SELECT id FROM salidas_de_articulos_de_inventario WHERE fecha BETWEEN '"+start_date+"' AND '"+end_date+"';")
        ids = cursor.fetchall()
        ids_string = ''
        for id in ids:
          ids_string += str(id[0]) + ','
        ids_string = ids_string[0:-1]        
        cursor.execute("UPDATE inventory_receipt_issue set sync = 1 WHERE id IN("+ids_string+");")
        db.close()                
        # Se crea el log con el número de póliza
        vals = {
          'description': u'Se creó la póliza número ' + str(move_row.name) + '\nLos ids actualizados en EBITA son: ' + ids_string,
          'company_id': company_id.id
        }    
        self.env['sync.ebita.log'].create(vals)   
      except Exception as e:
        # Se crea el log 
        txt_lines = ''
        for line in lines:
          txt_lines += str(line) + '\n'
        vals = {
          'description': u'Ocurrió un error al CREAR ó PUBLICAR la póliza, los datos de las lineas de la póliza son: \n' + str(txt_lines) + '\n' + str(e),
          'company_id': company_id.id
        }
        self.env['sync.ebita.log'].create(vals)           
        db.close()
        return True
    #
    else:
      # Se crea el log 
        vals = {
          'description': u'Se solicitó sincronización pero no existen registros para crear la póliza.',
          'company_id': company_id.id
        }        
        self.env['sync.ebita.log'].create(vals)   
        db.close()      
        return True
    return True

  def delete_log_ebita(self):
    for log in self.log_ids:
      if log.description == u'Se solicitó sincronización pero no existen registros para crear la póliza.':
        log.unlink()
    return True