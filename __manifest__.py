# -*- coding: utf-8 -*-
{
    'name': "Virtual Meeting",
    'summary': """
        Online meeting via BigBlueButton""",
    'description': """
    """,
    'author': "Alhaditech",
    'website': "http://www.alhaditech.com",
    'price': 80,
    'currency': 'EUR',
    'license': 'OPL-1',
    'category': 'E-Learning',
    'version': '0.1',
    # any module necessary for this one to work correctly
    'depends': ['base', 'calendar', 'web'],
    'images': ['static/description/virtual_meeting_cover.jpg'],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/template.xml',
        'views/calender_event_view.xml',
        'views/res_config_settings_view.xml',
    ],
    'qweb': [
        'static/xml/template.xml',
    ]
}
