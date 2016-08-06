from setuptools import setup
__version__ = "0.4.0"

# Get the long description by reading the README
try:
    readme_content = open("README.md").read()
except:
    readme_content = ""

# Create the actual setup method
setup(name='pypred',
      version=__version__,
      description='A Python library for simple evaluation of natural language predicates',
      long_description=readme_content,
      author='Armon Dadgar',
      author_email='armon@kiip.me',
      maintainer='Armon Dadgar',
      maintainer_email='armon@kiip.me',
      url="https://github.com/armon/pypred/",
      license="MIT License",
      keywords=["python", "predicate", "natural language"],
      packages=['pypred'],
      classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Topic :: Software Development :: Libraries"
      ],
      install_requires=["ply>=3.4"]
    )
