from setuptools import setup

setup(
    name='smartmeter',
    version='0.0.1',
    description='Read p0 port on smart meter and report metric to graphite.',

    author='Johan Bloemberg',
    author_email='mail@ijohan.nl',
    url='https://github.com/aequitas/smartmeter',

    install_requires=['pyserial'],

    py_modules=["smartmeter"],
    entry_points={
        'console_scripts': [
            "smartmeter = smartmeter:main"
        ]
    },
)
