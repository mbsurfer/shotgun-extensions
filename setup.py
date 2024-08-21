from setuptools import setup, find_packages

with open('README.md', 'r', encoding='utf-8') as ld:
    long_description = ld.read()

setup(
    name='shotgun_extensions',
    author='Ryan Neldner',
    author_email='rneldner@gmail.com',
    description='shotgun_extensions extends the functionality of shotgun_api3 Python package.',
    long_description=long_description,
    version='1.0.0',
    packages=find_packages(),
    url='https://github.com/mbsurfer/shotgun-extensions',
    install_requires=[
        'shotgun_api3',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.11',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent'
    ]
)
