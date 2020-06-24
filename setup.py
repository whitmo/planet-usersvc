from setuptools import setup, find_packages

setup(name='usersvc',
      version=0.1,
      description='Planet Takehome User Service',
      keywords="web services",
      packages=find_packages(),
      include_package_data=True,
      install_requires=['cornice',
                        'waitress',
                        'colander',
                        'google-cloud-firestore',
                        'cached_property'],
      entry_points="""\
      [paste.app_factory]
      main=usersvc.app:main
      """,
      paster_plugins=['pyramid'])
