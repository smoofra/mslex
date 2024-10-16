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
from pathlib import Path

from mslex import split, quote, split_msvcrt, split_ucrt, strip_carets_like_cmd, MSLexError

testdir = Path(__file__).parent

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

    def ctypes_split_exe(s):
        if s == "":
            return []
        argc = ctypes.c_int()
        argv = CommandLineToArgvW(s, ctypes.byref(argc))
        result = [argv[i] for i in range(argc.value)]
        LocalFree(argv)
        return result


def cmd_split(s: str) -> List[str]:
    assert sys.platform == "win32"
    script = os.path.join(os.path.dirname(__file__), "cmdline.py")
    cmdline = script + " " + s
    proc = subprocess.run(cmdline, shell=True, stdout=subprocess.PIPE, check=True)
    args = json.loads(proc.stdout)["CommandLineToArgvW"]
    return args[2:]  # first two args are "python.exe cmdline.py"


class CSVExample:

    def __init__(self, s: str, cmdline: str, split_msvcrt: List[str], split_ucrt: List[str]):
        self.s = s
        self.cmdline = cmdline
        self.split_msvcrt = split_msvcrt
        self.split_ucrt = split_ucrt

    @staticmethod
    def split_argv(s: str) -> List[str]:
        if not s:
            return []
        return s.removesuffix(";").split(";")

    @staticmethod
    def join_argv(v: List[str]) -> str:
        if not v:
            return ""
        return ";".join(v) + ";"

    @classmethod
    def loads(cls, line: str):
        (s, cmdline, *splits, _) = line.split(",")
        (split_msvcrt, split_ucrt) = map(cls.split_argv, splits)
        return cls(s, cmdline, split_msvcrt, split_ucrt)

    def dumps(self):
        msvcrt = self.join_argv(self.split_msvcrt)
        ucrt = self.join_argv(self.split_ucrt)
        return ",".join([self.s, self.cmdline, msvcrt, ucrt, ""])


class Example:
    def __init__(
        self,
        input: str,
        output: List[str],
        cmd: Optional[List[str]] = None,
        ucrt: Optional[List[str]] = None,
    ):
        self.input = input
        self.output = output
        self.cmd_output = cmd if cmd is not None else output
        self.ucrt_output = ucrt if ucrt is not None else output
        if cmd:
            self.ucrt_cmd_output = cmd
        elif ucrt:
            self.ucrt_cmd_output = ucrt
        else:
            self.ucrt_cmd_output = output


examples = [
    Example("", []),
    Example('"', [""]),
    Example('""', [""]),
    Example('"""', ['"']),
    Example('""""', ['"']),
    Example('"""""', ['"'], ucrt=['""']),
    Example('""""""', ['""']),
    Example('"""""""', ['""'], ucrt=['"""']),
    Example('""""""""', ['""'], ucrt=['"""']),
    Example('"""""""""', ['"""'], ucrt=['""""']),
    Example('""""""""""', ['"""'], ucrt=['""""']),
    Example(' "', [""]),
    Example(' ""', [""]),
    Example(' """', ['"']),
    Example(' """"', ['"']),
    Example(' """""', ['"'], ucrt=['""']),
    Example(' """"""', ['""']),
    Example(' """""""', ['""'], ucrt=['"""']),
    Example(' """"""""', ['""'], ucrt=['"""']),
    Example(' """"""""""', ['"""'], ucrt=['""""']),
    Example(" ", []),
    Example('" ', [" "]),
    Example('"" ', [""]),
    Example('""" ', ['"'], ucrt=['" ']),
    Example('"""" ', ['" '], ucrt=['"']),
    Example('""""" ', ['"'], ucrt=['"" ']),
    Example('"""""" ', ['""'], ucrt=['""']),
    Example('""""""" ', ['"" '], ucrt=['""" ']),
    Example('"""""""" ', ['""'], ucrt=['"""']),
    Example('""""""""" ', ['"""'], ucrt=['"""" ']),
    Example('"""""""""" ', ['""" '], ucrt=['""""']),
    Example("x", ["x"]),
    Example('x"', ["x"]),
    Example("foo", ["foo"]),
    Example('foo    "bar baz"', ["foo", "bar baz"]),
    Example('"abc" d e', ["abc", "d", "e"]),
    Example(r'"a\bc" d e', [r"a\bc", "d", "e"]),
    Example(r'a\\\b d"e f"g h', [r"a\\\b", "de fg", "h"]),
    Example(r"a\\\"b c d", [r"a\"b", "c", "d"]),
    Example(r'a\\\\"b c" d e', [r"a\\b c", "d", "e"]),
    Example('"" "" ""', ["", "", ""]),
    Example(" x", ["x"]),
    Example('" x', [" x"]),
    Example('"" x', ["", "x"]),
    Example('""" x', ['"', "x"], ucrt=['" x']),
    Example('"""" x', ['" x'], ucrt=['"', "x"]),
    Example('""""" x', ['"', "x"], ucrt=['"" x']),
    Example('"""""" x', ['""', "x"], ucrt=['""', "x"]),
    Example('""""""" x', ['"" x'], ucrt=['""" x']),
    Example('"""""""" x', ['""', "x"], ucrt=['"""', "x"]),
    Example('""""""""" x', ['"""', "x"], ucrt=['"""" x']),
    Example('"""""""""" x', ['""" x'], ucrt=['""""', "x"]),
    Example('""""""""""" x', ['"""', "x"], ucrt=['""""" x']),
    Example('"""""""""""" x', ['""""', "x"], ucrt=['"""""', "x"]),
    Example('""""""""""""" x', ['"""" x'], ucrt=['"""""" x']),
    Example('"aaa x', ["aaa x"]),
    Example('"aaa" x', ["aaa", "x"]),
    Example('"aaa"" x', ['aaa"', "x"], ucrt=['aaa" x']),
    Example('"aaa""" x', ['aaa" x'], ucrt=['aaa"', "x"]),
    Example('"aaa"""" x', ['aaa"', "x"], ucrt=['aaa"" x']),
    Example('"aaa""""" x', ['aaa""', "x"]),
    Example('"aaa"""""" x', ['aaa"" x'], ucrt=['aaa""" x']),
    Example('"aaa""""""" x', ['aaa""', "x"], ucrt=['aaa"""', "x"]),
    Example('"aaa"""""""" x', ['aaa"""', "x"], ucrt=['aaa"""" x']),
    Example('"aaa""""""""" x', ['aaa""" x'], ucrt=['aaa""""', "x"]),
    Example('"aaa"""""""""" x', ['aaa"""', "x"], ucrt=['aaa""""" x']),
    Example('"aaa""""""""""" x', ['aaa""""', "x"], ucrt=['aaa"""""', "x"]),
    Example('"aaa"""""""""""" x', ['aaa"""" x'], ucrt=['aaa"""""" x']),
    Example('"aaa\\ x', ["aaa\\ x"]),
    Example('"aaa\\" x', ['aaa" x']),
    Example('"aaa\\"" x', ['aaa"', "x"]),
    Example('"aaa\\""" x', ['aaa""', "x"], ucrt=['aaa"" x']),
    Example('"aaa\\"""" x', ['aaa"" x'], ucrt=['aaa""', "x"]),
    Example('"aaa\\""""" x', ['aaa""', "x"], ucrt=['aaa""" x']),
    Example('"aaa\\"""""" x', ['aaa"""', "x"]),
    Example('"aaa\\""""""" x', ['aaa""" x'], ucrt=['aaa"""" x']),
    Example('"aaa\\"""""""" x', ['aaa"""', "x"], ucrt=['aaa""""', "x"]),
    Example('"aaa\\""""""""" x', ['aaa""""', "x"], ucrt=['aaa""""" x']),
    Example('"aaa\\"""""""""" x', ['aaa"""" x'], ucrt=['aaa"""""', "x"]),
    Example('"aaa\\""""""""""" x', ['aaa""""', "x"], ucrt=['aaa"""""" x']),
    Example('"aaa\\"""""""""""" x', ['aaa"""""', "x"], ucrt=['aaa""""""', "x"]),
    Example('"aaa\\\\ x', ["aaa\\\\ x"]),
    Example('"aaa\\\\" x', ["aaa\\", "x"]),
    Example('"aaa\\\\"" x', ['aaa\\"', "x"], ucrt=['aaa\\" x']),
    Example('"aaa\\\\""" x', ['aaa\\" x'], ucrt=['aaa\\"', "x"]),
    Example('"aaa\\\\"""" x', ['aaa\\"', "x"], ucrt=['aaa\\"" x']),
    Example('"aaa\\\\""""" x', ['aaa\\""', "x"]),
    Example('"aaa\\\\"""""" x', ['aaa\\"" x'], ucrt=['aaa\\""" x']),
    Example('"aaa\\\\""""""" x', ['aaa\\""', "x"], ucrt=['aaa\\"""', "x"]),
    Example('"aaa\\\\"""""""" x', ['aaa\\"""', "x"], ucrt=['aaa\\"""" x']),
    Example('"aaa\\\\""""""""" x', ['aaa\\""" x'], ucrt=['aaa\\""""', "x"]),
    Example('"aaa\\\\"""""""""" x', ['aaa\\"""', "x"], ucrt=['aaa\\""""" x']),
    Example('"aaa\\\\""""""""""" x', ['aaa\\""""', "x"], ucrt=['aaa\\"""""', "x"]),
    Example('"aaa\\\\"""""""""""" x', ['aaa\\"""" x'], ucrt=['aaa\\"""""" x']),
    Example('"aaa\\\\\\ x', ["aaa\\\\\\ x"]),
    Example('"aaa\\\\\\" x', ['aaa\\" x']),
    Example('"aaa\\\\\\"" x', ['aaa\\"', "x"]),
    Example('"aaa\\\\\\""" x', ['aaa\\""', "x"], ucrt=['aaa\\"" x']),
    Example('"aaa\\\\\\"""" x', ['aaa\\"" x'], ucrt=['aaa\\""', "x"]),
    Example('"aaa\\\\\\""""" x', ['aaa\\""', "x"], ucrt=['aaa\\""" x']),
    Example('"aaa\\\\\\"""""" x', ['aaa\\"""', "x"]),
    Example('"aaa\\\\\\""""""" x', ['aaa\\""" x'], ucrt=['aaa\\"""" x']),
    Example('"aaa\\\\\\"""""""" x', ['aaa\\"""', "x"], ucrt=['aaa\\""""', "x"]),
    Example('"aaa\\\\\\""""""""" x', ['aaa\\""""', "x"], ucrt=['aaa\\""""" x']),
    Example('"aaa\\\\\\"""""""""" x', ['aaa\\"""" x'], ucrt=['aaa\\"""""', "x"]),
    Example('"aaa\\\\\\""""""""""" x', ['aaa\\""""', "x"], ucrt=['aaa\\"""""" x']),
    Example('"aaa\\\\\\"""""""""""" x', ['aaa\\"""""', "x"], ucrt=['aaa\\""""""', "x"]),
    Example('"aaa\\\\\\\\ x', ["aaa\\\\\\\\ x"]),
    Example('"aaa\\\\\\\\" x', ["aaa\\\\", "x"]),
    Example('"aaa\\\\\\\\"" x', ['aaa\\\\"', "x"], ucrt=['aaa\\\\" x']),
    Example('"aaa\\\\\\\\""" x', ['aaa\\\\" x'], ucrt=['aaa\\\\"', "x"]),
    Example('"aaa\\\\\\\\"""" x', ['aaa\\\\"', "x"], ucrt=['aaa\\\\"" x']),
    Example('"aaa\\\\\\\\""""" x', ['aaa\\\\""', "x"]),
    Example('"aaa\\\\\\\\"""""" x', ['aaa\\\\"" x'], ucrt=['aaa\\\\""" x']),
    Example('"aaa\\\\\\\\""""""" x', ['aaa\\\\""', "x"], ucrt=['aaa\\\\"""', "x"]),
    Example('"aaa\\\\\\\\"""""""" x', ['aaa\\\\"""', "x"], ucrt=['aaa\\\\"""" x']),
    Example('"aaa\\\\\\\\""""""""" x', ['aaa\\\\""" x'], ucrt=['aaa\\\\""""', "x"]),
    Example('"aaa\\\\\\\\"""""""""" x', ['aaa\\\\"""', "x"], ucrt=['aaa\\\\""""" x']),
    Example('"aaa\\\\\\\\""""""""""" x', ['aaa\\\\""""', "x"], ucrt=['aaa\\\\"""""', "x"]),
    Example('"aaa\\\\\\\\"""""""""""" x', ['aaa\\\\"""" x'], ucrt=['aaa\\\\"""""" x']),
    Example("\\ x", ["\\", "x"]),
    Example('\\" x', ['"', "x"]),
    Example('\\"" x', ['" x']),
    Example('\\""" x', ['"', "x"]),
    Example('\\"""" x', ['""', "x"], ucrt=['"" x']),
    Example('\\""""" x', ['"" x'], ucrt=['""', "x"]),
    Example('\\"""""" x', ['""', "x"], ucrt=['""" x']),
    Example('\\""""""" x', ['"""', "x"]),
    Example('\\"""""""" x', ['""" x'], ucrt=['"""" x']),
    Example('\\""""""""" x', ['"""', "x"], ucrt=['""""', "x"]),
    Example('\\"""""""""" x', ['""""', "x"], ucrt=['""""" x']),
    Example('\\""""""""""" x', ['"""" x'], ucrt=['"""""', "x"]),
    Example('\\"""""""""""" x', ['""""', "x"], ucrt=['"""""" x']),
    Example("\\\\ x", ["\\\\", "x"]),
    Example('\\\\" x', ["\\ x"]),
    Example('\\\\"" x', ["\\", "x"]),
    Example('\\\\""" x', ['\\"', "x"], ucrt=['\\" x']),
    Example('\\\\"""" x', ['\\" x'], ucrt=['\\"', "x"]),
    Example('\\\\""""" x', ['\\"', "x"], ucrt=['\\"" x']),
    Example('\\\\"""""" x', ['\\""', "x"]),
    Example('\\\\""""""" x', ['\\"" x'], ucrt=['\\""" x']),
    Example('\\\\"""""""" x', ['\\""', "x"], ucrt=['\\"""', "x"]),
    Example('\\\\""""""""" x', ['\\"""', "x"], ucrt=['\\"""" x']),
    Example('\\\\"""""""""" x', ['\\""" x'], ucrt=['\\""""', "x"]),
    Example('\\\\""""""""""" x', ['\\"""', "x"], ucrt=['\\""""" x']),
    Example('\\\\"""""""""""" x', ['\\""""', "x"], ucrt=['\\"""""', "x"]),
    Example("\\\\\\ x", ["\\\\\\", "x"]),
    Example('\\\\\\" x', ['\\"', "x"]),
    Example('\\\\\\"" x', ['\\" x']),
    Example('\\\\\\""" x', ['\\"', "x"]),
    Example('\\\\\\"""" x', ['\\""', "x"], ucrt=['\\"" x']),
    Example('\\\\\\""""" x', ['\\"" x'], ucrt=['\\""', "x"]),
    Example('\\\\\\"""""" x', ['\\""', "x"], ucrt=['\\""" x']),
    Example('\\\\\\""""""" x', ['\\"""', "x"]),
    Example('\\\\\\"""""""" x', ['\\""" x'], ucrt=['\\"""" x']),
    Example('\\\\\\""""""""" x', ['\\"""', "x"], ucrt=['\\""""', "x"]),
    Example('\\\\\\"""""""""" x', ['\\""""', "x"], ucrt=['\\""""" x']),
    Example('\\\\\\""""""""""" x', ['\\"""" x'], ucrt=['\\"""""', "x"]),
    Example('\\\\\\"""""""""""" x', ['\\""""', "x"], ucrt=['\\"""""" x']),
    Example("\\\\\\\\ x", ["\\\\\\\\", "x"]),
    Example('\\\\\\\\" x', ["\\\\ x"]),
    Example('\\\\\\\\"" x', ["\\\\", "x"]),
    Example('\\\\\\\\""" x', ['\\\\"', "x"], ucrt=['\\\\" x']),
    Example('\\\\\\\\"""" x', ['\\\\" x'], ucrt=['\\\\"', "x"]),
    Example('\\\\\\\\""""" x', ['\\\\"', "x"], ucrt=['\\\\"" x']),
    Example('\\\\\\\\"""""" x', ['\\\\""', "x"]),
    Example('\\\\\\\\""""""" x', ['\\\\"" x'], ucrt=['\\\\""" x']),
    Example('\\\\\\\\"""""""" x', ['\\\\""', "x"], ucrt=['\\\\"""', "x"]),
    Example('\\\\\\\\""""""""" x', ['\\\\"""', "x"], ucrt=['\\\\"""" x']),
    Example('\\\\\\\\"""""""""" x', ['\\\\""" x'], ucrt=['\\\\""""', "x"]),
    Example('\\\\\\\\""""""""""" x', ['\\\\"""', "x"], ucrt=['\\\\""""" x']),
    Example('\\\\\\\\"""""""""""" x', ['\\\\""""', "x"], ucrt=['\\\\"""""', "x"]),
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
    Example("^;;a", ["^;;a"], cmd=[";;a"]),
    Example('a "<>||&&', ["a", "<>||&&"]),
    Example('a "<>||&&^', ["a", "<>||&&^"]),
    Example('a "<>||&&^^', ["a", "<>||&&^^"]),
    Example('"foo &whoami bar"', ["foo &whoami bar"]),
    Example("^^", ["^^"], cmd=["^"]),
    Example('"^"', ["^"]),
    Example('"^^"', ["^^"]),
    Example("foo^bar", ["foo^bar"], cmd=["foobar"]),
    Example("foo^^bar", ["foo^^bar"], cmd=["foo^bar"]),
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
    Example("foo^", ["foo^"], cmd=["foo"]),
    Example("foo^^", ["foo^^"], cmd=["foo^"]),
    Example("foo^^^", ["foo^^^"], cmd=["foo^"]),
    Example("foo^^^^", ["foo^^^^"], cmd=["foo^^"]),
    Example("foo^ bar", ["foo^", "bar"], cmd=["foo", "bar"]),
    Example("foo^^ bar", ["foo^^", "bar"], cmd=["foo^", "bar"]),
    Example("foo^^^ bar", ["foo^^^", "bar"], cmd=["foo^", "bar"]),
    Example("foo^^^^ bar", ["foo^^^^", "bar"], cmd=["foo^^", "bar"]),
    Example('"foo^" bar', ["foo^", "bar"], cmd=["foo^", "bar"]),
    Example('"foo^^" bar', ["foo^^", "bar"], cmd=["foo^^", "bar"]),
    Example('"foo^^^" bar', ["foo^^^", "bar"], cmd=["foo^^^", "bar"]),
    Example('"foo^^^^" bar', ["foo^^^^", "bar"], cmd=["foo^^^^", "bar"]),
]

pretty_examples = [
    (r"c:\Program Files\FooBar", r'"c:\Program Files\FooBar"'),
    (r"c:\Program Files (x86)\FooBar", r'"c:\Program Files (x86)\FooBar"'),
    ("^", "^^"),
    (" ^", '" ^"'),
    ("&", "^&"),
    ("!", "^!"),
    (r"%foo%", r"^%foo^%"),
    ("!foo!", "^!foo^!"),
    ("foo bar!", '"foo bar"^!'),
    ("!foo bar!", '^!"foo bar"^!'),
    ("foo\\bar\\baz\\", "foo\\bar\\baz\\"),
    ("foo bar\\baz\\", '"foo bar\\baz\\\\"'),
    ("foo () bar\\baz\\", '"foo () bar\\baz\\\\"'),
    ("foo () bar\\baz\\\\", '"foo () bar\\baz\\\\\\\\"'),
    ("foo () bar\\baz\\\\\\", '"foo () bar\\baz\\\\\\\\\\\\"'),
    ("foo () bar\\baz\\\\\\\\", '"foo () bar\\baz\\\\\\\\\\\\\\\\"'),
    (r"foo\bar! baz", r'foo\bar^!" baz"'),
    (r"x\!", r"x\^!"),
    ("foo\\", "foo\\"),
    ("\\", "\\"),
]

pretty_examples_not_cmd = [
    ("\\", "\\"),
    ("foo", "foo"),
    ("foo\\", "foo\\"),
    ("foo!", "foo!"),
    ("foo bar", '"foo bar"'),
    (r"foo\bar", r"foo\bar"),
    (r'foo"bar', r"foo\"bar"),
]


class TestMslex(unittest.TestCase):
    """Tests for `mslex` package."""

    def case(
        self, s: str, ans: str, cmd: bool, exe: bool = False, ucrt: Optional[bool] = None
    ) -> None:
        assert not (cmd and exe)
        if sys.platform == "win32":
            win_split = cmd_split if cmd else ctypes_split
            if exe:
                win_split = ctypes_split_exe
        try:
            v = split(s, like_cmd=cmd, ucrt=ucrt)
            if ans is not None:
                self.assertEqual(v, ans)
            if sys.platform == "win32" and not ucrt:
                self.assertEqual(v, win_split(s))
        except (MSLexError, AssertionError):
            print("in: «{}»".format(s))
            print()
            for x in split(s, like_cmd=cmd, ucrt=ucrt):
                print("out: «{}»".format(x))
            print()
            if ans is not None:
                for x in ans:
                    print("ans: «{}»".format(x))
                print()
            if sys.platform == "win32" and not ucrt:
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
            self.case(s, None, cmd=False, ucrt=False)

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
                    self.case(s, None, cmd=False, ucrt=False)

    def test_examples(self):
        for e in examples:
            try:
                self.case(e.input, e.output, cmd=False)
            except MSLexError as err:
                assert e.output != e.ucrt_output
                assert "String is ambiguous" in str(err)
            else:
                assert e.output == e.ucrt_output

    def test_examples_ucrt(self):
        for e in examples:
            self.case(e.input, e.ucrt_output, cmd=False, ucrt=True)

    def test_examples_for_cmd(self):
        for e in examples:
            try:
                self.case(e.input, e.cmd_output, cmd=True)
            except MSLexError as err:
                assert e.cmd_output != e.ucrt_cmd_output
                assert "String is ambiguous" in str(err)
            else:
                assert e.cmd_output == e.ucrt_cmd_output

    def test_examples_for_cmd_ucrt(self):
        for e in examples:
            self.case(e.input, e.ucrt_cmd_output, cmd=True, ucrt=True)

    def test_quote_examples(self):
        qu = functools.partial(quote, for_cmd=False)
        sp = functools.partial(split, like_cmd=False)
        for e in examples:
            try:
                output = e.output
                self.assertEqual(e.output, sp(" ".join(map(qu, output))))
                if e.output == e.cmd_output:
                    continue
                output = e.cmd_output
                self.assertEqual(e.cmd_output, sp(" ".join(map(qu, output))))
            except AssertionError:
                print("in: «{}»".format(output))
                print("quoted: «{}»".format(quote(output)))
                raise

    def test_quote_examples_cmd(self):
        for e in examples:
            try:
                output = e.output
                self.assertEqual(e.output, split(" ".join(map(quote, output))))
                if e.output == e.cmd_output:
                    continue
                output = e.cmd_output
                self.assertEqual(e.cmd_output, split(" ".join(map(quote, output))))
            except AssertionError:
                print("in: «{}»".format(output))
                print("quoted: «{}»".format(quote(output)))
                raise

    def test_requote_examples_cmd(self):
        for e in examples:
            try:
                self.assertEqual([e.input], split(quote(e.input)))
            except AssertionError:
                print("in: «{}»".format(e.input))
                print("quoted: «{}»".format(quote(e.input)))
                for i, s in enumerate(split(quote(e.input))):
                    print("split[{}]: «{}»".format(i, s))
                raise

    def test_requote_examples(self):
        for e in examples:
            try:
                self.assertEqual([e.input], split(quote(e.input, for_cmd=False), like_cmd=False))
            except AssertionError:
                print("in: «{}»".format(e.input))
                print("quoted: «{}»".format(quote(e.input, for_cmd=False)))
                raise

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
            try:
                q = quote(s)
                self.assertEqual([s], split(q))
                self.assertEqual([s, s], split("{} {}".format(q, q)))
            except AssertionError:
                print("in: «{}»".format(s))
                print("quoted: «{}»".format(q))
                raise

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
            try:
                self.assertEqual(quote(s), ans)
                self.assertEqual(split(ans), [s])
                self.assertEqual(split(ans + " " + ans + " foo bar"), [s, s, "foo", "bar"])
            except AssertionError:
                print("in: «{}»".format(s))
                print("quoted: «{}»".format(quote(s)))
                print("expected: «{}»".format(ans))
                raise

    def test_pretty_examples_not_cmd(self):
        for s, ans in pretty_examples_not_cmd:
            try:
                self.assertEqual(quote(s, for_cmd=False), ans)
                self.assertEqual(split(ans, like_cmd=False), [s])
                self.assertEqual(split(ans + " " + ans, like_cmd=False), [s, s])
            except AssertionError:
                print("in: «{}»".format(s))
                print("quoted: «{}»".format(quote(s)))
                print("expected: «{}»".format(ans))
                raise

    def test_examples_csv(self):
        csv = testdir / "examples.csv"
        if not csv.exists():
            self.skipTest("%s missing.  clone from github" % csv)
        with open(str(csv), "r") as f:
            if next(iter(f)).startswith("version https://git-lfs.github.com/spec/"):
                self.skipTest("%s not downloaded.  turn on git-lfs." % csv)
        with open(str(csv), "r") as f:
            for line in f:
                try:
                    e = CSVExample.loads(line)
                    self.assertEqual(e.split_ucrt, split_ucrt(e.cmdline))
                    self.assertEqual(e.split_msvcrt, split_msvcrt(e.cmdline))
                    try:
                        self.assertEqual(e.split_msvcrt, split(e.s))
                    except MSLexError as err:
                        assert "ambiguous" in str(err)
                        assert e.split_ucrt != e.split_msvcrt
                    else:
                        assert e.split_ucrt == e.split_msvcrt
                    self.assertEqual(e.cmdline.lstrip(), strip_carets_like_cmd(e.s).lstrip())
                    q = quote(e.s)
                    self.assertEqual([e.s], split(q))
                    self.assertEqual([e.s, e.s], split(q + " " + q))
                    q = quote(e.s, for_cmd=False)
                    self.assertEqual([e.s], split(q, like_cmd=False))
                    self.assertEqual([e.s, e.s], split(q + " " + q, like_cmd=False))
                except AssertionError:
                    print("s: «{}»".format(e.s))
                    print("cmdline: «{}»".format(e.cmdline))
                    try:
                        print("q: «{}»".format(q))
                    except NameError:
                        pass
                    raise

    def test_unquoted(self):
        bad = [
            "foo && bar",
            "foo || bar",
            "foo >bar",
            "foo <bar",
            "&whoami",
            "!foo!",
            r"%foo%",
            '"!foo!"',
            '"^!foo!"',
            '"^!foo^!"',
            r'"%foo%"',
            r'"^%foo%"',
            r'"^%foo^%"',
            "(foo)",
        ]
        for s in bad:
            try:
                split(s)
            except MSLexError as err:
                assert "Unquoted CMD metacharacters" in str(err)
            else:
                print("s: «{}»".format(s))
                print("stripped: «{}»".format(strip_carets_like_cmd(s)))
                self.fail("expected exception")
        good = [
            '"foo && bar"',
            '"foo || bar"',
            'foo ">bar"',
            'foo "<bar"',
            '"&whoami"',
            "^!foo^!",
            r"^%foo^%",
            '^!"foo"^!',
            r'^%"foo"^%',
            '"(foo)"',
        ]
        for s in good:
            split(s)
