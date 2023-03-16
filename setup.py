from setuptools import setup
import os
import re

project_name = "Minnion"
cur_dir = os.path.abspath(os.path.dirname(__file__))

def read_version():
    _version_re = re.compile(r"version\s+=\s+(.*)")
    _version_path = os.path.join(cur_dir, "__version__.py")
    with open(_version_path, "rb") as f:
        version = str(
            ast.literal_eval(_version_re.search(f.read().decode("utf-8")).group(1))
        )

    return version


def read_requirements():
    with open(os.path.join(cur_dir, "requirements.txt")) as f:
        content = f.read()
        requirements = content.split("\n")
    return requirements


def read_readme():
    with open(os.path.join(cur_dir, "README.md")) as f:
        long_description = f.read()
    return long_description


setup(
    name=project_name,
    version=read_version(),
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
