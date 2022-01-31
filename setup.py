from importlib_metadata import entry_points
from setuptools import setup, find_packages
import timecard
setup(
    name='E4ETimecard',
    version=timecard.__version__,
    description="E4E Timecard Application",
    author='Nathan Hui',
    author_email='nthui@eng.ucsd.edu',
    packages=find_packages(),
    install_requires=[
        'pyrebase',
        'ipython',
        'pyyaml',
        'appdirs',
        'schema'
    ],
    entry_points={
        'console_scripts': [
            'timecard=e4e_timecard:main'
        ]
    }
)