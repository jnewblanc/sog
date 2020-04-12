from setuptools import setup

setup(name='sog',
      version='0.1',
      description='A creative remake of the 80s MUD',
      url='',
      author='Jason Newblanc',
      author_email='<first>.<last>(at)gmail.com',
      license='CC0 1.0',
      packages=find_namespace_packages(include=['sog.*'])
      zip_safe=False,
      )
