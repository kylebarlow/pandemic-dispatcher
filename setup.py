from setuptools import setup

setup(
    name='pandemic',
    packages=['pandemic'],
    include_package_data=True,
    install_requires=[
        'flask',
        'sqlalchemy',
        'Flask-SQLAlchemy',
        'Flask-Bootstrap',
        'flask-wtf',
        'Flask-Script',
        'wtforms'
    ],
)
