# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError

import qrcode
from PIL import Image, ImageDraw, ImageFont

from io import BytesIO
from base64 import b64encode, b64decode
#import logging

from base64 import b64decode, b64encode

#_logger = logging.getLogger(__name__)

class EtiquetasQR(models.TransientModel):
  _name = 'etiquetas.qr'
  _description = 'Impresión de etiquetas qr'

  id_producto = fields.Many2one(comodel_name = 'product.product', string='Producto', required = True)
  serie_inicial = fields.Integer(string="Serie inicial")
  serie_final = fields.Integer(string="Serie final")

  #Parametros de la imagen
  qr_border    = fields.Integer(string="qr_border",    default = 4,   required = True)
  qr_box_size  = fields.Integer(string="qr_box_size",  default = 7,   required = True)
  x_imagen     = fields.Integer(string="x_imagen",     default = 9,  required = True)
  y_imagen     = fields.Integer(string="y_imagen",     default = 0, required = True)
  font_size    = fields.Integer(string="font_size",    default = 18,  required = True)
  x_texto      = fields.Integer(string="x_texto",      default = 18,  required = True)
  y_texto      = fields.Integer(string="y_texto",      default = 185, required = True)

  def imprimir(self):

    consulta = """
      SELECT 
        CONCAT(prod.default_code, '|' ,lot.name) as producto
      FROM product_product AS x_prod
      INNER JOIN product_template AS prod ON x_prod.product_tmpl_id = prod.id
      INNER JOIN stock_production_lot AS lot ON x_prod.id = lot.product_id
        WHERE prod.company_id = {}
        AND x_prod.id = {}
        AND CAST(lot.name AS INTEGER) BETWEEN {} AND {}
          ORDER BY CAST(lot.name AS INTEGER)
    """.format(self.env.company.id, self.id_producto.id, self.serie_inicial, self.serie_final)
    
    try:
      self.env.cr.execute(consulta)
    except Exception as e:
      if 'integer' in "{}".format(e):
        raise ValidationError("No se pudo convertir una serie del producto a número. Revise las series del producto.")
      else:
        raise ValidationError("{}".format(e))

    lista_datos = []
    for res in self.env.cr.fetchall():
      lista_datos.append(res[0])

    if not lista_datos:
      raise ValidationError("No se encontraron articulos con el filtro seleccionado")

    lista_imagenes = []

    # Parametros
    qr_border = self.qr_border
    qr_box_size = self.qr_box_size
    x_imagen = self.x_imagen
    y_imagen = self.y_imagen
    font_size = self.font_size
    extra_bottom = font_size + 5
    x_texto = self.x_texto
    y_texto = self.y_texto
    
    for dato in lista_datos:
        # Crear QR
        qr = qrcode.QRCode(
            version = 1,
            box_size = qr_box_size,
            border = qr_border
        )

        qr.add_data(dato)
        qr.make(fit=True)
        img_qr = qr.make_image()

        # Crear imagen en blanco con espacio extra para el texto
        width, height = img_qr.size
        
        fondo = Image.new(img_qr.mode, (width, height + extra_bottom), 1)

        # Pegar QR a la imagen en blanco
        fondo.paste(img_qr, (x_imagen, y_imagen))

        # Añadir texto
        myFont = ImageFont.truetype('DejaVuSans.ttf', font_size)

        typewriter = ImageDraw.Draw(fondo)
        typewriter.text((x_texto, y_texto), dato.replace('|', '-'), 0, myFont)

        # Convertir a base 64
        byte_tool = BytesIO()
        fondo.save(byte_tool, format="PNG")
        fondo64 = b64encode(byte_tool.getvalue())
        lista_imagenes.append(fondo64)

    data = {
      'data': lista_imagenes
    }

    return self.env.ref('pabs_reports.etiquetas_qr_report').report_action(self, data=data)