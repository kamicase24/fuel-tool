# -*- coding: utf-8 -*-
import logging
import base64
import datetime
import xlrd
from sys import platform
from odoo import models, fields, api, _
_logger = logging.getLogger(__name__)


class FuelTool(models.Model):
    _name = 'fuel.tool'

    def _default_custom_fields(self):
        return self.env['fuel.tool.fields'].search([])

    file = fields.Binary(string='File')
    block_result = fields.Text(string='Resultado')
    report = fields.Many2many('fuel.tool.report', string='Reporte')
    custom_fields = fields.Many2many('fuel.tool.fields', string='Custom Fields', default=_default_custom_fields)

    def generate_xml(self):

        view_ref = self.env['ir.model.data'].get_object_reference('fuel_tool', 'fuel_tool_xml_form')
        view_id = view_ref[1] if view_ref else False

        self.create_xml()

        return {
            'name': 'XML',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'fuel.tool.xml',
            'view_id': view_id,
            'type': 'ir.actions.act_window',
            'target': 'new'
        }

    def import_xlm(self):
        excel = xlrd.open_workbook(file_contents=base64.decodestring(self.file))
        # excel = xlrd.open_workbook('C:\Users\Jesus Rojas\Desktop\Experimento.xlsx')
        _sheet = []
        for sheet in excel.sheets():
            for row in range(sheet.nrows):
                row_list = []
                for col in range(sheet.ncols):
                    value = sheet.cell(row, col).value
                    if sheet.cell(row, col).ctype == 3 and col == 1:
                        xls_date = xlrd.xldate_as_tuple(value, excel.datemode)
                        year, month, day, hour, minute, second = xls_date
                        real_date = datetime.date(year, month, day).strftime('%d/%m/%y')
                        value = real_date

                    elif sheet.cell(row, col).ctype == 3 and col == 2:
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

        self.update_report(_sheet)

        self.block_result = _sheet

    def update_report(self, sheet):

        sql = 'delete from fuel_tool_report'
        self.env.cr.execute(sql)
        i = 0
        fuel_report = self.env['fuel.tool.report']
        for line in sheet:
            if i == 0:
                i = 1
            else:
                fuel_report.create({
                    'token': line[0],
                    'date': line[1],
                    'hour': line[2],
                    'gallons': line[3],
                    'supplier': line[4],
                    'month': line[5],
                    'license_plate': line[6],
                    'kilometer': line[7],
                    'fuel_type': line[8],
                    'prices': line[9],
                    'real_prices': line[10],
                    'inv_prices': line[11],
                    'difference': line[12],
                    'ticket_number': line[13],
                    'responsable': line[14],
                    'location': line[15],
                    'commentary': line[16],
                    'payment_type': line[17],
                    'partner': line[18],
                })

        self.report = fuel_report.search([])

    def create_xml(self):

        fuel_report = self.env['fuel.tool.report'].search([])

        custom_list = []
        for custom_field in self.custom_fields:
            custom_list.append(custom_field.name)
        print custom_list

        template = '<?xml version="1.0" encoding="utf-8"?>\n'
        template += '<Fuel fileid="'+str(datetime.datetime.now())+'">\n'
        for line in fuel_report:
            template += '\t<Refills>\n'
            template += '\t\t<Refill>\n'
            template += '\t\t\t<VehicleID>'+line.token+'</VehicleID>\n'
            template += '\t\t\t<TimeStamp>'+line.date+'T'+line.hour+'</TimeStamp>\n'
            template += '\t\t\t<Volume>'+str(line.gallons)+'</Volume>\n'
            template += '\t\t\t<CustomFields>\n'

            if 'fuel_type' in custom_list:
                template += '\t\t\t\t<CustomField>\n'
                template += '\t\t\t\t\t<CustomFieldName>Tipo de combustible</CustomFieldName>\n'
                template += '\t\t\t\t\t<CustomFieldValue>'+line.fuel_type+'</CustomFieldValue>\n'
                template += '\t\t\t\t</CustomField>\n'

            if 'prices' in custom_list:
                template += '\t\t\t\t<CustomField>\n'
                template += '\t\t\t\t\t<CustomFieldName>Costo del combustible</CustomFieldName>\n'
                template += '\t\t\t\t\t<CustomFieldValue>'+str(line.prices)+'</CustomFieldValue>\n'
                template += '\t\t\t\t</CustomField>\n'

            if 'inv_prices' in custom_list:
                template += '\t\t\t\t<CustomField>\n'
                template += '\t\t\t\t\t<CustomFieldName>Monto de la recarga</CustomFieldName>\n'
                template += '\t\t\t\t\t<CustomFieldValue>'+str(line.inv_prices)+'</CustomFieldValue>\n'
                template += '\t\t\t\t</CustomField>\n'

            if 'commentary' in custom_list:
                template += '\t\t\t\t<CustomField>\n'
                template += '\t\t\t\t\t<CustomFieldName>Comentario</CustomFieldName>\n'
                template += '\t\t\t\t\t<CustomFieldValue>'+line.commentary+'</CustomFieldValue>\n'
                template += '\t\t\t\t</CustomField>\n'

            if 'supplier' in custom_list:
                template += '\t\t\t\t<CustomField>\n'
                template += '\t\t\t\t\t<CustomFieldName>Suplidor</CustomFieldName>\n'
                template += '\t\t\t\t\t<CustomFieldValue>'+line.supplier+'</CustomFieldValue>\n'
                template += '\t\t\t\t</CustomField>\n'

            if 'location' in custom_list:
                template += '\t\t\t\t<CustomField>\n'
                template += '\t\t\t\t\t<CustomFieldName>Localidad</CustomFieldName>\n'
                template += '\t\t\t\t\t<CustomFieldValue>'+line.location+'</CustomFieldValue>\n'
                template += '\t\t\t\t</CustomField>\n'

            if 'ticket_number' in custom_list:
                template += '\t\t\t\t<CustomField>\n'
                template += '\t\t\t\t\t<CustomFieldName>Numero de Ticket</CustomFieldName>\n'
                template += '\t\t\t\t\t<CustomFieldValue>'+line.ticket_number+'</CustomFieldValue>\n'
                template += '\t\t\t\t</CustomField>\n'

            if 'inv_number' in custom_list:
                template += '\t\t\t\t<CustomField>\n'
                template += '\t\t\t\t\t<CustomFieldName>Numero de Factura</CustomFieldName>\n'
                template += '\t\t\t\t\t<CustomFieldValue></CustomFieldValue>\n'
                template += '\t\t\t\t</CustomField>\n'

            if 'payment_type' in custom_list:
                template += '\t\t\t\t<CustomField>\n'
                template += '\t\t\t\t\t<CustomFieldName>Modalidad de pago</CustomFieldName>\n'
                template += '\t\t\t\t\t<CustomFieldValue>'+line.payment_type+'</CustomFieldValue>\n'
                template += '\t\t\t\t</CustomField>\n'

            if 'partner' in custom_list:
                template += '\t\t\t\t<CustomField>\n'
                template += '\t\t\t\t\t<CustomFieldName>Empresa</CustomFieldName>\n'
                template += '\t\t\t\t\t<CustomFieldValue>'+line.partner+'</CustomFieldValue>\n'
                template += '\t\t\t\t</CustomField>\n'

            template += '\t\t\t</CustomFields>\n'
            template += '\t\t</Refill>\n'
            template += '\t</Refills>\n'
        template += '</Fuel>'

        sql = 'delete from fuel_tool_xml'
        self.env.cr.execute(sql)
        sql = "insert into fuel_tool_xml (report) values ('%s')" % template
        self.env.cr.execute(sql)


class FuelToolSheet(models.TransientModel):
    _name = 'fuel.tool.xml'

    def _default_report(self):

        return self.env['fuel.tool.xml'].search([]).report

    report = fields.Text(string='Reporte', default=_default_report)
    binary_xml = fields.Binary(string='Descargar XML')
    binary_string = fields.Char('Descargar XML')

    @api.onchange('report')
    def download_xml(self):
        xml_read = False
        if platform == 'win32':
            xml_write = open('C:\Users\openpgsvc\comp_file.xml', 'w')
            xml_write.write(self.report)
            xml_write.close()
            xml_read = open('C:\Users\openpgsvc\comp_file.xml', 'r')
        elif platform == 'linux2':
            xml_write = open('/home/administrator/comp_file.xml', 'w')
            xml_write.write(self.report)
            xml_write.close()
            xml_read = open('/home/administrator/comp_file.xml', 'r')

        self.write({
            'binary_string': 'fuel_file'+str(datetime.datetime.now().strftime('%d%m%y%H%M%S'))+'.xml',
            'binary_xml': base64.encodestring(xml_read.read())
        })
        return {'type': 'ir.action.do_nothing'}


class FuelToolReport(models.Model):
    _name = 'fuel.tool.report'

    token = fields.Char(string='Ficha', required=True)
    date = fields.Date(string='Día, Mes y Año', required=True)
    hour = fields.Char(string='Hora', required=True)
    gallons = fields.Float(string='Galones', required=True)
    month = fields.Char(string='Mes')
    supplier = fields.Char(string='Suplidor')
    license_plate = fields.Char(string='Placa')
    kilometer = fields.Char(string='Kilometraje')
    fuel_type = fields.Char(string='Combustible')
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


class FuelToolFields(models.Model):
    _name = 'fuel.tool.fields'

    name = fields.Char(string='Nombre')
    custom_name = fields.Char(string='Nombre de titulo')
    category = fields.Selection([('char', 'Caracter'),
                                 ('date', 'Fecha'),
                                 ('time', 'Hora'),
                                 ('integer', 'Número Entero'),
                                 ('float', 'Número Decimal')], string='Catergoria/Tipo')
    sequence = fields.Integer(string='Prioridad')

