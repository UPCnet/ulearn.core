from setuptools import setup, find_packages
import os

version = '2.78.dev0'

README = open('README.rst').read()
HISTORY = open(os.path.join('docs', 'HISTORY.rst')).read()

setup(name='ulearn.core',
      version=version,
      description='',
      long_description=README + '\n' + HISTORY,
      classifiers=[
          'Environment :: Web Environment',
          'Framework :: Plone',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
          'Programming Language :: Python :: 2.6',
          'Programming Language :: Python :: 2.7',
          'Topic :: Software Development :: Libraries :: Python Modules',
      ],
      keywords='theme genweb plone',
      author='UPCnet Plone Team',
      author_email='plone.team@upcnet.es',
      url='https://github.com/UPCnet/ulearn.core.git',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['ulearn', ],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'genweb.core',
          'ulearn.theme',
          'mrs.max',
          'pas.plugins.osiris',
          'plone.app.dexterity',
          'plone.app.contenttypes',
          'plone.app.event',
          'infrae.rest',
          'Products.PloneFormGen',
          'collective.z3cform.datagridfield',
          'genweb.smartportlet',
          'collective.polls'
          # 'experimental.securityindexing'
      ],
      extras_require={'test': ['plone.app.testing',
                               'Products.PloneLDAP',
                               'plone.app.testing[robot]>=4.2.2',
                               'plone.app.robotframework[debug]',
                               'httpretty',
                               'profilehooks']},
      entry_points="""
      # -*- Entry points: -*-
      [z3c.autoinclude.plugin]
      target = plone
      """,
      )
