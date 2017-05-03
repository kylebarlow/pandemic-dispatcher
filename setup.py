from setuptools import setup

setup(
    name='pandemic',
    packages=['pandemic'],
    include_package_data=True,
    install_requires=[
        'flask>=0.12.1',
        'flask-nav',
        'sqlalchemy',
        'Flask-SQLAlchemy',
        'Flask-Bootstrap',
        'flask-wtf',
        'Flask-Script',
        'Flask-nav',
        'wtforms'
    ],
)
