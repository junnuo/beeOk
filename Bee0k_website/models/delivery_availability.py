from odoo import models, fields


class DeliveryAvailability(models.Model):
    _name = 'delivery.availability'
    _description = 'Delivery availability'

    day = fields.Selection([('monday', 'Lundi'), ('tuesday', 'Mardi'), ('wednesday', 'Mercredi'), ('thursday', 'Jeudi'),
                            ('friday', 'Vendredi'), ('saturday', 'Samedi'), ('sunday', 'Dimanche')], string='Jour de la semaine')
    is_available = fields.Boolean(string='Disponible')
    start_hour = fields.Float(string='Début de la plage horaire')
    end_hour = fields.Float(string='Fin de la plage horaire')
    is_take_away = fields.Boolean(string='Disponibilité pour emporter')


class DeliveryAvailabilityZone(models.Model):
    _name = 'delivery.availability.zone'
    _description = 'Delivery availability zone'

    name = fields.Char(string='Nom')
    zip = fields.Char(string='Zip')


class CollectPoint(models.Model):
    _name = "collect.point"
    _description = "Collect Point"

    name = fields.Char(string="Nom du point de collecte")
    description = fields.Text(string="Description à afficher en ligne")


class CollectAvailability(models.Model):
    _name = 'collect.availability'
    _inherit = 'delivery.availability'

    collect_point = fields.Selection([('collect', 'Strofilia'), ('collect2', 'Erasmus')])
    collect_point_id = fields.Many2one("collect.point", string="Point de collecte")
