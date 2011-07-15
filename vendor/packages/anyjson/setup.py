from setuptools import setup, find_packages

author = "Rune Halvorsen"
email = "runefh@gmail.com"
version = "0.2.4"
desc = """Wraps the best available JSON implementation available in a common
interface"""

setup(name='anyjson',
      version=version,
      description=desc,
      long_description=open("README").read(),
      classifiers=[
            'License :: OSI Approved :: BSD License',
            'Intended Audience :: Developers',
            'Programming Language :: Python'
            ],
      keywords='json',
      author=author,
      author_email=email,
      url='http://bitbucket.org/runeh/anyjson',
      license='BSD',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      zip_safe=False,
      platforms=["any"],
      test_suite = 'nose.collector',
)
