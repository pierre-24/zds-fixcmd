import zds_fixcmd
from setuptools import setup
try:  # for pip >= 10
    from pip._internal.req import parse_requirements
except ImportError:  # for pip <= 9.0.3
    from pip.req import parse_requirements

pkgs = []
dependency_links = []
for pkg in parse_requirements('requirements.txt', session=False):
    if pkg.req:
        pkgs.append(str(pkg.req))

setup(
    name='zds-fixcmd',
    packages=['zds_fixcmd', 'zds_fixcmd.fixes'],
    version=zds_fixcmd.__version__,
    author=zds_fixcmd.__author__,
    author_email=zds_fixcmd.__email__,
    description=zds_fixcmd.__doc__,
    classifiers=[
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3'
    ],
    install_requires=pkgs,
    test_suite='tests',
    python_requires='>=3',
    entry_points={
        'console_scripts': [
            'zds-fixcmd = zds_fixcmd.cmd:main'
        ]
    },
)

