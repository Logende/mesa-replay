#!/usr/bin/env python
import re

from setuptools import setup, find_packages
from codecs import open

# dill extends the pickle module by adding support also for lambdas and other special built-in Python types
requires = ["mesa", "dill"]

extras_require = {
    "dev": ["flake8"]
}

# loading the version from the init file is taken over from mesa
with open("mesareplay/__init__.py") as fd:
    version = re.search(
        r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', fd.read(), re.MULTILINE
    ).group(1)

with open("README.md", "rb", encoding="utf-8") as f:
    readme = f.read()

setup(
    name="Mesa-Replay",
    version=version,
    description="Enables caching simulations of mesa models, persisting them on the file system and replaying them "
                "later.",
    long_description=readme,
    url="https://github.com/Logende/mesa_replay",
    packages=find_packages(),
    install_requires=requires,
    extras_require=extras_require,
    keywords="agent based modeling model ABM simulation multi-agent mesa cache replay caching",
    license="Apache 2.0",
)
