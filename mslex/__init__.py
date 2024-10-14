# -*- coding: utf-8 -*-

"""
On windows, before a command line argument becomes a ``char*`` in a
program's argv, it must be parsed by both ``cmd.exe``, and by
``CommandLineToArgvW``.

For some strings there is no way to quote them so they will
parse correctly in both situations.
"""

import sys
import re
import itertools

from typing import Iterator, List, Match, TextIO, Optional  # noqa: F401

from .exceptions import MSLexError

__all__ = (
    "split",
    "split_ucrt",
    "split_msvcrt",
    "strip_carets_like_cmd",
    "quote",
    "join",
    "MSLexError",
)

__version__ = "1.3.0"


def _iter_arg_msvcrt(peek: Match[str], i: Iterator[Match[str]]) -> Iterator[str]:
    quote_mode = False
    for m in itertools.chain([peek], i):
        space, slashes, quotes, text = m.groups()
        if space:
            if quote_mode:
                yield space
            else:
                return
        elif quotes:
            n_slashes = len(slashes)
            n_quotes = len(quotes)
            slashes_odd = bool(n_slashes % 2)
            yield "\\" * (n_slashes // 2)
            magic_sum = n_quotes + quote_mode + 2 * slashes_odd
            yield '"' * (magic_sum // 3)
            quote_mode = (magic_sum % 3) == 1
        else:
            yield text


def split_msvcrt(s: str) -> List[str]:
    """
    Split a string of command line options like `msvcrt.dll`_ does.

    :param s: a string to parse
    :return: a list of parsed words

    This parses arguments the same way `CommandLineToArgvW`_ does, except
    it does not treat ``argv[0]`` specially.

    Specifically, it is the same as ``CommandLineToArgvW("foo.exe " + s)[1:]``

    If the first word of ``s`` is a valid command name, then it cannot contain
    any quotes, so this is the same as ``CommandLineToArgvW(s)``

    .. _`CommandLineToArgvW`: https://learn.microsoft.com/en-us/windows/win32/api/shellapi\
        /nf-shellapi-commandlinetoargvw
    .. _`msvcrt.dll`: https://devblogs.microsoft.com/oldnewthing/20140411-00/?p=1273
    """
    i = re.finditer(r"(\s+)|(\\*)(\"+)|(.[^\s\\\"]*)", s.lstrip())
    return ["".join(_iter_arg_msvcrt(m, i)) for m in i]


def _iter_arg_ucrt(peek: Match[str], i: Iterator[Match[str]]) -> Iterator[str]:
    quote_mode = False
    for m in itertools.chain([peek], i):
        space, slashes, quotes, text = m.groups()
        if space:
            if quote_mode:
                yield space
            else:
                return
        elif quotes:
            if slashes:
                yield slashes[: len(slashes) // 2]
                if len(slashes) % 2:
                    yield '"'
                    quotes = quotes[1:]
            while quotes:
                if quote_mode and len(quotes) >= 2:
                    yield '"'
                    quotes = quotes[2:]
                else:
                    quote_mode = not quote_mode
                    quotes = quotes[1:]
        else:
            yield text


def split_ucrt(s: str) -> List[str]:
    """
    Split a string of command line options like `UCRT`_ does.

    :param s: a string to parse
    :return: a list of parsed words

    This should compute the same function that is used by a modern windows
    C runtime library to convert arguments in ``GetCommandLineW`` to
    individual arguments found in ``argv``, except it does not treat
    ``argv[0]`` specially.

    see: `Parsing C Command Line Arguments`_

    .. _`UCRT`: https://learn.microsoft.com/en-us/cpp/porting/\
        upgrade-your-code-to-the-universal-crt
    .. _`Parsing C Command Line Arguments`: https://learn.microsoft.com/en-us/cpp/c-language\
        /parsing-c-command-line-arguments
    """
    i = re.finditer(r"(\s+)|(\\*)(\"+)|(.[^\s\\\"]*)", s.lstrip())
    return ["".join(_iter_arg_ucrt(m, i)) for m in i]


cmd_meta = r"([\"\^\&\|\<\>\(\)\%\!])"
cmd_meta_or_space = r"[\s\"\^\&\|\<\>\(\)\%\!]"
cmd_meta_inside_quotes = r"([\"\%\!])"


def strip_carets_like_cmd(s: str, check: bool = True) -> str:
    """
    Interpret caret escaping like ``cmd.exe`` does.

    :param s: a command line string
    :param check: raise an error on unquoted metacharacters
    :returns: the string with any carets interpreted as an escape character
    """

    def i() -> Iterator[str]:
        quote_mode = False
        for m in re.finditer(r"(\^.?)|(\")|([^\^\"]+)", s):
            escaped, quote, text = m.groups()
            if escaped:
                if quote_mode:
                    yield escaped
                    if len(escaped) > 1:
                        if escaped[1] == '"':
                            quote_mode = False
                        elif check and escaped[1] in "!%":
                            raise MSLexError("Unquoted CMD metacharacters in string: " + repr(s))
                else:
                    yield escaped[1:]
            elif quote:
                yield '"'
                quote_mode = not quote_mode
            else:
                yield text
                if check:
                    meta = cmd_meta_inside_quotes if quote_mode else cmd_meta
                    if re.search(meta, text):
                        raise MSLexError("Unquoted CMD metacharacters in string: " + repr(s))

    return "".join(i())


def split(
    s: str, like_cmd: bool = True, check: bool = True, ucrt: Optional[bool] = None
) -> List[str]:
    """
    Split a string of command line arguments like DOS and Windows do.

    :param s: a string to parse
    :param like_cmd: parse it like ``cmd.exe``
    :param ucrt: parse like UCRT
    :param check: raise an error on unquoted metacharacters
    :return: a list of parsed words

    If ``like_cmd`` is true, then this will emulate both ``cmd.exe`` and
    ``CommandLineToArgvW``.   Since ``cmd.exe`` is a shell, and can run
    external programs, this function obviously cannot emulate everything it
    does.   However if the string passed in would be parsed by cmd as a
    quoted literal, without command invocations like ``&whoami``, and
    without string substitutions like ``%PATH%``, then this function will
    split it accurately.

    f ``like_cmd`` is false, then this will split the string like
    ``CommandLineToArgvW`` does.

    If ``check`` is true, this will raise a ``ValueError`` if cmd
    metacharacters occur in the string without being quoted.

    If ``ucrt`` is true, this will parse like a modern C runtime.   If it
    is false, then it will parse like ``msvcrt.dll``.  If it is None, then
    it will raise an exception if the two methods disagree.

    .. note:: This does not treat ``argv[0]`` specially as described in Microsoft's
      `documentation`_, because this function does not have any way of knowing
      if the first word of ``s`` is meant to be used as the program name.  If
      it is, then it should be a valid path name, so it can not contain
      quotes, so both methods of interpretation will give the same answer.

    .. _`documentation`: https://learn.microsoft.com/en-us/cpp/c-language/\
        parsing-c-command-line-arguments
    """
    if like_cmd and re.search(cmd_meta, s):
        s = strip_carets_like_cmd(s, check=check)

    if ucrt is None:
        v = split_ucrt(s)
        if v != split_msvcrt(s):
            raise MSLexError(
                "String is ambiguous, legacy and modern runtimes disagree: " + repr(s)
            )
        return v
    elif ucrt:
        return split_ucrt(s)
    else:
        return split_msvcrt(s)


def _escape_quotes(s: str) -> str:
    """
    Escape any quotes found in string by prefixing them with an appropriate
    number of backslashes.
    """

    i = re.finditer(r"(\\*)(\"+)|(\\+|[^\\\"]+)", s)

    def parts() -> Iterator[str]:
        for m in i:
            pos, end = m.span()
            slashes, quotes, text = m.groups()
            if quotes:
                yield slashes
                yield slashes
                yield r"\"" * len(quotes)
            else:
                yield text

    return "".join(parts())


def _wrap_in_quotes(s: str) -> str:
    """
    Wrap a string whose internal quotes have been escaped in double quotes.
    This handles adding the correct number of backslashes in front of the
    closing quote.
    """
    return '"' + re.sub(r"(\\+)$", r"\1\1", s) + '"'


def _quote_for_cmd(s: str) -> str:
    """
    Quote a string for cmd. Split the string into sections that can be
    quoted (or used verbatim), and runs of % and ! characters which must be
    escaped with carets outside of quotes, and runs of quote characters,
    which must be escaped with a caret for cmd.exe, and a backslash for
    CommandLineToArgvW.
    """

    def f(m) -> str:
        quotable, subst = m.groups()
        if quotable:
            # A trailing backslash could combine a backslash escaping a
            # quote, so it must be quoted
            if re.search(cmd_meta_or_space, quotable) or quotable.endswith("\\"):
                return _wrap_in_quotes(quotable)
            else:
                return quotable
        elif subst:
            return "^" + subst
        else:
            return '\\^"'

    return re.sub(r'([^\%\!\"]+)|([\%\!])|"', f, s)


def quote(s: str, for_cmd: bool = True) -> str:
    """
    Quote a string for use as a command line argument in DOS or Windows.

    :param s: a string to quote
    :param for_cmd: quote it for ``cmd.exe``
    :return: quoted string

    If ``for_cmd`` is true, then this will quote the strings so the result will
    be parsed correctly by ``cmd.exe`` and then by ``CommandLineToArgvW``.   If
    false, then this will quote the strings so the result will
    be parsed correctly when passed directly to ``CommandLineToArgvW``.
    """
    if not s:
        return '""'

    if for_cmd:
        if not re.search(cmd_meta_or_space, s):
            return s
        quoted = _quote_for_cmd(s)
        if not re.search(r"[\s\"]", s):
            # for example the string «x\!» can be quoted as «x\^!», but
            # _quote_for_cmd would quote it as «"x\\"^!»
            alt = re.sub(cmd_meta, r"^\1", s)
            if len(alt) < len(quoted):
                return alt
        return quoted
    else:
        if not re.search(r"\s", s):
            return _escape_quotes(s)
        return _wrap_in_quotes(_escape_quotes(s))


def join(split_command: List[str], for_cmd: bool = True) -> str:
    """
    Quote and concatenate a list of strings for use as a command line in DOS
    or Windows.

    :param split_command: a list of words to be quoted
    :param for_cmd: quote it for ``cmd.exe``
    :return: quoted command string

    If ``for_cmd`` is true, then this will quote the strings so the result will
    be parsed correctly by ``cmd.exe`` and then by ``CommandLineToArgvW``.   If
    false, then this will quote the strings so the result will
    be parsed correctly when passed directly to ``CommandLineToArgvW``.

    """
    return " ".join(quote(arg, for_cmd) for arg in split_command)


def split_cli() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="split a file into strings using windows-style quoting "
    )
    parser.add_argument("filename", nargs="?", help="file to split")
    args = parser.parse_args()

    if args.filename:
        input = open(args.filename, "r")  # type: TextIO
    else:
        input = sys.stdin

    for s in split(input.read(), like_cmd=False):
        print(s)
