from setuptools import setup

setup(
    name='MicroFlack-Common',
    description='Common MicroFlack classes and functions',
    version='0.1',
    packages=['microflack_common'],
    install_requires=[
        'docker',
        'flask-httpauth',
        'python-etcd',
        'pyjwt'
    ]
)
