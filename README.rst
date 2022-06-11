=======
Omnidep
=======

A Python linter to compare a project's declared dependencies against the import
statements in its source code.

.. image:: https://github.com/sjjessop/omnidep/workflows/tests/badge.svg?branch=develop
   :alt: Test status
   :target: https://github.com/sjjessop/omnidep/actions?query=workflow%3Atests+branch%3Adevelop

.. image:: https://img.shields.io/badge/python-3.7%20%7C%203.8%20%7C%203.9%20%7C%203.10-blue.svg
   :alt: Python versions 3.7 3.8 3.9 3.10
   :target: https://www.python.org/downloads/

.. image:: https://img.shields.io/badge/badges-3-green.svg
   :alt: 3 badges
   :target: https://shields.io/

Purpose
=======

Provides warnings when a project imports packages that it doesn't declare a
dependency on, plus some related linting of the project dependency data.

Currently only poetry projects are supported (configured in pyproject.toml).

Usage
-----

.. code-block:: bash

    omnidep pyproject.toml
