# -*- coding: utf-8 -*-
import logging
import base64

import datetime
import xlrd
from odoo import models, fields, api, _
_logger = logging.getLogger(__name__)


class FuelTool(models.Model):
    _name = 'fuel.tool'

    file = fields.Binary(string='File')
    block_result = fields.Text(string='Resultado')
    report = fields.Many2many('fuel.tool.report', string='Reporte')

    def import_xlm(self):
        excel = xlrd.open_workbook(file_contents=base64.decodestring(self.file))
        # excel = xlrd.open_workbook('C:\Users\Jesus Rojas\Desktop\Experimento.xlsx')
        _sheet = []
        for sheet in excel.sheets():
            for row in range(sheet.nrows):
                row_list = []
                for col in range(sheet.ncols):
                    value = sheet.cell(row, col).value
                    if sheet.cell(row, col).ctype == 3 and col == 2:
                        xls_date = xlrd.xldate_as_tuple(value, excel.datemode)
                        year, month, day, hour, minute, second = xls_date
                        real_date = datetime.date(year, month, day).strftime('%d/%m/%y')
                        value = real_date

                    elif sheet.cell(row, col).ctype == 3 and col == 3:
                        if value > 0 and value < 1:
                            xls_date = xlrd.xldate_as_tuple(value, excel.datemode)
                            year, month, day, hour, minute, second = xls_date
                            real_date = datetime.time(hour, minute, second).strftime('%H:%M:%S')
                            value = real_date
                        else:
                            xls_date = xlrd.xldate_as_tuple(0.0, excel.datemode)
                            year, month, day, hour, minute, second = xls_date
                            real_date = datetime.time(hour, minute, second).strftime('%H:%M:%S')
                            value = real_date
                    row_list.append(value)
                _sheet.append(row_list)

        # [u'Item', u'Mes', u'Fecha', u'Hora', u'Suplidor', u'Ficha', u'Placa', u'Kilometraje', u'Galones', u'Combustible', u'Precio', u'Precio Real', u'Precio Factura', u'Diferencia', u'# Ticket', u'Responsable', u'Oficina', u'Comentario', u'Observacion', u'Empresa']
        # [2.0, u'Enero', '01/02/17', '08:00:00', u'Mazara Comercial & Asocs. S.R.L.', 201.0, 281017.0, 130300.0, 6.0, u'Gasolina Regular', 195.2, 1171.1999999999998, 1171.0, 0.1999999999998181, 8366.0, u'felix sanchez', u'comercial san pedro de macoris', u'', u'tarjeta', u'DANAKY']
        self.update_report(_sheet)

        self.block_result = _sheet

    def update_report(self, sheet):

        sql = 'delete from fuel_tool_report'
        self.env.cr.execute(sql)

        i=0
        fuel_report = self.env['fuel.tool.report']
        for line in sheet:
            if i == 0:
                i = 1
            else:
                fuel_report.create({
                    'month': line[1],
                    'date': line[2],
                    'hour': line[3],
                    'supplier': line[4],
                    'token': line[5],
                    'license_plate': line[6],
                    'kilometer': line[7],
                    'gallons': line[8],
                    'fuel_type': line[9],
                    'prices': line[10],
                    'real_prices': line[11],
                    'inv_prices': line[12],
                    'difference': line[13],
                    'ticket_number': line[14],
                    'responsable': line[15],
                    'location': line[16],
                    'commentary': line[17],
                    'payment_type': line[18],
                    'partner': line[19],
                    # 'partner': line[20],
                })

        self.report = fuel_report.search([])


class FuelToolSheet(models.TransientModel):
    _name = 'fuel.tool.sheet'

    report = fields.Many2one('fuel.tool.report', string='Reporte')


class FuelToolReport(models.Model):
    _name = 'fuel.tool.report'

    # [u'Item', u'  Mes', u'Fecha', u'Hora', u'Suplidor', u'Ficha', u'Placa', u'Kilometraje', u'Galones', u'Combustible', u'Precio', u'Precio Real', u'Precio Factura', u'Diferencia', u'# Ticket', u'Responsable', u'Oficina', u'Comentario', u'Observacion', u'Empresa']
    month = fields.Char(string='Mes')
    date = fields.Date(string='Día, Mes y Año')
    hour = fields.Char(string='Hora')
    supplier = fields.Char(string='Suplidor')
    token = fields.Char(string='Ficha')
    license_plate = fields.Char(string='Placa')
    kilometer = fields.Char(string='Kilometraje')
    gallons = fields.Float(string='Galones')
    fuel_type = fields.Char(string='Combustible')
    # fuel_type = fields.Selection([('Gasolina Regular', 'Gasolina Regular'),
    #                               ('Gasoil Regular', 'Gasoil Regular'),
    #                               ('Gasolina Premium', 'Gasolina Premium'),
    #                               ('Gasoil Premium', 'Gasoil Premium')], string='Combustible')
    prices = fields.Float(string='Precios')
    real_prices = fields.Float(string='Precios Reales')
    inv_prices = fields.Float(string='Precios Facturados')
    difference = fields.Float(string='Diferencia')
    ticket_number = fields.Char(string='Ticket #')
    responsable = fields.Char(string='Responsable')
    location = fields.Char(string='Oficina')
    commentary = fields.Text(string='Comentario')
    payment_type = fields.Char(string='Tipo de Pago')
    partner = fields.Char(string='Empresa')
    brigade = fields.Char(string='Brigada')
    # payment_type = fields.Selection([('credito', 'Credito'), ('tarjeta', 'Tarjeta')], string='Tipo de Pago')
    # partner_id = fields.One2Many('res_partner', string='Empresa', domain='[("customer","=",True)]')
