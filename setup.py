from setuptools import setup

setup(
    name='tesu',
    packages=['tesu'],
    include_package_data=True,
    install_requires=[
        'flask',
        'markdown',
    ],
)
