from setuptools import setup


with open('README.rst') as fd:
    README = fd.read()


install_requires = ['paramiko >= 2.7.0']


setup(
    name='paramiko-jump',
    version='0.0.0',
    packages=['paramiko_jump'],
    python_requires='>= 3.6',
    install_requires=install_requires,
    url='https://github.com/andrewschenck/paramiko-jump',
    license='Apache License 2.0',
    author='Andrew Blair Schenck, Tyler Bruno',
    author_email='aschenck@gmail.com, tybruno117@gmail.com',
    description='Paramiko + jump host (SSH proxy) + multi-factor '
                'authentication simplified.',
    long_description=README,
    long_description_content_type='text/x-rst',
)
