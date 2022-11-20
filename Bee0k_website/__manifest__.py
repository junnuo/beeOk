# -*- coding: utf-8 -*-
{
    'name': 'Bee0k Website',
    'version': '1.0.1',
    'summary': 'Bee0k Website',
    'description': """
Bee0k Website customisation
""",
    'depends': [
        'portal', 'website', 'website_sale', 'base', 'website_sale_delivery',
    ],
    'data': [
        # views
        'views/portal_template.xml',
        'views/templates.xml',
        'views/partner_views.xml',
        'views/sale_order_views.xml',
        'views/delivery_availability_views.xml',
        'views/website_sale_delivery.xml',
        # datas
        "data/collect_point_data.xml",
        # security
        'security/ir.model.access.csv',
        # wizard
        #reports
    ],
    'qweb': [
    ],
    'test': [
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
