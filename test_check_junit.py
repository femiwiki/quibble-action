# Tests for check_junit.py, the coverage stage's only record of whether its
# PHPUnit run passed. Its failure paths are what the stage rests on, so they
# are exercised here rather than left to the happy path CI already runs.
#
# The reports below keep the shape PHPUnit 9.6 emits: one <testsuite> per
# --testsuite argument directly under <testsuites>, carrying the totals of
# everything nested below it, and a second <testsuite> per class repeating
# them.
import subprocess
import sys
import tempfile
import os

CHECKER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'check_junit.py')


def report(tests, failures, errors):
    attributes = f'tests="{tests}" assertions="{tests}" errors="{errors}" warnings="0" failures="{failures}" skipped="0" time="0.1"'
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<testsuites>\n'
        f'  <testsuite name="/workspace/src/extensions/Foo" {attributes}>\n'
        f'    <testsuite name="FooTest" file="/workspace/src/extensions/Foo/tests/phpunit/FooTest.php" {attributes}/>\n'
        '  </testsuite>\n'
        '</testsuites>\n'
    )


def check(content):
    """Return the exit status check_junit.py gives a report, or None for no report at all."""
    with tempfile.TemporaryDirectory() as directory:
        path = os.path.join(directory, 'junit.xml')
        if content is not None:
            with open(path, 'w') as f:
                f.write(content)
        return subprocess.run([sys.executable, CHECKER, path], capture_output=True).returncode


CASES = [
    ('a clean run passes', report(3, 0, 0), 0),
    ('a skipped test is not a failure', report(3, 0, 0).replace('skipped="0"', 'skipped="3"'), 0),
    ('a failing test fails', report(3, 1, 0), 1),
    ('an erroring test fails', report(3, 0, 1), 1),
    ('both at once fails', report(3, 1, 1), 1),
    ('a run that collected nothing fails', report(0, 0, 0), 1),
    ('an empty report fails', '<?xml version="1.0"?>\n<testsuites/>\n', 1),
    ('a truncated report fails', report(3, 0, 0)[:120], 1),
    ('a missing report fails', None, 1),
]


def main():
    failed = 0
    for name, content, expected in CASES:
        actual = check(content)
        if actual != expected:
            print(f'FAIL: {name}: expected exit {expected}, got {actual}')
            failed += 1
        else:
            print(f'ok: {name}')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
