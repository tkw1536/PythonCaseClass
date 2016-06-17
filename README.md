# PythonCaseClass
[![Build Status](https://travis-ci.org/tkw1536/PythonCaseClass.svg?branch=master)](https://travis-ci.org/tkw1536/PythonCaseClass)

Zero-dependency scala-like case classes for Python 2 + 3.

## Features
* Simple usage: Just inherit from ```case_class.CaseClass```
* Simple Installation: Zero dependencies
* plays well with inheritance
    * ```CaseClass``` usable as a Mix-In
    * Case-to-case inheritance forbidden by default
        * use ```AbstractCaseClass``` to allow only subclasses to be instantiated
        * use ```InheritableCaseClass``` to override allow both super and
        subclasses to be instantiated.
* equality based on arguments
    * calls constructor only once per combination of arguments
    * works with ```==``` operator and ```is``` (referential equality) operator.
* automatic ```repr()``` function`

* works in both Python 2 and Python 3!

## Install

This package is published on the
[the Python Package Index](https://pypi.python.org/pypi/case_class).
Installation can be done simply via pip:

```bash
pip install case_class
```

Alternatively, clone this repository and run setup.py:

```bash
git clone https://github.com/tkw1536/PythonCaseClass
python setup.py install
```

## Examples
```python
# Import the CaseClass module
from case_class import CaseClass

# Create a symbol case class
class Symbol(CaseClass):
    def __init__(self, name):
        self.name = name

# Create an instance
x = Symbol("x")
print(x)  # Symbol('x')

# And create another one
also_x = Symbol('x')
print(x == also_x)  # equality via operator
print(x is also_x)  # referential equality
```

Another example can be found in [example.py](example.py).



## License + Acknowledgements

This module and associated documentation is Copyright &copy; Tom Wiesing 2016
and licensed under the MIT license, see [LICENSE](license) for details. Small
parts of the code are adapted from the [six](https://pypi.python.org/pypi/six)
module, which is Copyright &copy; 2010-2015 Benjamin Peterson.
