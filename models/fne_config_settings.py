from odoo import models, fields, api

# Utiliser l'héritage standard pour les écrans de configuration
class FneConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    _name = 'fne.config.settings'

    # En utilisant 'config_parameter', Odoo gère automatiquement la lecture 
    # (get_values) et l'écriture (set_values) dans ir.config_parameter.

    fne_api_key = fields.Char(string="API Key FNE", config_parameter='fne.api_key')
    fne_mode = fields.Selection([
        ('test', 'Test'),
        ('prod', 'Production')
    ], string="Mode", config_parameter='fne.mode', default='test')
    
    # La valeur est stockée comme 'True' ou 'False' dans ir.config_parameter
    fne_auto_send = fields.Boolean(string="Envoi automatique après validation", config_parameter='fne.auto_send', default=False)
    
    fne_test_url = fields.Char(string="URL Test", config_parameter='fne.test_url', default="http://54.247.95.108/ws")
    fne_prod_url = fields.Char(string="URL Production", config_parameter='fne.prod_url', default="https://prod.fne.ci/api")
    point_de_vente= fields.Char(string="Point de Vente", config_parameter='fne.point_de_vente', help="Identifiant du point de vente pour le FNE")
    footer = fields.Html(string="FNE Footer", config_parameter='fne.footer', default="<p> Merci pour votre confiance</p>")

    # Les méthodes set_values et get_values deviennent inutiles avec 'config_parameter', 
    # mais si vous avez une logique additionnelle à exécuter, vous pouvez les laisser.
    # Dans ce cas, nous les supprimons pour la propreté.