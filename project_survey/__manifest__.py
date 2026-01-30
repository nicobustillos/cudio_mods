{
    'name': 'Project Survey integration',
    'version': '19.0.1.0.0',
    'category': 'Project',
    'author': 'Nicolas Bustillos',
    'summary': 'Inquire via surveys from project tasks',
    'description': """
        This module integrates Project and Survey modules.
        It allows defining a survey per task stage and sending it to the customer directly from the task.
    """,
    'depends': ['project', 'survey'],
    'data': [
        'views/project_views.xml',
        'views/survey_views.xml',
    ],
    'demo': [
        'data/survey_demo.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
}