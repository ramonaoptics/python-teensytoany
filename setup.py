#!/usr/bin/env python3
import versioneer
from setuptools import setup, find_packages

with open('README.md') as readme_file:
    readme = readme_file.read()

with open('HISTORY.md') as history_file:
    history = history_file.read()

requirements = ['pyserial', ]

test_requirements = ['pytest', ]

setup(
    author="Ramona Optics Inc.",
    author_email='info@ramonaoptics.com',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    python_requires='>=3.6',
    description="A pythonic way to access the teensytoany board",
    install_requires=requirements,
    license="BSD license",
    long_description=readme + '\n\n' + history,
    long_description_content_type='text/markdown',
    include_package_data=True,
    keywords='teensytoany',
    name='teensytoany',
    packages=find_packages(include=['teensytoany']),
    tests_require=test_requirements,
    url='https://github.com/ramonaoptics/teensytoany',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    zip_safe=False,
)
