from setuptools import setup

setup(
    name='mqthermo',
    version='0.1',
    py_modules=['mqthermo'],
    install_requires=[
        'Click',
        'pudb',
        'logzero',
    ],
    entry_points='''
        [console_scripts]
        mqthermo=mqthermo:cli
    ''',
)
