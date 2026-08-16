# A script to fail the coverage stage when its PHPUnit run did not pass.
#
# Wikimedia's mwext-phpunit-coverage runs PHPUnit under `set +e`, so that a
# failing suite still publishes the report it produced, and it never looks at
# the exit code again. The container therefore exits 0 whatever PHPUnit did,
# and so does Quibble. The JUnit report is the only remaining record of the
# result, so read the totals off it and exit non-zero on anything but a clean
# run.
import sys
import xml.etree.ElementTree as etree


def totals(path):
    """Return the (tests, failures, errors) totals of a JUnit report."""
    root = etree.parse(path).getroot()
    # PHPUnit writes <testsuites> wrapping one <testsuite> per suite, each
    # carrying the totals of everything below it. Anything deeper is counted
    # twice.
    suites = root.findall('testsuite') if root.tag == 'testsuites' else [root]
    return tuple(
        sum(int(suite.get(attribute, 0)) for suite in suites)
        for attribute in ('tests', 'failures', 'errors')
    )


def main():
    path = sys.argv[1]
    try:
        tests, failures, errors = totals(path)
    except (OSError, etree.ParseError, ValueError) as e:
        print(f"::error::Cannot read the PHPUnit report of the coverage run ({path}): {e}")
        return 1
    if failures or errors:
        print(
            f"::error::The coverage PHPUnit run reported {failures} failure(s) "
            f"and {errors} error(s) out of {tests} test(s). See the log above."
        )
        return 1
    if not tests:
        print("::error::The coverage PHPUnit run reported no tests at all.")
        return 1
    print(f"The coverage PHPUnit run passed {tests} test(s).")
    return 0


if __name__ == '__main__':
    sys.exit(main())
