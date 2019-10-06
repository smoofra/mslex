#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `mslex` package."""

import sys
import itertools
import functools
import unittest
import subprocess

from mslex import split, quote

if sys.platform == 'win32':
    import ctypes
    from ctypes import windll, wintypes

    CommandLineToArgvW = windll.shell32.CommandLineToArgvW
    CommandLineToArgvW.argtypes = [
        wintypes.LPCWSTR, ctypes.POINTER(ctypes.c_int)]
    CommandLineToArgvW.restype = ctypes.POINTER(wintypes.LPWSTR)

    LocalFree = windll.kernel32.LocalFree
    LocalFree.argtypes = [wintypes.HLOCAL]
    LocalFree.restype = wintypes.HLOCAL

    def ctypes_split(s):
        argc = ctypes.c_int()
        argv = CommandLineToArgvW('foo.exe ' + s, ctypes.byref(argc))
        result = [argv[i] for i in range(1, argc.value)]
        LocalFree(argv)
        return result


examples = [
    (r'', []),
    (r'"', ['']),
    (r'x', ['x']),
    (r'x"', ['x']),
    (r'foo', ['foo']),
    (r'foo    "bar baz"', ['foo', 'bar baz']),
    (r'"abc" d e', ['abc', 'd', 'e']),
    (r'a\\\b d"e f"g h', [r'a\\\b', 'de fg', 'h']),
    (r'a\\\"b c d', [r'a\"b', 'c', 'd']),
    (r'a\\\\"b c" d e', [r'a\\b c', 'd', 'e']),
    ('"" "" ""', ['', '', '']),
    ('" x', [' x']),
    ('"" x', ['', 'x']),
    ('""" x', ['"', 'x']),
    ('"""" x', ['" x']),
    ('""""" x', ['"', 'x']),
    ('"""""" x', ['""', 'x']),
    ('""""""" x', ['"" x']),
    ('"""""""" x', ['""', 'x']),
    ('""""""""" x', ['"""', 'x']),
    ('"""""""""" x', ['""" x']),
    ('""""""""""" x', ['"""', 'x']),
    ('"""""""""""" x', ['""""', 'x']),
    ('""""""""""""" x', ['"""" x']),
    ('"aaa x', ['aaa x']),
    ('"aaa" x', ['aaa', 'x']),
    ('"aaa"" x', ['aaa"', 'x']),
    ('"aaa""" x', ['aaa" x']),
    ('"aaa"""" x', ['aaa"', 'x']),
    ('"aaa""""" x', ['aaa""', 'x']),
    ('"aaa"""""" x', ['aaa"" x']),
    ('"aaa""""""" x', ['aaa""', 'x']),
    ('"aaa"""""""" x', ['aaa"""', 'x']),
    ('"aaa""""""""" x', ['aaa""" x']),
    ('"aaa"""""""""" x', ['aaa"""', 'x']),
    ('"aaa""""""""""" x', ['aaa""""', 'x']),
    ('"aaa"""""""""""" x', ['aaa"""" x']),
    ('"aaa\\ x', ['aaa\\ x']),
    ('"aaa\\" x', ['aaa" x']),
    ('"aaa\\"" x', ['aaa"', 'x']),
    ('"aaa\\""" x', ['aaa""', 'x']),
    ('"aaa\\"""" x', ['aaa"" x']),
    ('"aaa\\""""" x', ['aaa""', 'x']),
    ('"aaa\\"""""" x', ['aaa"""', 'x']),
    ('"aaa\\""""""" x', ['aaa""" x']),
    ('"aaa\\"""""""" x', ['aaa"""', 'x']),
    ('"aaa\\""""""""" x', ['aaa""""', 'x']),
    ('"aaa\\"""""""""" x', ['aaa"""" x']),
    ('"aaa\\""""""""""" x', ['aaa""""', 'x']),
    ('"aaa\\"""""""""""" x', ['aaa"""""', 'x']),
    ('"aaa\\\\ x', ['aaa\\\\ x']),
    ('"aaa\\\\" x', ['aaa\\', 'x']),
    ('"aaa\\\\"" x', ['aaa\\"', 'x']),
    ('"aaa\\\\""" x', ['aaa\\" x']),
    ('"aaa\\\\"""" x', ['aaa\\"', 'x']),
    ('"aaa\\\\""""" x', ['aaa\\""', 'x']),
    ('"aaa\\\\"""""" x', ['aaa\\"" x']),
    ('"aaa\\\\""""""" x', ['aaa\\""', 'x']),
    ('"aaa\\\\"""""""" x', ['aaa\\"""', 'x']),
    ('"aaa\\\\""""""""" x', ['aaa\\""" x']),
    ('"aaa\\\\"""""""""" x', ['aaa\\"""', 'x']),
    ('"aaa\\\\""""""""""" x', ['aaa\\""""', 'x']),
    ('"aaa\\\\"""""""""""" x', ['aaa\\"""" x']),
    ('"aaa\\\\\\ x', ['aaa\\\\\\ x']),
    ('"aaa\\\\\\" x', ['aaa\\" x']),
    ('"aaa\\\\\\"" x', ['aaa\\"', 'x']),
    ('"aaa\\\\\\""" x', ['aaa\\""', 'x']),
    ('"aaa\\\\\\"""" x', ['aaa\\"" x']),
    ('"aaa\\\\\\""""" x', ['aaa\\""', 'x']),
    ('"aaa\\\\\\"""""" x', ['aaa\\"""', 'x']),
    ('"aaa\\\\\\""""""" x', ['aaa\\""" x']),
    ('"aaa\\\\\\"""""""" x', ['aaa\\"""', 'x']),
    ('"aaa\\\\\\""""""""" x', ['aaa\\""""', 'x']),
    ('"aaa\\\\\\"""""""""" x', ['aaa\\"""" x']),
    ('"aaa\\\\\\""""""""""" x', ['aaa\\""""', 'x']),
    ('"aaa\\\\\\"""""""""""" x', ['aaa\\"""""', 'x']),
    ('"aaa\\\\\\\\ x', ['aaa\\\\\\\\ x']),
    ('"aaa\\\\\\\\" x', ['aaa\\\\', 'x']),
    ('"aaa\\\\\\\\"" x', ['aaa\\\\"', 'x']),
    ('"aaa\\\\\\\\""" x', ['aaa\\\\" x']),
    ('"aaa\\\\\\\\"""" x', ['aaa\\\\"', 'x']),
    ('"aaa\\\\\\\\""""" x', ['aaa\\\\""', 'x']),
    ('"aaa\\\\\\\\"""""" x', ['aaa\\\\"" x']),
    ('"aaa\\\\\\\\""""""" x', ['aaa\\\\""', 'x']),
    ('"aaa\\\\\\\\"""""""" x', ['aaa\\\\"""', 'x']),
    ('"aaa\\\\\\\\""""""""" x', ['aaa\\\\""" x']),
    ('"aaa\\\\\\\\"""""""""" x', ['aaa\\\\"""', 'x']),
    ('"aaa\\\\\\\\""""""""""" x', ['aaa\\\\""""', 'x']),
    ('"aaa\\\\\\\\"""""""""""" x', ['aaa\\\\"""" x']),
    (' x', ['x']),
    ('" x', [' x']),
    ('"" x', ['', 'x']),
    ('""" x', ['"', 'x']),
    ('"""" x', ['" x']),
    ('""""" x', ['"', 'x']),
    ('"""""" x', ['""', 'x']),
    ('""""""" x', ['"" x']),
    ('"""""""" x', ['""', 'x']),
    ('""""""""" x', ['"""', 'x']),
    ('"""""""""" x', ['""" x']),
    ('""""""""""" x', ['"""', 'x']),
    ('"""""""""""" x', ['""""', 'x']),
    ('\\ x', ['\\', 'x']),
    ('\\" x', ['"', 'x']),
    ('\\"" x', ['" x']),
    ('\\""" x', ['"', 'x']),
    ('\\"""" x', ['""', 'x']),
    ('\\""""" x', ['"" x']),
    ('\\"""""" x', ['""', 'x']),
    ('\\""""""" x', ['"""', 'x']),
    ('\\"""""""" x', ['""" x']),
    ('\\""""""""" x', ['"""', 'x']),
    ('\\"""""""""" x', ['""""', 'x']),
    ('\\""""""""""" x', ['"""" x']),
    ('\\"""""""""""" x', ['""""', 'x']),
    ('\\\\ x', ['\\\\', 'x']),
    ('\\\\" x', ['\\ x']),
    ('\\\\"" x', ['\\', 'x']),
    ('\\\\""" x', ['\\"', 'x']),
    ('\\\\"""" x', ['\\" x']),
    ('\\\\""""" x', ['\\"', 'x']),
    ('\\\\"""""" x', ['\\""', 'x']),
    ('\\\\""""""" x', ['\\"" x']),
    ('\\\\"""""""" x', ['\\""', 'x']),
    ('\\\\""""""""" x', ['\\"""', 'x']),
    ('\\\\"""""""""" x', ['\\""" x']),
    ('\\\\""""""""""" x', ['\\"""', 'x']),
    ('\\\\"""""""""""" x', ['\\""""', 'x']),
    ('\\\\\\ x', ['\\\\\\', 'x']),
    ('\\\\\\" x', ['\\"', 'x']),
    ('\\\\\\"" x', ['\\" x']),
    ('\\\\\\""" x', ['\\"', 'x']),
    ('\\\\\\"""" x', ['\\""', 'x']),
    ('\\\\\\""""" x', ['\\"" x']),
    ('\\\\\\"""""" x', ['\\""', 'x']),
    ('\\\\\\""""""" x', ['\\"""', 'x']),
    ('\\\\\\"""""""" x', ['\\""" x']),
    ('\\\\\\""""""""" x', ['\\"""', 'x']),
    ('\\\\\\"""""""""" x', ['\\""""', 'x']),
    ('\\\\\\""""""""""" x', ['\\"""" x']),
    ('\\\\\\"""""""""""" x', ['\\""""', 'x']),
    ('\\\\\\\\ x', ['\\\\\\\\', 'x']),
    ('\\\\\\\\" x', ['\\\\ x']),
    ('\\\\\\\\"" x', ['\\\\', 'x']),
    ('\\\\\\\\""" x', ['\\\\"', 'x']),
    ('\\\\\\\\"""" x', ['\\\\" x']),
    ('\\\\\\\\""""" x', ['\\\\"', 'x']),
    ('\\\\\\\\"""""" x', ['\\\\""', 'x']),
    ('\\\\\\\\""""""" x', ['\\\\"" x']),
    ('\\\\\\\\"""""""" x', ['\\\\""', 'x']),
    ('\\\\\\\\""""""""" x', ['\\\\"""', 'x']),
    ('\\\\\\\\"""""""""" x', ['\\\\""" x']),
    ('\\\\\\\\""""""""""" x', ['\\\\"""', 'x']),
    ('\\\\\\\\"""""""""""" x', ['\\\\""""', 'x'])]


cmd_examples = [
    (r'"foo &whoami bar"', ['foo &whoami bar']),
    (r'^^', ['^']),
    (r'"^"', ['^']),
    (r'"^^"', ['^^']),
    (r'foo^bar', ['foobar']),
    (r'foo^^bar', ['foo^bar']),
    (r'"foo^bar"', ['foo^bar']),
    (r'"foo^^bar"', ['foo^^bar']),
    ]


pretty_examples = [
    (r'c:\Program Files\FooBar', r'"c:\Program Files\FooBar"'),
    (r'c:\Program Files (x86)\FooBar', r'"c:\Program Files (x86)\FooBar"'),
    (r'^', '"^"'),
    (r' ^', '" ^"'),
    (r'&', '"&"'),
    (r'!', '^!'),
    (r'!foo!', '^!foo^!'),
    ("foo\\bar\\baz\\", 'foo\\bar\\baz\\'),
    ("foo bar\\baz\\", '"foo bar\\baz\\\\"'),
    ("foo () bar\\baz\\", '"foo () bar\\baz\\\\"'),
    ("foo () bar\\baz\\\\", '"foo () bar\\baz\\\\\\\\"'),
    ("foo () bar\\baz\\\\\\", '"foo () bar\\baz\\\\\\\\\\\\"'),
    ("foo () bar\\baz\\\\\\\\", '"foo () bar\\baz\\\\\\\\\\\\\\\\"'),
]

class TestMslex(unittest.TestCase):
    """Tests for `mslex` package."""

    def case(self, s, ans, cmd):
        try:
            if ans is not None:
                self.assertEqual(split(s, like_cmd=cmd), ans)
            if sys.platform == 'win32' and not cmd:
                self.assertEqual(split(s), ctypes_split(s))
        except AssertionError:
            print(f"in: «{s}»")
            print()
            for x in split(s, like_cmd=cmd):
                print(f"out: «{x}»")
            print()
            if ans is not None:
                for x in ans:
                    print(f"ans: «{x}»")
                print()
            if sys.platform == 'win32':
                for x in ctypes_split(s):
                    print(f"win: «{x}»")
                print()
            raise


    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    @unittest.skipUnless(sys.platform == "win32", "requires Windows")
    def test_every_string(self):

        def every_string():
            chars = [' ', 'x', '"', '\\']
            prod = itertools.product(*itertools.repeat(chars, 10))
            for x in prod:
                yield ''.join(x)

        for s in every_string():
            self.case(s, None, cmd=False)

    @unittest.skipUnless(sys.platform == "win32", "requires Windows")
    def test_multi_quotes(self):
        for qm in (True, False):
            for m in range(5):
                for n in range(13):
                    if qm:
                        s = '"aaa'
                    else:
                        s = ''
                    s += '\\'*m + '"'*n + ' x'
                    self.case(s, None, False)

    def test_examples(self):
        for s, ans in examples:
            self.case(s, ans, cmd=False)

    def test_examples_for_cmd(self):
        for s, ans in cmd_examples:
            self.case(s, ans, cmd=True)

    def test_quote_examples(self):
        qu = functools.partial(quote, for_cmd=False)
        sp = functools.partial(split, like_cmd=False)
        for s, ans in itertools.chain(examples, cmd_examples):
            self.assertEqual(ans, sp(' '.join(map(qu, ans))))

    def test_quote_examples_cmd(self):
        for s, ans in itertools.chain(examples, cmd_examples):
            self.assertEqual(ans, split(' '.join(map(quote, ans))))

    def test_requote_examples_cmd(self):
        for s, ans in examples:
            self.assertEqual([s], split(quote(s)))

    def test_requote_examples(self):
        for s, ans in examples:
            self.assertEqual([s], split(quote(s, for_cmd=False), like_cmd=False))

    def test_quote_every_string(self):

        def every_string():
            chars = [' ', 'x', '"', '\\']
            prod = itertools.product(*itertools.repeat(chars, 8))
            for x in prod:
                yield ''.join(x)

        for s in every_string():
            q = quote(s, for_cmd=False)
            self.assertEqual([s], split(q, like_cmd=False))
            self.assertEqual([s, s], split(f'{q} {q}', like_cmd=False))


    def test_quote_every_string_for_cmd(self):

        def every_string():
            chars = [' ', 'x', '"', '\\', '^', '&', '!']
            prod = itertools.product(*itertools.repeat(chars, 6))
            for x in prod:
                yield ''.join(x)

        for s in every_string():
            q = quote(s)
            self.assertEqual([s], split(q))
            self.assertEqual([s, s], split(f'{q} {q}'))


    @unittest.skipUnless(sys.platform == "win32", "requires Windows")
    def test_quote_every_string_using_cmd(self):
        def every_string():
            chars = [' ', 'x', '"', '\\', '^', '&']
            prod = itertools.product(*itertools.repeat(chars, 4))
            for x in prod:
                yield ''.join(x)
        for s in every_string():
            q = quote(s)
            if sys.platform == "win32":
                proc = subprocess.run('python -c "import sys; print(sys.argv[1])" ' + q, shell=True, stdout=subprocess.PIPE)
                self.assertEqual(proc.stdout.decode('ascii').rstrip(), s.rstrip())

    def test_pretty_examples(self):
        for s, ans in pretty_examples:
            self.assertEqual(quote(s), ans)
            self.assertEqual(split(ans), [s])
            self.assertEqual(split(ans + ' ' + ans + " foo bar"), [s, s, 'foo', 'bar'])
