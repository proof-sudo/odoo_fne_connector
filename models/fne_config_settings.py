from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _name = 'fne.config.settings'

    fne_api_key = fields.Char("API Key FNE", store=True)
    fne_mode = fields.Selection([
        ('test', 'Test'),
        ('prod', 'Production')
    ], string="Mode", default='test')
    fne_auto_send = fields.Boolean("Envoi automatique après validation")
    fne_test_url = fields.Char("URL Test", default="http://54.247.95.108/ws")
    fne_prod_url = fields.Char("URL Production", default="https://prod.fne.ci/api")
    point_de_vente= fields.Char("Point de Vente", help="Identifiant du point de vente pour le FNE")
    footer = fields.Html(default="<p> Merci pour votre confiance</p>", string="FNE Footer")

    def set_values(self):
        super().set_values()
        # Utilisation de self (le modèle fne.config.settings) pour l'enregistrement
        params = self.env[self._name].sudo() 
        
        # Enregistrement des paramètres
        params.set_param('fne.api_key', self.fne_api_key or '')
        params.set_param('fne.mode', self.fne_mode or 'test')
        params.set_param('fne.auto_send', 'True' if self.fne_auto_send else 'False')
        params.set_param('fne.test_url', self.fne_test_url or '')
        params.set_param('fne.prod_url', self.fne_prod_url or '')
        
        # ✅ CORRECTION du champ manquant point_de_vente, en utilisant votre modèle
        params.set_param('fne.point_de_vente', self.point_de_vente or '')
        
        params.set_param('fne.footer', self.footer or 'Merci pour votre confiance')

    @api.model
    def get_values(self):
        res = super().get_values()
        
        # Utilisation de self (le modèle fne.config.settings) pour la lecture
        params = self.env[self._name].sudo()
        
        res.update(
            fne_api_key=params.get_param('fne.api_key', ''),
            fne_mode=params.get_param('fne.mode', 'test'),
            # Conversion de la chaîne stockée en booléen
            fne_auto_send=params.get_param('fne.auto_send', 'False') == 'True',
            fne_test_url=params.get_param('fne.test_url', 'http://54.247.95.108/ws'),
            fne_prod_url=params.get_param('fne.prod_url', 'https://prod.fne.ci/api'),
            point_de_vente=params.get_param('fne.point_de_vente', ''),
            footer=params.get_param('fne.footer', '<p> Merci pour votre confiance</p>'),
        )
        return res