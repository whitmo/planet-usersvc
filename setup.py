from setuptools import setup, find_packages

setup(name='usersvc',
      version=0.1,
      description='Planet Takehome User Service',
      keywords="web services",
      packages=find_packages(),
      include_package_data=True,
      install_requires=['cornice',
                        'colander',
                        'google-cloud-firestore'],
      entry_points="""\
      [paste.app_factory]
      main=usersvc.app:main
      [console_scripts]
      usersvc.ftest=usersvc.tests.functional_test:exercise
      """,
      paster_plugins=['pyramid'])
