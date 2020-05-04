from setuptools import setup, find_packages

setup(
    name='third_homework',
    version='1.0',
    packages=find_packages(),
    install_requires = ['click'],
    entry_points = {
    'console_scripts': ['cli=cli.cli:cli']
    }
)