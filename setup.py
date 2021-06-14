from setuptools import setup

with open("README.md", 'r') as readme:
    long_description = readme.read()

setup(
    name="BendersLib",
    version="0.0.1",
    description="A Bender\'s decomposition library.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="GPL-3.0",
    url="https://guo.ph/benderslib",
    
    author="Penghui Guo",
    author_email="m@guo.ph",
    
    packages=["benders"],
    install_requires=[]
)
