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
the project used to install it (for example the project ``beautifulsoup4``
installs the package ``bs4``). omnidep does its best to find what project your
desired package comes from, but if it fails, or if you don't have a suitable
dependency, then this is the result.

To fix:

* List the project name in your dependencies. If the package is used from test
  code, then the dependency can be either dev or non-dev. If the package is
  used from non-test code, then the dependency needs to be non-dev.
* To ignore the import, add it to the list of ignored imports in your
  ``[tool.omnidep]`` config, like ``ignore-imports = ["X"]``.
* The package might come from a dependency of a dependency, and you might
  prefer not to explicitly list it as a direct dependency too, so you can list
  X as a child of some other dependency that you do list. You should only do
  this when the indirect dependency is inherent to the direct dependency, for
  example ``boto3`` provides ``botocore``. Otherwise there's a risk that the
  indirect dependency will introduce breaking changes, which the direct
  dependency doesn't care about and so accepts the new version, but which break
  your particular usage of the indirect dependency. To do this, then
  you can add ``child-packages = {something = ["X"]}`` to your
  ``[tool.omnidep]`` config, meaning that the project named "something"
  provides "X", and so a dependency on "something" is acceptable in place of a
  dependency on "X".

ODEP002
^^^^^^^

``module 'X' is imported but not installed``

Not only is there no dependency found that provides X, but X isn't even
currently installed. omnidep relies on locally installed metadata to help it
find what dependencies correspond to what imports.

To fix:

* Install your project, bringing in its dependencies.
* Add a dependency that provides X.
* Ignore the import by listing it in your in your ``[tool.omnidep]`` config,
  like ``ignore-imports = ["X"]``.

ODEP003
^^^^^^^

``Namespace package found: any of ['P', 'Q', 'R'] might provide 'X'``

If projects P, Q, and R all provide code in the Python package X, then omnidep
doesn't know which one you need in order to satisfy a given import. If you
declare dependencies on all of them (that is, all the ones you urrently have
installed), then omnidep is satisfied. If you depend on some but not others,
then you get this message.

To fix:

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
declare dependencies on all of them (that is, all the ones you urrently have
installed), then omnidep is satisfied. If you depend on none of them,
then you get this message.

To fix:

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

To fix:

* Remove the dependency.
* List the dependency in your ``[tool.omnidep]`` config like
  ``ignore-dependencies = ["X"]``.

ODEP006
^^^^^^^

| ``dependencies are not sorted: 'Y' before 'X'``
| ``dev-dependencies are not sorted: 'Y' before 'X'``
|

Ignoring ``python``, which is allowed to come first, omnidep expects you to
list dependencies in alphabetical order within each section (dev and non-dev).

To fix: Either list your dependencies alphabetically, or set
``ignore-dependencies-order = true`` or
``ignore-dev-dependencies-order = true`` in your ``[tool.omnidep]`` config.

ODEP007
^^^^^^^

``dependency 'X' is not the preferred name: consider 'Y'``

There are two formats that omnidep expects you to use to name dependencies in
your project file: the "Normalized Name" as defined in
`PEP 503 <https://peps.python.org/pep-0503/>`_ or the name the dependency uses
for itself in its metadata. Any other name will work that normalizes to the
same value, but inconsistent naming tends to lead to confusion, or to failing
to find mentions when you search for them.

To fix: Use the name omnidep suggests.

ODEP008
^^^^^^^

``Module 'X' not under package management but found on python path``

omnidep cannot find any project that provides X, but it is available to import.
This can happen for example if you have set up the ``PYTHONPATH`` to find the
code, instead of installing it as a dependency.

To fix:

* If this is an error, list a suitable dependency.
* If you know what you're doing, and users of your project will know how to
  supply the code that you're importing, then ignore the import with
  ``ignore-imports = ["X"]`` in your ``[tool.omnidep]`` config.
