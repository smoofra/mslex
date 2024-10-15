=====
mslex
=====


.. image:: https://img.shields.io/pypi/v/mslex.svg
        :target: https://pypi.python.org/pypi/mslex

.. image:: https://img.shields.io/travis/com/smoofra/mslex.svg
        :target: https://travis-ci.org/smoofra/mslex

.. image:: https://readthedocs.org/projects/mslex/badge/?version=latest
        :target: https://mslex.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status


shlex for windows

* Free software: Apache Software License 2.0
* Documentation: https://mslex.readthedocs.io.

Features
--------

This is the missing shlex package for windows shell quoting.   It provides three
functions -- split, quote, and join -- just like shlex.


Windows Quoting
---------------

Since time immemorial, windows quoting behavior has been strange.  Prior to
(I think) Visual Studio 2005, it exhibited the extremely strange modulo 3
periodic behavior which is emulated here in ``split_msvcrt()``.   Programs
compiled with the C runtime from Visual Studio 2005 and later exhibit the
somewhat less strange behavior emulated in ``split_ucrt()``.

Microsoft still ships a dll called ``msvcrt.dll`` as part of Windows,
for compatibility reasons.   And even though they have been very clear in
their documentation that nobody should ever link against this dll, people
still do, either for compatibility reasons of their own, or because it
is universally available on any version of windows you might care about
without needing to run an installer.   And ``msvcrt.dll`` preserves the
extremely strange argument parsing behavior from prior to VS 2005.

You can can download the latest version of `msys2`_ today and build an
executable linking ``msvcrt.dll`` on Windows 11, and it will parse
arguments like Windows 95.

``mslex`` will produce quoted strings that will be parsed correctly by
either modern C runtimes or by ``msvcrt.dll``.   When parsing, ``mslex``
parses it both ways and raises an error if they disagree.   This can
be overridden by passing ``ucrt=True`` or ``ucrt=False`` to ``split``.

See also:

* `Parsing C Command Line Arguments`_

* `Windows is not a Microsoft Visual C/C++ Run-Time delivery channel`_

* `How a Windows Program Splits Its Command Line Into Individual Arguments`_

* `Everyone quotes command line arguments the wrong way`_

.. _`How a Windows Program Splits Its Command Line Into Individual Arguments`:
   https://web.archive.org/web/20220629212422/http://www.windowsinspired.com/how-a-windows-programs-splits-its-command-line-into-individual-arguments/

.. _`Everyone quotes command line arguments the wrong way`:
  https://blogs.msdn.microsoft.com/twistylittlepassagesallalike/2011/04/23/everyone-quotes-command-line-arguments-the-wrong-way/

.. _`Windows is not a Microsoft Visual C/C++ Run-Time delivery channel`: https://devblogs.microsoft.com/oldnewthing/20140411-00/?p=1273

.. _`msys2`: https://www.msys2.org/docs/environments/

.. _`Parsing C Command Line Arguments`: https://learn.microsoft.com/en-us/cpp/c-language/parsing-c-command-line-arguments?view=msvc-170


Automatic selection between mslex and shlex
-------------------------------------------

If you want to automatically use mslex on Windows, and shlex otherwise, check out the `oslex`_ package.

.. _`oslex`: https://pypi.org/project/oslex/
.. _`msvcrt`: https://devblogs.microsoft.com/oldnewthing/20140411-00/?p=1273
.. _`UCRT`: https://learn.microsoft.com/en-us/cpp/porting/upgrade-your-code-to-the-universal-crt?view=msvc-170
