# -*- coding: utf-8 -*-
{
    'name': 'Bee0k Product',
    'version': '1.0.0',
    'summary': 'Bee0k Product',
    'description': """
Bee0k Product customisation
""",
    'depends': [
        'product', 'website_sale_stock',
    ],
    'data': [
        # views
        'views/product_views.xml',
        'views/template.xml',
        # datas
        # security
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
