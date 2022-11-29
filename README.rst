=======
Omnidep
=======

A Python linter to compare a project's declared dependencies against the import
statements in its source code.

.. image:: https://github.com/sjjessop/omnidep/workflows/tests/badge.svg?branch=develop
   :alt: Test status
   :target: https://github.com/sjjessop/omnidep/actions?query=workflow%3Atests+branch%3Adevelop

.. image:: https://img.shields.io/badge/CI%20python-3.7%20%7C%203.8%20%7C%203.9%20%7C%203.10%20%7C%203.11-blue.svg
   :alt: Tested with Python versions 3.7 3.8 3.9 3.10 3.11
   :target: https://www.python.org/downloads/

.. image:: https://img.shields.io/pypi/pyversions/omnidep
   :alt: PyPI project
   :target: https://pypi.org/project/omnidep/

.. image:: https://img.shields.io/badge/badges-4-green.svg
   :alt: 4 badges
   :target: https://shields.io/

Purpose
=======

Provides warnings when a project imports packages that it doesn't declare a
dependency on, plus some related linting of the project dependency data.

Currently only poetry projects are supported (configured in pyproject.toml).
The projects that your project depends on can be packaged using any tools, but
your project (that omnidep analyses) currently must use poetry.

Installation
------------

.. code-block:: bash

    pip install omnidep

Optionally, you can also run the test suite. This would be a good idea if
you're using a new (or pre-release) version of Python not included in this
repo's CI testing.

.. code-block:: bash

    pip install pyOpenSSL pytest
    pytest --pyargs omnidep.tst

Usage
-----

.. code-block:: bash

    omnidep pyproject.toml


Configuration
-------------

omnidep uses your project's poetry configuration to work out:

* What source files to search for imports, from ``tool.poetry.packages``.
* What dependencies your project declares, from ``tool.poetry.dependencies``.
* What dev-dependencies your project declares, from
  ``tool.poetry.dev-dependencies`` and ``tool.poetry.group.dev.dependences``.

If you have test code that you want omnidep to search for imports, then:

* If you keep your test code "inside" your project, then list it in
  ``local-test-paths`` in the ``[omnidep.config]`` section described below.
* If you keep your test code "outside" your project, then use the ``--tests``
  command-line option to locate it, otherwise omnidep ignores it. You also need
  to configure ``local-test-packages`` if some of your test files import other
  test files, for example if you have shared helper functions.

omnidep is configured using the ``pyproject.toml`` file, and specifically the
``[tool.omnidep]`` section. The following config keys are recognised.
Unrecognised keys are rejected and omnidep will not run (so, if you want to
use a particular key then you should require at least the minimum version of
omnidep that recognises it).

ignore-imports
^^^^^^^^^^^^^^

Example: ``ignore-imports = ["X"]``

Since: 0.2.0

Causes omnidep to ignore all import statements from X, for example
``import X``, ``from X.Y import Z``. omnidep will behave as if your code does
not use package X, even if it does. X must be a top-level package. It is not
currently possible to selectively ignore a sub-package (like X.Y), nor is it
currently possible to ignore imports from some files but not others.

child-packages
^^^^^^^^^^^^^^

Example: ``child-packages = {boto3 = ["botocore"]}``

Since: 0.2.0

Causes omnidep to consider a dependency on boto3 to also supply botocore. This
saves you having to explictly list the child as a dependency of your project.
You chould only do this when the child is inherant to the parent, not just
because by chance you pull in a package you need via an indirect dependency.
The reason is that indirect dependencies can change, and the project that you
do depend on might not require the same version of the child that your usage
requires. Only if the projects are closely related can you assume that the
version you require of one will provide the features you need from the other.

ignore-dependencies
^^^^^^^^^^^^^^^^^^^

Example: ``ignore-dependencies = ["X"]``

Since: 0.2.0

Causes omnidep to ignore the project X listed in your project's dependencies.
omnidep will behave as if your project does not depend on X, even if it does.

ignore-dependencies-order
^^^^^^^^^^^^^^^^^^^^^^^^^

Example: ``ignore-dependencies-order = true``

Since: 0.2.0

Causes omnidep to skip the check that your dependencies are alphabetically
ordered.

ignore-dev-dependencies-order
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Example: ``ignore-dev-dependencies-order = true``

Since: 0.2.0

Causes omnidep to skip the check that your dev-dependencies are alphabetically
ordered.

local-test-paths
^^^^^^^^^^^^^^^^

Example: ``local-test-paths = ["myproject/tests/"]``

Since: 0.2.0

Causes omnidep to treat all code in ``myproject.tests`` as test code, meaning
that anything it imports can be provided either by your projects dependencies
or by its dev-dependencies. Imports from code that is not test code must be
provided by non-dev dependencies.

local-test-packages
^^^^^^^^^^^^^^^^^^^

Example: ``local-test-packages = ["tests"]``

Since: 0.2.0

Causes omnidep to treat ``tests`` as part of the current project, but only when
considering imports that appear in test code. Use this when your test code is
not shipped as part of your project.

Error codes explained
---------------------

X, Y, P, Q, R, represent the names of imports or dependencies, depending on the
message.

ODEP001
^^^^^^^

| ``package 'X' is imported but not listed in dependencies``
| ``package 'X' is imported but not listed in dev-dependencies``
|

X is the name you imported, which is not necessarily the same as the name of
the project you have to install (for example the project ``beautifulsoup4``
installs the package ``bs4``). omnidep does its best to find what project your
desired package comes from, but if it fails, or if you don't have a suitable
dependency, then this is the result.

To fix, choose one of the following:

* List the project name in your dependencies. If the package is used from test
  code, then the dependency can be either dev or non-dev. If the package is
  used from non-test code, then the dependency needs to be non-dev.
* To ignore the import, add it to the list of ignored imports in your
  ``[tool.omnidep]`` config, like ``ignore-imports = ["X"]``.
* The package might come from a dependency of a dependency, and you might
  prefer not to explicitly list it as a direct dependency too, so you can list
  X as a child of some other dependency that you do list. You should only do
  this when the indirect dependency is inherent to the direct dependency, for
  example ``boto3`` provides ``botocore``. Add
  ``child-packages = {something = ["X"]}`` to your ``[tool.omnidep]`` config,
  meaning that the project named "something" provides "X", and so a dependency
  on "something" is acceptable in place of a dependency on "X".

ODEP002
^^^^^^^

``module 'X' is imported but not installed``

Not only is there no dependency found that provides X, but X isn't even
currently installed. omnidep relies on locally installed metadata to help it
find what dependencies correspond to what imports.

To fix, choose one of the following:

* If your project has X as a dependency, but you haven't installed your
  project then install your project, bringing in its dependencies.
* Add a dependency that provides X.
* Ignore the import by listing it in your in your ``[tool.omnidep]`` config,
  like ``ignore-imports = ["X"]``.

ODEP003
^^^^^^^

``Namespace package found: any of ['P', 'Q', 'R'] might provide 'X'``

If projects P, Q, and R all provide code in the Python package X, then omnidep
doesn't know which one you need in order to satisfy a given import. If you
declare dependencies on all of them (that is, all the ones you currently have
installed), then omnidep is satisfied. If you depend on some but not others,
then you get this message.

To fix, choose one of the following:

* If you don't need the ones you don't declare dependencies on, and they are
  installed accidentally, then uninstall them.
* If appropriate, declare dependencies on all of P, Q, and R. However, this
  might not be appropriate because P and Q might be genuine direct dependencies
  of your code, whereas R was pulled in indirectly via something else. You
  don't want to have to list indirect dependencies as direct dependencies.
* Otherwise you have to resolve for yourself whether your dependencies are
  adequate, then ignore the import with ``ignore-imports = ["X"]`` in your
  ``[tool.omnidep]`` config.


ODEP004
^^^^^^^

``Namespace package found: any of ['P', 'Q', 'R'] might provide 'X', and there are no dependencies on any of them``

If projects P, Q, and R all provide code in the Python package X, then omnidep
doesn't know which one you need in order to satisfy a given import. If you
declare dependencies on all of them (that is, all the ones you currently have
installed), then omnidep is satisfied. If you depend on none of them,
then you get this message.

To fix, choose one of the following:

* If appropriate, declare dependencies on all of P, Q, and R. However, this
  might not be appropriate because P and Q might be genuine direct dependencies
  of your code, whereas R was pulled in indirectly via something else. You
  don't want to have to list indirect dependencies as direct dependencies.
* Otherwise you have to resolve for yourself whether your dependencies are
  adequate, then ignore the import with ``ignore-imports = ["X"]`` in your
  ``[tool.omnidep]`` config.


ODEP005
^^^^^^^

``unused dependencies in project file: {'X', 'Y'}``

omnidep expects you not to list any dependencies that you don't import. This
might be completely legitimate, for example:

* the dependency is a plugin to some framework and will be used via some means
  other than an explicit ``import`` in your code;
* you are controlling the version of an indirect dependency, to deal with
  some problem caused by unexpected breaking changes.

Unused dev-dependencies are always ignored, since they tend to include linters
and suchlike.

To fix, choose one of the following:

* Remove the dependency.
* List the dependency in your ``[tool.omnidep]`` config like
  ``ignore-dependencies = ["X"]``.

ODEP006
^^^^^^^

| ``dependencies are not sorted: 'Y' before 'X'``
| ``dev-dependencies are not sorted: 'Y' before 'X'``
|

Ignoring ``python``, which is allowed to come first, omnidep expects you to
list dependencies in case-insensitive alphabetical order within each section
(dev and non-dev).

To fix, choose one of the following:

* List your dependencies alphabetically.
* Set ``ignore-dependencies-order = true`` or
  ``ignore-dev-dependencies-order = true`` in your ``[tool.omnidep]`` config.

ODEP007
^^^^^^^

``dependency 'X' is not the preferred name: consider 'Y'``

omnidep expects you to use either of two formats to name dependencies in your
project file: the "Normalized Name" as defined in
`PEP 503 <https://peps.python.org/pep-0503/>`_ or the name the dependency uses
for itself in its metadata. Any name that normalizes to the same value will
work, but inconsistent naming tends to lead to confusion, or to failing to find
mentions when you search for them.

To fix:

* Use the name omnidep suggests, or the normalized name.

ODEP008
^^^^^^^

``Module 'X' not under package management but found on python path``

omnidep cannot find any project that provides X, but it is available to import.
This can happen for example if you have set up the ``PYTHONPATH`` to find the
code, instead of installing it as a dependency.

To fix, choose one of the following:

* If this is an error, list a suitable dependency.
* If you know what you're doing, and users of your project will know how to
  supply the code that you're importing, then ignore the import with
  ``ignore-imports = ["X"]`` in your ``[tool.omnidep]`` config.

Changelog
=========

0.3.1
-----

* Add Python 3.11 to the test matrix, and use separate badges in the README
  for what is tagged on PyPI vs. what is tested.
* Documentation improvements.
* Uncap Python dependency. If Python ever reaches version 4, you are free to
  install omnidep on it and see what happens!

0.3.0
-----

* Breaking: When testing that dependencies are sorted, do it case-insensitive.
* Deal with some build issues.

0.2.1
-----

* Refer to online docs insted of long message in terminal.
* Publish to PyPI.

0.2.0
-----

* Minor documentation improvements.
* Lower bounds for dependencies importlib-metadata, isort, and tomli.
* CI test of the lower-bound versions.
