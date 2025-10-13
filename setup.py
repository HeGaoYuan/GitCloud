#!/usr/bin/env python3
"""
Setup script for GitCloud CLI
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = ""
if readme_file.exists():
    with open(readme_file, encoding='utf-8') as f:
        long_description = f.read()

# Read dependencies
install_requires = [
    'anthropic>=0.18.0',
    'tencentcloud-sdk-python>=3.0.1090',
    'requests>=2.31.0',
]

setup(
    name='gitcloud-cli',
    version='0.1.0',
    description='Intelligent cloud provisioning tool for GitHub projects',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='GitCloud Team',
    author_email='your.email@example.com',
    url='https://github.com/yourusername/gitcloud-cli',
    packages=find_packages(),
    py_modules=['main', 'cleanup'],
    include_package_data=True,
    package_data={
        '': ['banner.txt'],
    },
    install_requires=install_requires,
    python_requires='>=3.8',
    entry_points={
        'console_scripts': [
            'gitcloud=main:main',
        ],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
    ],
    keywords='cloud provisioning github automation devops',
)
