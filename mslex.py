# -*- coding: utf-8 -*-

import sys
import re
import itertools

__all__ = ('split', 'quote')

__version__ = '0.1.0'

def iter_arg(peek, i):
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
            yield '\\' * (n_slashes // 2)
            magic_sum = n_quotes + quote_mode + 2*slashes_odd
            yield '"' * (magic_sum // 3)
            quote_mode = (magic_sum % 3) == 1
        else:
            yield text

def iter_args(s):
    i = re.finditer(r'(\s+)|(\\*)(\"+)|(.[^\s\\\"]*)', s.lstrip())
    for m in i:
        yield ''.join(iter_arg(m, i))

def split(s):
    return list(iter_args(s))

cmd_meta = r'[\s\"\^\&\|\<\>\(\)\%\!]'

cmd_meta_inside_quotes = r'[\%\!]'

def quote(s):
    if not s:
        return '""'
    if not re.search(cmd_meta, s):
        return s
    i = re.finditer(r'(\\*)(\"+)|(\\+)|([^\\\"]+)', s)
    def parts():
        yield '"'
        for m in i:
            pos,end = m.span()
            slashes, quotes, onlyslashes, text = m.groups()
            if quotes:
                yield slashes
                yield slashes
                yield r'\"' * len(quotes)
            elif onlyslashes:
                if end == len(s):
                    yield onlyslashes
                    yield onlyslashes
                else:
                    yield onlyslashes
            else:
                yield text
        yield '"'
    return ''.join(parts())

def split_cli():
    import argparse

    parser = argparse.ArgumentParser(
        description='split a file into strings using windows-style quoting ')
    parser.add_argument('filename', nargs='?',
                        help='file to split')
    args = parser.parse_args()

    if args.filename:
        input = open(args.filename, 'r')
    else:
        input = sys.stdin

    for s in iter_args(input.read()):
        print(s)
