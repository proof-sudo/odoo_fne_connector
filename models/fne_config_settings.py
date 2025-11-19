from odoo import models, fields, api

class FneConfigSettings(models.TransientModel):
    # Hériter de res.config.settings pour conserver l'interface standard
    _inherit = 'res.config.settings'
    _name = 'fne.config.settings'

    # Les champs n'utilisent plus 'config_parameter'
    fne_api_key = fields.Char(string="API Key FNE")
    fne_mode = fields.Selection([
        ('test', 'Test'),
        ('prod', 'Production')
    ], string="Mode", default='test')
    fne_auto_send = fields.Boolean(string="Envoi automatique après validation", default=False)
    fne_test_url = fields.Char(string="URL Test", default="http://54.247.95.108/ws")
    fne_prod_url = fields.Char(string="URL Production", default="https://prod.fne.ci/api")
    point_de_vente= fields.Char(string="Point de Vente", help="Identifiant du point de vente pour le FNE")
    footer = fields.Html(string="FNE Footer", default="<p> Merci pour votre confiance</p>")

    # Lecture explicite des paramètres depuis ir.config_parameter
    @api.model
    def get_values(self):
        res = super().get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        
        res.update(
            fne_api_key=ICPSudo.get_param('fne.api_key', ''),
            fne_mode=ICPSudo.get_param('fne.mode', 'test'),
            fne_auto_send=ICPSudo.get_param('fne.auto_send', 'False') == 'True',
            fne_test_url=ICPSudo.get_param('fne.test_url', 'http://54.247.95.108/ws'),
            fne_prod_url=ICPSudo.get_param('fne.prod_url', 'https://prod.fne.ci/api'),
            point_de_vente=ICPSudo.get_param('fne.point_de_vente', ''),
            footer=ICPSudo.get_param('fne.footer', '<p> Merci pour votre confiance</p>'),
        )
        return res

    # Écriture explicite des paramètres dans ir.config_parameter
    def set_values(self):
        super().set_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        
        ICPSudo.set_param('fne.api_key', self.fne_api_key or '')
        ICPSudo.set_param('fne.mode', self.fne_mode or 'test')
        ICPSudo.set_param('fne.auto_send', 'True' if self.fne_auto_send else 'False')
        ICPSudo.set_param('fne.test_url', self.fne_test_url or '')
        ICPSudo.set_param('fne.prod_url', self.fne_prod_url or '')
        ICPSudo.set_param('fne.point_de_vente', self.point_de_vente or '')
        ICPSudo.set_param('fne.footer', self.footer or 'Merci pour votre confiance')