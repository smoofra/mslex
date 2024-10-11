#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `mslex` package."""

import os
import sys
import json
import itertools
import functools
import unittest
import subprocess
from typing import List, cast, Any, Optional

from mslex import split, quote


if sys.platform == "win32":
    import ctypes
    from ctypes import windll, wintypes

    CommandLineToArgvW = windll.shell32.CommandLineToArgvW
    CommandLineToArgvW.argtypes = [wintypes.LPCWSTR, ctypes.POINTER(ctypes.c_int)]
    CommandLineToArgvW.restype = ctypes.POINTER(wintypes.LPWSTR)

    LocalFree = windll.kernel32.LocalFree
    LocalFree.argtypes = [wintypes.HLOCAL]
    LocalFree.restype = wintypes.HLOCAL

    def ctypes_split(s):
        argc = ctypes.c_int()
        argv = CommandLineToArgvW("foo.exe " + s, ctypes.byref(argc))
        result = [argv[i] for i in range(1, argc.value)]
        LocalFree(argv)
        return result


def cmd_split(s: str) -> List[str]:
    assert sys.platform == "win32"
    script = os.path.join(os.path.dirname(__file__), "cmdline.py")
    cmdline = script + " " + s
    proc = subprocess.run(cmdline, shell=True, stdout=subprocess.PIPE, check=True)
    args = json.loads(proc.stdout)["CommandLineToArgvW"]
    return args[2:]  # first two args are "python.exe cmdline.py"


class Example:
    def __init__(self, input: str, output: List[str], cmd_output: Optional[List[str]] = None):
        self.input = input
        self.output = output
        self.cmd_output = cmd_output if cmd_output is not None else output


examples = [
    Example(r"", []),
    Example(r'"', [""]),
    Example(r'""', [""]),
    Example(r'"""', ['"']),
    Example(r'""""', ['"']),
    Example(r'"""""', ['"']),
    Example(r'""""""', ['""']),
    Example(r'"""""""', ['""']),
    Example(r'""""""""', ['""']),
    Example(r'"""""""""', ['"""']),
    Example(r'""""""""""', ['"""']),
    Example(r' "', [""]),
    Example(r' ""', [""]),
    Example(r' """', ['"']),
    Example(r' """"', ['"']),
    Example(r' """""', ['"']),
    Example(r' """"""', ['""']),
    Example(r' """""""', ['""']),
    Example(r' """"""""', ['""']),
    Example(r' """"""""""', ['"""']),
    Example(r" ", []),
    Example(r'" ', [" "]),
    Example(r'"" ', [""]),
    Example(r'""" ', ['"']),
    Example(r'"""" ', ['" ']),
    Example(r'""""" ', ['"']),
    Example(r'"""""" ', ['""']),
    Example(r'""""""" ', ['"" ']),
    Example(r'"""""""" ', ['""']),
    Example(r'"""""""""" ', ['""" ']),
    Example(r"x", ["x"]),
    Example(r'x"', ["x"]),
    Example(r"foo", ["foo"]),
    Example(r'foo    "bar baz"', ["foo", "bar baz"]),
    Example(r'"abc" d e', ["abc", "d", "e"]),
    Example(r'a\\\b d"e f"g h', [r"a\\\b", "de fg", "h"]),
    Example(r"a\\\"b c d", [r"a\"b", "c", "d"]),
    Example(r'a\\\\"b c" d e', [r"a\\b c", "d", "e"]),
    Example('"" "" ""', ["", "", ""]),
    Example('" x', [" x"]),
    Example('"" x', ["", "x"]),
    Example('""" x', ['"', "x"]),
    Example('"""" x', ['" x']),
    Example('""""" x', ['"', "x"]),
    Example('"""""" x', ['""', "x"]),
    Example('""""""" x', ['"" x']),
    Example('"""""""" x', ['""', "x"]),
    Example('""""""""" x', ['"""', "x"]),
    Example('"""""""""" x', ['""" x']),
    Example('""""""""""" x', ['"""', "x"]),
    Example('"""""""""""" x', ['""""', "x"]),
    Example('""""""""""""" x', ['"""" x']),
    Example('"aaa x', ["aaa x"]),
    Example('"aaa" x', ["aaa", "x"]),
    Example('"aaa"" x', ['aaa"', "x"]),
    Example('"aaa""" x', ['aaa" x']),
    Example('"aaa"""" x', ['aaa"', "x"]),
    Example('"aaa""""" x', ['aaa""', "x"]),
    Example('"aaa"""""" x', ['aaa"" x']),
    Example('"aaa""""""" x', ['aaa""', "x"]),
    Example('"aaa"""""""" x', ['aaa"""', "x"]),
    Example('"aaa""""""""" x', ['aaa""" x']),
    Example('"aaa"""""""""" x', ['aaa"""', "x"]),
    Example('"aaa""""""""""" x', ['aaa""""', "x"]),
    Example('"aaa"""""""""""" x', ['aaa"""" x']),
    Example('"aaa\\ x', ["aaa\\ x"]),
    Example('"aaa\\" x', ['aaa" x']),
    Example('"aaa\\"" x', ['aaa"', "x"]),
    Example('"aaa\\""" x', ['aaa""', "x"]),
    Example('"aaa\\"""" x', ['aaa"" x']),
    Example('"aaa\\""""" x', ['aaa""', "x"]),
    Example('"aaa\\"""""" x', ['aaa"""', "x"]),
    Example('"aaa\\""""""" x', ['aaa""" x']),
    Example('"aaa\\"""""""" x', ['aaa"""', "x"]),
    Example('"aaa\\""""""""" x', ['aaa""""', "x"]),
    Example('"aaa\\"""""""""" x', ['aaa"""" x']),
    Example('"aaa\\""""""""""" x', ['aaa""""', "x"]),
    Example('"aaa\\"""""""""""" x', ['aaa"""""', "x"]),
    Example('"aaa\\\\ x', ["aaa\\\\ x"]),
    Example('"aaa\\\\" x', ["aaa\\", "x"]),
    Example('"aaa\\\\"" x', ['aaa\\"', "x"]),
    Example('"aaa\\\\""" x', ['aaa\\" x']),
    Example('"aaa\\\\"""" x', ['aaa\\"', "x"]),
    Example('"aaa\\\\""""" x', ['aaa\\""', "x"]),
    Example('"aaa\\\\"""""" x', ['aaa\\"" x']),
    Example('"aaa\\\\""""""" x', ['aaa\\""', "x"]),
    Example('"aaa\\\\"""""""" x', ['aaa\\"""', "x"]),
    Example('"aaa\\\\""""""""" x', ['aaa\\""" x']),
    Example('"aaa\\\\"""""""""" x', ['aaa\\"""', "x"]),
    Example('"aaa\\\\""""""""""" x', ['aaa\\""""', "x"]),
    Example('"aaa\\\\"""""""""""" x', ['aaa\\"""" x']),
    Example('"aaa\\\\\\ x', ["aaa\\\\\\ x"]),
    Example('"aaa\\\\\\" x', ['aaa\\" x']),
    Example('"aaa\\\\\\"" x', ['aaa\\"', "x"]),
    Example('"aaa\\\\\\""" x', ['aaa\\""', "x"]),
    Example('"aaa\\\\\\"""" x', ['aaa\\"" x']),
    Example('"aaa\\\\\\""""" x', ['aaa\\""', "x"]),
    Example('"aaa\\\\\\"""""" x', ['aaa\\"""', "x"]),
    Example('"aaa\\\\\\""""""" x', ['aaa\\""" x']),
    Example('"aaa\\\\\\"""""""" x', ['aaa\\"""', "x"]),
    Example('"aaa\\\\\\""""""""" x', ['aaa\\""""', "x"]),
    Example('"aaa\\\\\\"""""""""" x', ['aaa\\"""" x']),
    Example('"aaa\\\\\\""""""""""" x', ['aaa\\""""', "x"]),
    Example('"aaa\\\\\\"""""""""""" x', ['aaa\\"""""', "x"]),
    Example('"aaa\\\\\\\\ x', ["aaa\\\\\\\\ x"]),
    Example('"aaa\\\\\\\\" x', ["aaa\\\\", "x"]),
    Example('"aaa\\\\\\\\"" x', ['aaa\\\\"', "x"]),
    Example('"aaa\\\\\\\\""" x', ['aaa\\\\" x']),
    Example('"aaa\\\\\\\\"""" x', ['aaa\\\\"', "x"]),
    Example('"aaa\\\\\\\\""""" x', ['aaa\\\\""', "x"]),
    Example('"aaa\\\\\\\\"""""" x', ['aaa\\\\"" x']),
    Example('"aaa\\\\\\\\""""""" x', ['aaa\\\\""', "x"]),
    Example('"aaa\\\\\\\\"""""""" x', ['aaa\\\\"""', "x"]),
    Example('"aaa\\\\\\\\""""""""" x', ['aaa\\\\""" x']),
    Example('"aaa\\\\\\\\"""""""""" x', ['aaa\\\\"""', "x"]),
    Example('"aaa\\\\\\\\""""""""""" x', ['aaa\\\\""""', "x"]),
    Example('"aaa\\\\\\\\"""""""""""" x', ['aaa\\\\"""" x']),
    Example(" x", ["x"]),
    Example('" x', [" x"]),
    Example('"" x', ["", "x"]),
    Example('""" x', ['"', "x"]),
    Example('"""" x', ['" x']),
    Example('""""" x', ['"', "x"]),
    Example('"""""" x', ['""', "x"]),
    Example('""""""" x', ['"" x']),
    Example('"""""""" x', ['""', "x"]),
    Example('""""""""" x', ['"""', "x"]),
    Example('"""""""""" x', ['""" x']),
    Example('""""""""""" x', ['"""', "x"]),
    Example('"""""""""""" x', ['""""', "x"]),
    Example("\\ x", ["\\", "x"]),
    Example('\\" x', ['"', "x"]),
    Example('\\"" x', ['" x']),
    Example('\\""" x', ['"', "x"]),
    Example('\\"""" x', ['""', "x"]),
    Example('\\""""" x', ['"" x']),
    Example('\\"""""" x', ['""', "x"]),
    Example('\\""""""" x', ['"""', "x"]),
    Example('\\"""""""" x', ['""" x']),
    Example('\\""""""""" x', ['"""', "x"]),
    Example('\\"""""""""" x', ['""""', "x"]),
    Example('\\""""""""""" x', ['"""" x']),
    Example('\\"""""""""""" x', ['""""', "x"]),
    Example("\\\\ x", ["\\\\", "x"]),
    Example('\\\\" x', ["\\ x"]),
    Example('\\\\"" x', ["\\", "x"]),
    Example('\\\\""" x', ['\\"', "x"]),
    Example('\\\\"""" x', ['\\" x']),
    Example('\\\\""""" x', ['\\"', "x"]),
    Example('\\\\"""""" x', ['\\""', "x"]),
    Example('\\\\""""""" x', ['\\"" x']),
    Example('\\\\"""""""" x', ['\\""', "x"]),
    Example('\\\\""""""""" x', ['\\"""', "x"]),
    Example('\\\\"""""""""" x', ['\\""" x']),
    Example('\\\\""""""""""" x', ['\\"""', "x"]),
    Example('\\\\"""""""""""" x', ['\\""""', "x"]),
    Example("\\\\\\ x", ["\\\\\\", "x"]),
    Example('\\\\\\" x', ['\\"', "x"]),
    Example('\\\\\\"" x', ['\\" x']),
    Example('\\\\\\""" x', ['\\"', "x"]),
    Example('\\\\\\"""" x', ['\\""', "x"]),
    Example('\\\\\\""""" x', ['\\"" x']),
    Example('\\\\\\"""""" x', ['\\""', "x"]),
    Example('\\\\\\""""""" x', ['\\"""', "x"]),
    Example('\\\\\\"""""""" x', ['\\""" x']),
    Example('\\\\\\""""""""" x', ['\\"""', "x"]),
    Example('\\\\\\"""""""""" x', ['\\""""', "x"]),
    Example('\\\\\\""""""""""" x', ['\\"""" x']),
    Example('\\\\\\"""""""""""" x', ['\\""""', "x"]),
    Example("\\\\\\\\ x", ["\\\\\\\\", "x"]),
    Example('\\\\\\\\" x', ["\\\\ x"]),
    Example('\\\\\\\\"" x', ["\\\\", "x"]),
    Example('\\\\\\\\""" x', ['\\\\"', "x"]),
    Example('\\\\\\\\"""" x', ['\\\\" x']),
    Example('\\\\\\\\""""" x', ['\\\\"', "x"]),
    Example('\\\\\\\\"""""" x', ['\\\\""', "x"]),
    Example('\\\\\\\\""""""" x', ['\\\\"" x']),
    Example('\\\\\\\\"""""""" x', ['\\\\""', "x"]),
    Example('\\\\\\\\""""""""" x', ['\\\\"""', "x"]),
    Example('\\\\\\\\"""""""""" x', ['\\\\""" x']),
    Example('\\\\\\\\""""""""""" x', ['\\\\"""', "x"]),
    Example('\\\\\\\\"""""""""""" x', ['\\\\""""', "x"]),
    Example('"x"', ["x"]),
    Example('"^x"', ["^x"]),
    Example('"^^x"', ["^^x"]),
    Example('"x', ["x"]),
    Example('"^x', ["^x"]),
    Example('"^^x', ["^^x"]),
    Example('"', [""]),
    Example('"^', ["^"]),
    Example('"^^', ["^^"]),
    Example('"^ ', ["^ "]),
    Example(":dir", [":dir"]),
    Example(";;;a,, b, c===", [";;;a,,", "b,", "c==="]),
    Example("^;;a", ["^;;a"], [";;a"]),
    Example('a "<>||&&', ["a", "<>||&&"]),
    Example('a "<>||&&^', ["a", "<>||&&^"]),
    Example('a "<>||&&^^', ["a", "<>||&&^^"]),
    Example('"foo &whoami bar"', ["foo &whoami bar"]),
    Example("^^", ["^^"], ["^"]),
    Example('"^"', ["^"]),
    Example('"^^"', ["^^"]),
    Example("foo^bar", ["foo^bar"], ["foobar"]),
    Example("foo^^bar", ["foo^^bar"], ["foo^bar"]),
    Example('"foo^bar"', ["foo^bar"]),
    Example('"foo^^bar"', ["foo^^bar"]),
    Example('"x"', ["x"]),
    Example('"^x"', ["^x"]),
    Example('"^^x"', ["^^x"]),
    Example('"x', ["x"]),
    Example('"^x', ["^x"]),
    Example('"^^x', ["^^x"]),
    Example('"', [""]),
    Example('"^', ["^"]),
    Example('"^^', ["^^"]),
    Example('"^ ', ["^ "]),
    Example(":dir", [":dir"]),
    Example(";;;a,, b, c===", [";;;a,,", "b,", "c==="]),
    Example('a "<>||&&', ["a", "<>||&&"]),
    Example('a "<>||&&^', ["a", "<>||&&^"]),
    Example('a "<>||&&^^', ["a", "<>||&&^^"]),
    Example("foo", ["foo"]),
    Example("foo^", ["foo^"], ["foo"]),
    Example("foo^^", ["foo^^"], ["foo^"]),
    Example("foo^^^", ["foo^^^"], ["foo^"]),
    Example("foo^^^^", ["foo^^^^"], ["foo^^"]),
    Example("foo^ bar", ["foo^", "bar"], ["foo", "bar"]),
    Example("foo^^ bar", ["foo^^", "bar"], ["foo^", "bar"]),
    Example("foo^^^ bar", ["foo^^^", "bar"], ["foo^", "bar"]),
    Example("foo^^^^ bar", ["foo^^^^", "bar"], ["foo^^", "bar"]),
    Example('"foo^" bar', ["foo^", "bar"], ["foo^", "bar"]),
    Example('"foo^^" bar', ["foo^^", "bar"], ["foo^^", "bar"]),
    Example('"foo^^^" bar', ["foo^^^", "bar"], ["foo^^^", "bar"]),
    Example('"foo^^^^" bar', ["foo^^^^", "bar"], ["foo^^^^", "bar"]),
]

pretty_examples = [
    (r"c:\Program Files\FooBar", r'"c:\Program Files\FooBar"'),
    (r"c:\Program Files (x86)\FooBar", r'"c:\Program Files (x86)\FooBar"'),
    (r"^", '"^"'),
    (r" ^", '" ^"'),
    (r"&", '"&"'),
    (r"!", "^!"),
    (r"!foo!", "^!foo^!"),
    ("foo\\bar\\baz\\", "foo\\bar\\baz\\"),
    ("foo bar\\baz\\", '"foo bar\\baz\\\\"'),
    ("foo () bar\\baz\\", '"foo () bar\\baz\\\\"'),
    ("foo () bar\\baz\\\\", '"foo () bar\\baz\\\\\\\\"'),
    ("foo () bar\\baz\\\\\\", '"foo () bar\\baz\\\\\\\\\\\\"'),
    ("foo () bar\\baz\\\\\\\\", '"foo () bar\\baz\\\\\\\\\\\\\\\\"'),
]


class TestMslex(unittest.TestCase):
    """Tests for `mslex` package."""

    def case(self, s: str, ans: str, cmd: bool) -> None:
        if sys.platform == "win32":
            win_split = cmd_split if cmd else ctypes_split
        try:
            if ans is not None:
                self.assertEqual(split(s, like_cmd=cmd), ans)
            if sys.platform == "win32":
                self.assertEqual(split(s, like_cmd=cmd), win_split(s))
        except AssertionError:
            print("in: «{}»".format(s))
            print()
            for x in split(s, like_cmd=cmd):
                print("out: «{}»".format(x))
            print()
            if ans is not None:
                for x in ans:
                    print("ans: «{}»".format(x))
                print()
            if sys.platform == "win32":
                for x in win_split(s):
                    print("win: «{}»".format(x))
                print()
            raise

    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    @unittest.skipUnless(sys.platform == "win32", "requires Windows")
    def test_every_string(self):
        def every_string():
            chars = [" ", "x", '"', "\\"]
            prod = itertools.product(*itertools.repeat(chars, 10))
            for x in prod:
                yield "".join(x)

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
                        s = ""
                    s += "\\" * m + '"' * n + " x"
                    self.case(s, None, False)

    def test_examples(self):
        for e in examples:
            self.case(e.input, e.output, cmd=False)

    def test_examples_for_cmd(self):
        for e in examples:
            self.case(e.input, e.cmd_output, cmd=True)

    def test_quote_examples(self):
        qu = functools.partial(quote, for_cmd=False)
        sp = functools.partial(split, like_cmd=False)
        for e in examples:
            self.assertEqual(e.output, sp(" ".join(map(qu, e.output))))
            if e.output == e.cmd_output:
                continue
            self.assertEqual(e.cmd_output, sp(" ".join(map(qu, e.cmd_output))))

    def test_quote_examples_cmd(self):
        for e in examples:
            self.assertEqual(e.output, split(" ".join(map(quote, e.output))))
            if e.output == e.cmd_output:
                continue
            self.assertEqual(e.cmd_output, split(" ".join(map(quote, e.cmd_output))))

    def test_requote_examples_cmd(self):
        for e in examples:
            self.assertEqual([e.input], split(quote(e.input)))

    def test_requote_examples(self):
        for e in examples:
            self.assertEqual([e.input], split(quote(e.input, for_cmd=False), like_cmd=False))

    def test_quote_every_string(self):
        def every_string():
            chars = [" ", "x", '"', "\\"]
            prod = itertools.product(*itertools.repeat(chars, 8))
            for x in prod:
                yield "".join(x)

        for s in every_string():
            q = quote(s, for_cmd=False)
            self.assertEqual([s], split(q, like_cmd=False))
            self.assertEqual([s, s], split("{} {}".format(q, q), like_cmd=False))

    def test_quote_every_string_for_cmd(self):
        def every_string():
            chars = [" ", "x", '"', "\\", "^", "&", "!"]
            prod = itertools.product(*itertools.repeat(chars, 6))
            for x in prod:
                yield "".join(x)

        for s in every_string():
            q = quote(s)
            self.assertEqual([s], split(q))
            self.assertEqual([s, s], split("{} {}".format(q, q)))

    @unittest.skipUnless(sys.platform == "win32", "requires Windows")
    def test_quote_every_string_using_cmd(self):
        def every_string():
            chars = [" ", "x", '"', "\\", "^", "&"]
            prod = itertools.product(*itertools.repeat(chars, 4))
            for x in prod:
                yield "".join(x)

        for s in every_string():
            q = quote(s)
            if sys.platform == "win32":
                proc = subprocess.run(
                    'python -c "import sys; print(sys.argv[1])" ' + q,
                    shell=True,
                    stdout=subprocess.PIPE,
                )
                self.assertEqual(proc.stdout.decode("ascii").rstrip(), s.rstrip())

    def test_pretty_examples(self):
        for s, ans in pretty_examples:
            self.assertEqual(quote(s), ans)
            self.assertEqual(split(ans), [s])
            self.assertEqual(split(ans + " " + ans + " foo bar"), [s, s, "foo", "bar"])
