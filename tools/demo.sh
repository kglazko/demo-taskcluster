#!/usr/bin/env bash
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# This script uses the flank tool (https://github.com/TestArmada/flank)
# to shard UI test execution on Google Firebase so tests can run in parallel.  
#
# NOTE: 
#   Google Firebase does not currently allow renaming nor grouping of test
#   jobs.  recommendation: look at test failure summary in taskcluster
#   (not on Firebase dashboard)


# If a command fails then do not proceed and fail this script too.
set -e

PATH_TEST="."



# create TEST_TARGETS 
# (aka: get list of all tests in androidTest)
file_list=$(ls $PATH_TEST | xargs -n 1 basename)
array=( $file_list )
echo $array
echo "Hello from  Taskcluster"
exitcode=$?

# Now exit the script with the exit code from the test run. (Only 0 if all test executions passed)
exit $exitcode
