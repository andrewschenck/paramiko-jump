from setuptools import setup


with open('README.md') as fd:
    README = fd.read()


install_requires = ['paramiko >= 3.4.0']


setup(
    name='paramiko-jump',
    packages=['paramiko_jump'],
    version='0.0.2',
    description='Paramiko + jump host (SSH proxy) + multi-factor '
                'authentication simplified.',
    long_description=README,
    python_requires='>= 3.6',
    install_requires=install_requires,
    license='Apache License 2.0',
    author='Andrew Blair Schenck',
    author_email='aschenck@gmail.com',
    long_description_content_type='text/markdown',
    url='https://github.com/andrewschenck/paramiko-jump',
)
