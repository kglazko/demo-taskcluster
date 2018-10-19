# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
This script will be executed whenever a change is pushed to the
master branch. It will schedule multiple child tasks that build
the app, run tests and execute code quality tools:
"""

import datetime
import json
import taskcluster
import os

from lib.tasks import schedule_task


TASK_ID = os.environ.get('TASK_ID')
REPO_URL = os.environ.get('MOBILE_HEAD_REPOSITORY')
BRANCH = os.environ.get('MOBILE_HEAD_BRANCH')
COMMIT = os.environ.get('MOBILE_HEAD_REV')
OWNER = "skaspari@mozilla.com"
SOURCE = "https://github.com/mozilla-mobile/focus-android/tree/master/tools/taskcluster"

def generate_build_task():
	return taskcluster.slugId(), generate_task(
		name = "(Focus for Android) Build",
		description = "Build Focus/Klar for Android from source code.",
		command = ('echo "--" > .adjust_token'
				   ' && python tools/l10n/check_translations.py'
				   ' && ./gradlew --no-daemon clean assemble'))


def generate_unit_test_task(buildTaskId):
	return taskcluster.slugId(), generate_task(
		name = "(Focus for Android) Unit tests",
		description = "Run unit tests for Focus/Klar for Android.",
		command = 'echo "--" > .adjust_token && ./gradlew --no-daemon clean test',
		dependencies = [ buildTaskId ])



def generate_gecko_ARM_ui_test_task(dependencies):
	return taskcluster.slugId(), generate_task(
		name = "(Focus for Android) UI tests - Gecko ARM",
		description = "Run UI tests for Klar Gecko ARM build for Android.",
		command = ('echo "--" > .adjust_token'
			' && ./gradlew --no-daemon clean assembleKlarArmDebug assembleKlarArmDebugAndroidTest'
			' && ./tools/taskcluster/google-firebase-testlab-login.sh'
                        ' && tools/taskcluster/execute-firebase-tests.sh arm geckoview'),
		dependencies = dependencies,
		scopes = [ 'secrets:get:project/focus/firebase' ],
		artifacts = {
			"public": {
				"type": "directory",
				"path": "/opt/focus-android/test_artifacts",
				"expires": taskcluster.stringDate(taskcluster.fromNow('1 week'))
			}
		})



def generate_task(name, description, command, dependencies = [], artifacts = {}, scopes = [], routes = []):
	created = datetime.datetime.now()
	expires = taskcluster.fromNow('1 month')
	deadline = taskcluster.fromNow('1 day')

	return {
	    "workerType": "github-worker",
	    "taskGroupId": TASK_ID,
	    "expires": taskcluster.stringDate(expires),
	    "retries": 5,
	    "created": taskcluster.stringDate(created),
	    "tags": {},
	    "priority": "lowest",
	    "schedulerId": "taskcluster-github",
	    "deadline": taskcluster.stringDate(deadline),
	    "dependencies": [ TASK_ID ] + dependencies,
	    "routes": routes,
	    "scopes": scopes,
	    "requires": "all-completed",
	    "payload": {
	        "features": {
	            "taskclusterProxy": True
	        },
	        "maxRunTime": 7200,
	        "image": "mozillamobile/focus-android:1.2",
	        "command": [
	            "/bin/bash",
	            "--login",
	            "-c",
				"git fetch %s %s && git config advice.detachedHead false && git checkout %s && %s" % (REPO_URL, BRANCH, COMMIT, command)
	        ],
	        "artifacts": artifacts,
	        "deadline": taskcluster.stringDate(deadline)
	    },
		"provisionerId": "aws-provisioner-v1",
		"metadata": {
			"name": name,
			"description": description,
			"owner": OWNER,
			"source": SOURCE
		}
	}


if __name__ == "__main__":
	queue = taskcluster.Queue({ 'baseUrl': 'http://taskcluster/queue/v1' })

	buildTaskId, buildTask = generate_build_task()
	schedule_task(queue, buildTaskId, buildTask)

