=====
mslex
=====


.. image:: https://img.shields.io/pypi/v/mslex.svg
        :target: https://pypi.python.org/pypi/mslex

.. image:: https://img.shields.io/travis/smoofra/mslex.svg
        :target: https://travis-ci.org/smoofra/mslex

.. image:: https://readthedocs.org/projects/mslex/badge/?version=latest
        :target: https://mslex.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status


shlex for windows

* Free software: Apache Software License 2.0
* Documentation: https://mslex.readthedocs.io.

Features
--------

This is the missing shlex package for windows shell quoting.   It provides two
functions -- split and quote -- just like shlex.


Credits
-------

These are excellent articles to read if you really want to face the
sanity-melting reality buried under the surface of how windows passes command
line arguments to your programs.   I recommend you read something else.

* `How a Windows Program Splits Its Command Line Into Individual Arguments`_

* `Everyone quotes command line arguments the wrong way`_

.. _`How a Windows Program Splits Its Command Line Into Individual Arguments`:
  http://www.windowsinspired.com/how-a-windows-programs-splits-its-command-line-into-individual-arguments/

.. _`Everyone quotes command line arguments the wrong way`:
  https://blogs.msdn.microsoft.com/twistylittlepassagesallalike/2011/04/23/everyone-quotes-command-line-arguments-the-wrong-way/

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
