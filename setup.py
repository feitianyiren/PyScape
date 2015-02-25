from setuptools import setup, find_packages
setup(
  name='pyscape',
  version='1.3.1',
  entry_points={'console_scripts': ['pyscape = pyscape.pyscape:main']},
  include_package_data = True,
  packages = find_packages(),
  package_data = {
    'pyscape': [
        'backgrounds/*',
        'presets/*',
        'sounds/*.wav',
        'sounds/fm3/*',
        'sounds/beach/*',
        'sounds/explodes/*',
        'sounds/jungle/*',
        'sounds/plane/*',
        'sounds/rain/*',
        'sounds/sea/*',
        'sounds/village/*',
     ],
  }
)
