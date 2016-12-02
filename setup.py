import os
from setuptools import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name="case_class",
    version="0.0.8",

    url="https://github.com/tkw1536/PythonCaseClass",
    author="Tom Wiesing",
    author_email="tkw01536@gmail.com",

    py_modules=['case_class', 'case_class.case_class', 'case_class.clsutils',
                'case_class.exceptions', 'case_class.signature',
                'case_class.utils', 'case_class.extractor'],

    description=("Scala-like CaseClasses for Python"),
    long_description=read('README.rst'),

    license="MIT",

    classifiers=[
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",

        "License :: OSI Approved :: MIT License",

        "Topic :: Software Development :: Libraries",
        "Intended Audience :: Developers",
        "Topic :: Utilities",
    ]
)
