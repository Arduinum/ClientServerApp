from setuptools import setup, find_packages

setup(name='robot_messenger_server',
      version='0.1.0',
      description='Server for messenger',
      author='Eugene Kaddo',
      author_email='message.chaos628@gmail.com',
      packages=find_packages(),
      install_requires=['PyQt5', 'sqlalchemy', 'pycryptodome', 'pycryptodomex']
      )
