# -*- coding: utf-8 -*-
{
    'name': 'Bee0k Website',
    'version': '1.0.0',
    'summary': 'Bee0k Website',
    'description': """
Bee0k Website customisation
""",
    'depends': [
        'portal', 'website',
    ],
    'data': [
        # views
        'views/portal_template.xml',
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
