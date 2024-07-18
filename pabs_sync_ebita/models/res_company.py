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
  kit_cost_account_ebita = fields.Many2one(string='Cuenta de costos kits', comodel_name='account.account')
  coffin_stock_account_ebita = fields.Many2one(string='Cuenta de inventario ataúdes', comodel_name='account.account')
  urn_stock_account_ebita = fields.Many2one(string='Cuenta de inventario urnas', comodel_name='account.account')
  kit_stock_account_ebita = fields.Many2one(string='Cuenta de inventario kits', comodel_name='account.account')
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

  # test_data:
  # [
  #   [
  #     0,              #'id_documento'
  #     0,              #'id_bitacora'
  #     'CUE24MAY027',  #'bitacora'
  #     'UR-00018',     #'codigo' #URNA LATINOAMERICANA
  #     'UR18-00010',   #'serie'
  #     '',             #'fecha_de_captura'
  #     '',             #'codigo_almacen_de_consumo'
  #     'BODEGA GENERAL', #'almacen_de_consumo'
  #     0,              #'almacen_salida_id'
  #     ''              #'tipo_de_servicio'
  #   ]
  # ]

  def create_account_move_ebita(self, company_id=False, sync_date=False, test_data = []):
    if company_id:
      company_id = self.browse(company_id)
    else:
      company_id = self   
    #
    try:  
       # Se valida que estén todos los parámetros configurados      
      if not company_id.coffin_stock_account_ebita or \
      not company_id.coffin_cost_account_ebita or \
      not company_id.urn_stock_account_ebita or \
      not company_id.urn_cost_account_ebita or \
      not company_id.analytic_cost_account_id or \
      not company_id.kit_stock_account_ebita or \
      not company_id.kit_cost_account_ebita or \
      not company_id.journal_id_ebita:
        # Se crea el log con el error de la conexión a MySQL
        vals = {
          'description': "Se solicitó sincronización pero no se han especificado todos los parámetros para crear la póliza contable correctamente.",
          'company_id': company_id.id
        }
        self.env['sync.ebita.log'].create(vals)   
        return True
      
      if test_data:
        rows = test_data
      else:
        # Abre conexion con la base de datos
        db = pymysql.connect(host=company_id.mysql_ip_ebita, port=int(company_id.mysql_port_ebita), db=company_id.mysql_db_ebita, 
        user=company_id.mysql_user_ebita, password=company_id.mysql_pass_ebita, autocommit=True)
        cursor = db.cursor()
        #
        if company_id.set_date or sync_date:
          #
          if company_id.set_date:
            start_date = str(company_id.sync_date) + ' 00:00:00'
            end_date = str(company_id.sync_date) + ' 23:59:59'
          if sync_date:
            start_date = str(sync_date) + ' 00:00:00'
            end_date = str(sync_date) + ' 23:59:59'
        else:
          today = datetime.today() - timedelta(hours=6)
          start_date = (today - timedelta(days=1)).strftime('%Y-%m-%d 00:00:00')
          end_date = (today - timedelta(days=1)).strftime('%Y-%m-%d 23:59:59')  
    
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
      # No encontrados
      product_not_found = []
      warehouse_not_found = []
      lot_not_found = []
      qty_not_found = []
      binnacle_not_found  =[]
      inventory_ids = []
      # Objetos
      wh_obj = self.env['stock.warehouse']
      lot_obj = self.env['stock.production.lot']
      sq_obj = self.env['stock.quant']
      # Productos para ajsutar
      adjust_product = []
      # Lineas de la póliza
      for row in rows:
        # Se busca el producto
        product_id = self.env['product.product'].search([('default_code','=',row[3]),('company_id','=',company_id.id)], limit=1)
        if product_id:    
          # Si es un kit
          if 'KC-' in row[3]:
            lines.append((0,0,{
              'name': _(''),
              'debit': 0.0,
              'credit':  product_id.list_price,
              'account_id': company_id.kit_stock_account_ebita.id,
            }))
            lines.append((0,0,{
              'name': _(row[3] + ' (p.u. $' + str(product_id.list_price)+')'),
              'debit':  product_id.list_price,
              'credit': 0.0,
              'account_id': company_id.kit_cost_account_ebita.id,
              'analytic_account_id': company_id.analytic_cost_account_id.id
            }))
            continue   
          # Si es un ataúd
          if 'AT-' in row[3]:            
            # Se busca el almacén
            if company_id.name == 'GUADALAJARA':
              warehouse_id = wh_obj.search([('name','=','BUNKER'),('company_id','=',company_id.id)])
            elif company_id.name == 'TOLUCA' and 'DOMICILIO' in str(row[7]):
              warehouse_id = wh_obj.search([('name','=','BODEGA GENERAL'),('company_id','=',company_id.id)])             
            else: 
              warehouse_id = wh_obj.search([('name','=',row[7]),('company_id','=',company_id.id)])
            if warehouse_id:              
              # Se busca la serie
              lot_id = lot_obj.search([('product_id', '=', product_id.id), ('name','=',row[4])])
              if lot_id:
                # Se busca la cantidad disponible
                quant_id = sq_obj.search(
                [
                  ('product_id','=',product_id.id),
                  ('company_id','=',company_id.id),
                  ('location_id','=',warehouse_id.lot_stock_id.id),
                  ('lot_id','=',lot_id.id),
                  ('quantity','>',0)
                ])
                if quant_id:
                  #
                  lines.append((0,0,{
                    'name': _(''),
                    'debit': 0.0,
                    'credit': product_id.list_price,
                    'account_id': company_id.coffin_stock_account_ebita.id,
                  }))
                  lines.append((0,0,{
                    'name': f"{row[3]} (serie: {str(row[4])}, {str(row[2])})",
                    'debit':  product_id.list_price,
                    'credit': 0.0,
                    'account_id': company_id.coffin_cost_account_ebita.id,
                    'analytic_account_id': company_id.analytic_cost_account_id.id
                  }))
                  #
                  adjust_product.append(
                  {
                    'product_id': product_id.id,
                    'lot_id': lot_id.id,
                    'location_id': warehouse_id.lot_stock_id.id,
                    'company_id':company_id.id,
                    'id_documento': row[0],
                    'bitacora': row[2]
                  })
                  continue
                else:
                  qty_not_found.append({'producto': row[3],'serie':row[4], 'almacen': row[7]})
              else:
                lot_not_found.append(row[4])
            else:
              if row[7] not in warehouse_not_found:
                warehouse_not_found.append(row[7])
          # Si es una urna
          if 'UR-' in row[3]:            
            # Se busca el almacén
            if company_id.name == 'GUADALAJARA':
              warehouse_id = wh_obj.search([('name','=','BUNKER'),('company_id','=',company_id.id)])
            else:
              warehouse_id = wh_obj.search([('name','=',row[7])])
            #  
            if warehouse_id:
              # Se busca la serie
              lot_id = lot_obj.search([('product_id', '=', product_id.id), ('name','=',row[4])])
              if lot_id:
                # Se busca la cantidad disponible
                quant_id = sq_obj.search(
                [
                  ('product_id','=',product_id.id),
                  ('company_id','=',company_id.id),
                  ('location_id','=',warehouse_id.lot_stock_id.id),
                  ('lot_id','=',lot_id.id),
                  ('available_quantity','>',0)
                ])
                if quant_id:                  
                  #
                  lines.append((0,0,{
                    'name': _(''),
                    'debit': 0.0,
                    'credit':  product_id.list_price,
                    'account_id': company_id.urn_stock_account_ebita.id,
                  }))
                  lines.append((0,0,{
                    'name': f"{row[3]} (serie: {str(row[4])}, {str(row[2])})",
                    'debit':  product_id.list_price,
                    'credit': 0.0,
                    'account_id': company_id.urn_cost_account_ebita.id,
                    'analytic_account_id': company_id.analytic_cost_account_id.id
                  }))
                  #
                  adjust_product.append(
                  {
                    'product_id': product_id.id,
                    'lot_id': lot_id.id,
                    'location_id': warehouse_id.lot_stock_id.id,
                    'company_id':company_id.id,
                    'id_documento': row[0],
                    'bitacora': row[2]
                  })
                  continue
                else:
                  qty_not_found.append({'producto': row[3],'serie':row[4], 'almacen': row[7]})
              else:
                lot_not_found.append(row[4])
            else:
              if row[7] not in warehouse_not_found:
                warehouse_not_found.append(row[7])            
        else:
          if row[3] not in product_not_found:
            product_not_found.append(row[3])   
      
      
      # Se crea la póliza        
      try:
        # Se crea la póliza
        move_row = self.env['account.move'].create({
            'journal_id': company_id.journal_id_ebita.id,
            'ref': 'Costo de venta',
            'line_ids': lines,
            'date': start_date[:10]
        })          
        # Se publica la póliza
        move_row.action_post()                  
                
        # Baja de atáudes y urnas en la ubicación, lote y producto especificados
        for adjust in adjust_product:
          #
          vals  ={
            'picking_type': 'adjust2',
            'origin_location_id': adjust.get('location_id'),
            'company_id': adjust.get('company_id')
          }
          inventory_id = self.env['pabs.stock.picking'].create(vals)  
          
          # Se agrega el producto al inventario          
          line_id = self.env['pabs.stock.picking.line'].create(
          {
              'pabs_picking_id': inventory_id.id, 
              'product_id': adjust.get('product_id'), 
              'qty': 1,         
              'prod_lot_id': adjust.get('lot_id'),           
          })   
          # Se busca la bitácora
          mortuary_id = self.env['mortuary'].search(
          [
            ('name','=',adjust.get('bitacora')),
            ('company_id','=',adjust.get('company_id'))
          ])
          if mortuary_id:
            line_id.mortuary_id = mortuary_id.id
          else:
            binnacle_not_found.append(adjust.get('bitacora'))
          # Se valida el inventario ORIGEN
          inventory_id.action_done()
          inventory_ids.append(inventory_id)                  
        
        # Se obtienen los ids de EBITA que se actualizan 
        ids_string = ''
        for adjust in adjust_product:
          ids_string += str(adjust.get('id_documento')) + ','                
        ids_string = ids_string[0:-1]        
        qry = """
        UPDATE bitacora_details_appliances_documents set salida_exportada = 1 
        WHERE id IN ({});
        """.format(ids_string)                  
                       
        # Se crea el log con el número de póliza
        description = 'Se creó la póliza número: ' + str(move_row.name) + '\nLos ids actualizados en EBITA son: ' + ids_string + "\n"
        description += 'Los movimientos de baja son: ' + str([inv.name for inv in inventory_ids]) + "\n"
        description += "Productos no encontrados: {}\n".format(product_not_found)
        description += "Almacenes no encontrados: {}\n".format(warehouse_not_found)
        description += "Lotes no encontrados: {}\n".format(lot_not_found)
        description += "Bitácoras no encontradas: {}\n".format(binnacle_not_found)
        description += "Productos sin existencia: {}\n".format(qty_not_found)
        description += "La fecha solicitada fue: {}\n".format(start_date[:10])
        vals = {
          'description': description,
          'company_id': company_id.id
        }    
        self.env['sync.ebita.log'].create(vals)                
        
        if not test_data:
          # Se confirma a EBITA
          cursor.execute(qry)
          db.close()     
      except Exception as e:
        # Se crea el log 
        txt_lines = ''
        for line in lines:
          txt_lines += str(line) + '\n'
        
        description = "{}".format(txt_lines)
        description += "{}\n".format(e)
        description += "Productos no encontrados: {}\n".format(product_not_found)
        description += "Almacenes no encontrados: {}\n".format(warehouse_not_found)
        description += "Lotes no encontrados: {}\n".format(lot_not_found)
        description += "Productos sin existencia: {}\n".format(qty_not_found)
        description += "La fecha solicitada fue: {}\n".format(start_date[:10])
        #
        vals = {
          'description': u'Ocurrió un error al CREAR ó PUBLICAR la póliza: \n' + description,
          'company_id': company_id.id
        }
        self.env['sync.ebita.log'].create(vals) 
                  
        if not test_data:
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
      log.unlink()
    return True