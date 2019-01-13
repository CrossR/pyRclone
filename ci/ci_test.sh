#!/bin/bash

# Setup some global variables
SUCCESS=0
FAIL=1

RED='\033[0;31m'
GREEN='\033[1;32m'

LogMessage() {
    echo -e "${GREEN}$(date +'%d/%m/%Y %X')" : "$*"
}

LogError() {
    echo -e "${RED}$(date +'%d/%m/%Y %X')" : "$*"
}

LogMessage "Starting testing script..."

# Printing relevant versions of libraries
poetry run python --version

if [ "${LINT_CODE:-0}" -eq 1 ]; then

    poetry run pylint --version
    poetry run black --version

    LogMessage "Running full lint of code..."
    poetry run pylint pyRclone
    LogMessage "Finished running full lint of code..."

    LogMessage "Linting code ignoring TODO warnings..."
    poetry run pylint pyRclone -d W0511
    RETURN_CODE=$?
    LogMessage "Finished running second lint of code..."

    LogMessage "Pylint returned ${RETURN_CODE}..."

    if [ $RETURN_CODE -ne 0 ]; then
        LogError "pylint failed check..."
        exit ${FAIL}
    fi

    LogMessage "Running black on main source..."
    poetry run black pyRclone --check
    RETURN_CODE=$?
    LogMessage "Finished running black on main source..."

    LogMessage "black returned ${RETURN_CODE}..."

    if [ $RETURN_CODE -ne 0 ]; then
        LogError "Main code failed black check..."
        exit ${FAIL}
    fi
fi

if [ "${UNIT_TESTS-0}" -eq 1 ]; then

    poetry run pytest --version

    LogMessage "Running unit tests..."
    poetry run pytest --cov=./
    RETURN_CODE=$?

    LogMessage "Uploading results..."
    poetry run codecov
    LogMessage "Done uploading!"

    LogMessage "Finished running unit tests..."

    LogMessage "pytest returned ${RETURN_CODE}..."

    if [ $RETURN_CODE -ne 0 ]; then
        LogError "Unit tests failed..."
        exit ${FAIL}
    else
        LogMessage "Unit tests passed!"
    fi
fi

if [ "${FULL_TYPING:-0}" -eq 1 ]; then

    poetry run mypy --version

    LogMessage "Running full mypy on code base..."
    poetry run mypy pyRclone --strict
    RETURN_CODE=$?
    LogMessage "Finished running full mypy on code base..."

    LogMessage "mypy returned ${RETURN_CODE}..."

    if [ $RETURN_CODE -ne 0 ]; then
        LogError "Full typing check failed..."
        exit ${FAIL}
    else
        LogMessage "Full typing check passed!"
    fi
fi

if [ "${BASIC_TYPING-0}" -eq 1 ]; then

    poetry run mypy --version

    LogMessage "Running basic mypy on code base..."
    poetry run mypy --config-file mypy.ini pyRclone
    RETURN_CODE=$?
    LogMessage "Finished running basic mypy on code base..."

    LogMessage "mypy returned ${RETURN_CODE}..."

    if [ $RETURN_CODE -ne 0 ]; then
        LogError "Basic typing check failed..."
        exit ${FAIL}
    else
        LogMessage "Basic typing check passed!"
    fi
fi

LogMessage "Script finished!"
exit ${SUCCESS}
