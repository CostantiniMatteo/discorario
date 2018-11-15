#!/bin/bash
set -o errexit

# Get project path.
PROJECT_PATH="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Add project modules to PYTHONPATH.
if [ -z   "${PYTHONPATH}" ]; then
   export PYTHONPATH="${PROJECT_PATH}/src/"
elif [[ "${PYTHONPATH}" != *"${PROJECT_PATH}"* ]]; then
   export PYTHONPATH="${PYTHONPATH}:${PROJECT_PATH}/src/"
fi

pushd ${PROJECT_PATH}

# Run tests.
for TEST_FILE in $(find tests -name "*test.py"); do
    echo "Running tests in ${TEST_FILE}"
    python ${TEST_FILE}
done
echo "All tests passed!"

popd
