import pytest


def run_tests_with_coverage():
    """
    Run pytest with coverage and print the report in the terminal.
    """
    # Define coverage options
    pytest_args = [
        '--cov=.',              # Measure coverage for the current directory
        '--cov-report=term',    # Print coverage report to the terminal
    ]

    # Run pytest with the specified arguments
    exit_code = pytest.main(pytest_args)

    # Exit with the pytest exit code
    return exit_code

if __name__ == "__main__":
    exit(run_tests_with_coverage())
