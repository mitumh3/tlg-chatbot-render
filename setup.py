import os
import re
from typing import List

from __version__ import __version__
from setuptools import setup

PROJECT_NAME = "Minnion"
cur_dir = os.path.abspath(os.path.dirname(__file__))


def read_requirements() -> List[str]:
    with open(os.path.join(cur_dir, "requirements.txt")) as f:
        content = f.read()
        requirements = content.split("\n")
    return requirements


def read_readme() -> str:
    with open(os.path.join(cur_dir, "README.md")) as f:
        long_description = f.read()
    return long_description


setup(
    name=PROJECT_NAME,
    version=__version__,
    description="OpenAI GPT bot with Duckduckgo search engine",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    author="Truong Ngoc Minh",
    author_email="@gmail.com",
    url="https://github.com/mitumh3/tlg-chatbot-render",
    install_requires=read_requirements(),
    classifiers=[
        "Intended Audience :: Developers",
        "Operating System :: Unix",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.10.2",
    ],
)
