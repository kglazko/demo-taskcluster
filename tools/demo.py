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
GITHUB_REPO = 'demo-taskcluster'
GITHUB_OWNER = 'kglazko'
GITHUB_OWNER_EMAIL = "katglazko@gmail.com"
SOURCE = "https://github.com/kglazko/demo-taskcluster/tree/master/tools"
payload_source = {
  "title": "Create Comment Request",
  "description": "Write a new comment on a GitHub Issue or Pull Request.\nFull specification on [GitHub docs](https://developer.github.com/v3/issues/comments/#create-a-comment)\n",
  "type": "object",
  "properties": {
    "body": {
      "type": "string",
      "description": "The contents of the comment that were posted from TaskCluster."
    }
  },
  "additionalProperties": False,
  "required": [
    "body"
  ],
}
payload = json.dumps(payload_source)



def post_github_comment(issue_number, payload):
    print('posting comment....')
    taskcluster.Github().createComment(payload, owner=GITHUB_OWNER, repo=GITHUB_REPO, number=issue_number)

def generate_demo_test_task():
    slug_id = taskcluster.slugId()
    task_json = generate_task(
		name = "(Demo Taskcluster) Dummy tests",
		description = "Run a demo for the heck of it.",
		command = ('./tools/demo.sh'),
                routes=['notify.irc-channel.#demo-ci.on-any',
                        '/repository/rpappalax/demo-taskcluster/issues/1/comments'],
		#dependencies = dependencies,
                scopes = ['github:create-comment:rpappalax/demo-taskcluster'],
		artifacts = {
			"public": {
				"type": "directory",
				"path": "/opt/demo-taskcluster/test_artifacts",
				"expires": taskcluster.stringDate(taskcluster.fromNow('1 week'))
			}
		})
    print(task_json)
    post_github_comment('1', payload)
    return slug_id, task_json


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
			"owner": GITHUB_OWNER_EMAIL,
			"source": SOURCE
		}
	}


if __name__ == "__main__":
	queue = taskcluster.Queue({ 'baseUrl': 'http://taskcluster/queue/v1' })
	demoTestTaskId, demoTestTask = generate_demo_test_task()
	schedule_task(queue, demoTestTaskId, demoTestTask)
