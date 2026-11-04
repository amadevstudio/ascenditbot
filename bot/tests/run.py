"""Runs the bench cases: every `async def test_*(bench)` in tests/test_*.py, each on a clean database.

    python tests/run.py            # all of them
    python tests/run.py notice     # those whose module, name or description contains "notice"

Meant to run in docker-compose.test.yml (it needs the test Postgres and Redis): ./scripts/test.sh
"""
import asyncio
import importlib
import inspect
import os
import sys
import time
import traceback

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(TESTS_DIR))  # the bot's root, as when main.py runs


def collect(filters: list[str]):
    cases = []
    for file_name in sorted(os.listdir(TESTS_DIR)):
        if not (file_name.startswith('test_') and file_name.endswith('.py')):
            continue
        module = importlib.import_module(f'tests.{file_name[:-3]}')
        for name, function in inspect.getmembers(module, inspect.iscoroutinefunction):
            if not name.startswith('test_') or function.__module__ != module.__name__:
                continue
            description = inspect.getdoc(function) or name
            label = f'{file_name[5:-3]}: {description}'
            if filters and not any(f.lower() in f'{label} {name}'.lower() for f in filters):
                continue
            cases.append((inspect.getsourcelines(function)[1], module.__name__, label, function))
    cases.sort(key=lambda case: (case[1], case[0]))
    return [(label, function) for _, _, label, function in cases]


async def main(filters: list[str]) -> int:
    from tests.bench import Bench

    bench = await Bench.start()
    cases = collect(filters)
    failed = []
    started = time.monotonic()

    for label, function in cases:
        await bench.reset()
        try:
            await function(bench)
        except Exception:
            failed.append(label)
            print(f'FAIL {label}\n{traceback.format_exc()}', flush=True)
        else:
            print(f'ok   {label}', flush=True)

    print(f'\n{len(cases) - len(failed)} of {len(cases)} passed in {time.monotonic() - started:.1f} s')
    if not cases:
        print('no cases matched')
        return 1
    for label in failed:
        print(f'  failed: {label}')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(asyncio.run(main(sys.argv[1:])))
