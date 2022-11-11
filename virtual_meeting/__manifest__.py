# -*- coding: utf-8 -*-
{
    'name': "Virtual Meeting Bigbluebutton",
    'summary': """
        Online meeting via BigBlueButton""",
    'description': """
    """,
    'author': "Alhaditech",
    'website': "http://www.alhaditech.com",
    'license': 'AGPL-3',
    'category': 'E-Learning',
    'version': '0.1',
    # any module necessary for this one to work correctly
    'depends': ['base', 'calendar', 'web'],
    'images': ['static/description/virtual_meeting_cover.jpg'],
    # always loaded
    'external_dependencies': {
        'python': ['pyperclip']
    },
    'data': [
        'views/Scheduler.xml',
        'security/ir.model.access.csv',
        'views/template.xml',
        'views/calender_event_view.xml',
        'views/res_config_settings_view.xml',
    ],
     'assets': {
        'web.assets_frontend': [
            'virtual_meeting/static/scss/ribbon.scss'
        ],
    },
    'qweb': [
        'static/xml/template.xml',
    ]
}
