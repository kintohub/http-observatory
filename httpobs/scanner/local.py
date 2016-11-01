import httpobs.conf

from httpobs.scanner.analyzer import NUM_TESTS, tests
from httpobs.scanner.grader import get_grade_and_likelihood_for_score
from httpobs.scanner.retriever import retrieve_all


def scan(hostname, **kwargs):
    # Always allow localhost scans when run in this way
    """Performs an Observatory scan, but doesn't require any database/redis
    backing. Given the lowered security concerns due to not being a public
    API, you can use this to scan arbitrary ports and paths.

    Args:
        hostname (str): domain name for host to be scanned

    Kwargs:
        http_port (int): port to scan for HTTP, instead of 80
        https_port (int): port to be scanned for HTTPS, instead of 443
        path (str): path to scan, instead of "/"

        cookies (dict): Cookies sent to the system being scanned. Matches the
            requests cookie dict.
        headers (dict): HTTP headers sent to the system being scanned. Format
            matches the requests headers dict.

    Returns:
        A dict representing the analyze (scan) and getScanResults (test) API call.  Example:

        {
            'scan': {
                'grade': 'A'
                ...
            },
            'test': {
                'content-security-policy': {
                    'pass': True
                    ...
                }
            }
        }
    """
    httpobs.conf.SCANNER_ALLOW_LOCALHOST = True

    # Attempt to retrieve all the resources, not capturing exceptions
    reqs = retrieve_all(hostname, **kwargs)

    # If we can't connect at all, let's abort the test
    if reqs['responses']['auto'] is None:
        return {'error': 'site down'}

    # Get all the results
    results = [test(reqs) for test in tests]

    # Get the score, grade, etc.
    grades = get_grade_and_likelihood_for_score(100 + sum([result.get('score_modifier', 0) for result in results]))
    tests_passed = sum([1 if result.get('pass') else 0 for result in results])

    # Return the results
    return({
        'scan': {
            'grade': grades[1],
            'likelihood_indicator': grades[2],
            'response_headers': reqs['responses']['auto'].headers,
            'score': grades[0],
            'tests_failed': NUM_TESTS - tests_passed,
            'tests_passed': tests_passed,
            'tests_quantity': NUM_TESTS,
        },
        'tests': {result.pop('name'): result for result in results}
    })
