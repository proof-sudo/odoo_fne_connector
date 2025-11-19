from odoo import models, fields

class InheritResPartner(models.Model):
    _inherit = 'res.partner'

    templateFne = fields.Selection([
        ('b2b', 'B2B'),
        ('b2f', 'B2F'),
        ('b2g', 'B2G'),
        ('b2c', 'B2C')
    ], string="Type de client", default='b2b',
       help=(
           "B2B : Entreprise/professionnel possédant un NCC\n"
           "B2F : Client à l'international\n"
           "B2G : Institution gouvernementale\n"
           "B2C : Particulier"
       ))

    regimeFiscal = fields.Selection([
        ('tva', 'TVA normal de 18%'),
        ('tvab', 'TVA réduit de 9%'),
        ('tvac', 'TVA exec conv de 0%'),
        ('tvad', 'TVA exec leg de 0%')
    ], string="Régime fiscal", default='tva',
       help=(
           "Régime fiscal du client :\n"
           "TVA normal de 18%\n"
           "TVA réduit de 9%\n"
           "TVA exec conv de 0%\n"
           "TVA exec leg de 0%"
       ))