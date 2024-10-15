#!/usr/bin/env python

import shutil
import os
import re
import json
import itertools
from dataclasses import dataclass
from pathlib import Path
from typing import *

import mslex
import trio
from tqdm import tqdm  # type: ignore

from test_mslex import CSVExample as Example  # type: ignore

chars = [" ", "x", '"', "\\", "^"]


def every_string() -> Iterable[str]:

    for qm in (True, False):
        for m in range(16):
            for n in range(16):
                if qm:
                    s = '"aaa'
                else:
                    s = ""
                yield s + "\\" * m + '"' * n + " x"

    for n in range(9):
        prod = itertools.product(*itertools.repeat(chars, n))
        for x in prod:
            yield "".join(x)


testdir = Path(__file__).parent

N = 32
limit = trio.Semaphore(N)


async def get_one(s: str) -> Example:
    cmd = mslex.quote(str(testdir / "cmdline.py")) + " " + s
    proc = await trio.run_process(cmd, check=True, capture_stdout=True, shell=True)
    j = json.loads(proc.stdout)
    cmdline, n = re.subn(r'^.*cmdline.py"\s*', "", j["GetCommandLineW"])
    assert n
    return Example(s, cmdline, j["CommandLineToArgvW"][2:], j["sys.argv"][1:])


async def main() -> None:
    examples: Dict[str, Example] = dict()

    csv_file = testdir / "examples.csv"
    if os.path.exists(csv_file):
        with open(csv_file, "r") as f:
            for line in f:
                e = Example.loads(line)
                examples[e.s] = e

    async def job(s) -> None:
        try:
            examples[s] = await get_one(s)
        finally:
            limit.release()

    def sync():
        tmp = csv_file.with_suffix(".tmp")
        with open(tmp, "w") as f:
            for e in sorted(examples.values(), key=lambda e: e.s):
                print(e.dumps(), file=f)
        shutil.copyfile(tmp, csv_file)

    total = sum(1 for s in every_string())

    try:
        async with trio.open_nursery() as spawning_pool:
            for s in tqdm(every_string(), total=total):
                await trio.sleep(0)
                if examples and len(examples) % 10000 == 0:
                    sync()
                if s in examples:
                    continue
                await limit.acquire()
                spawning_pool.start_soon(job, s)
    finally:
        sync()


if __name__ == "__main__":
    trio.run(main)
