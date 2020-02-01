# Copyright 2020 Open Source Robotics Foundation, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import time

from pulpcore.client import pulpcore


class PulpTaskPoller:

    def __init__(self, pulp_configuration, timeout, interval=0.5):
        client = pulpcore.ApiClient(pulp_configuration)
        self._tasks_api = pulpcore.TasksApi(client)
        self._timeout = timeout
        self._interval = interval

    def wait_for_task(self, task_href):
        task = self._tasks_api.read(task_href)

        print("Waiting for task '%s'..." %
              (self._tasks_api.api_client.configuration.host + task.pulp_href))

        timeout = self._timeout
        while task.state != 'completed':
            if task.state in ['failed', 'canceled']:
                raise RuntimeError(
                    "Pulp task '%s' did not complete (%s)" % (task.pulp_href, task.state))
            time.sleep(self._interval)
            timeout -= self._interval
            if timeout <= 0:
                raise RuntimeError(
                    "Pulp task '%s' did not complete (timed out)" % task.pulp_href)

            task = self._tasks_api.read(task.pulp_href)

        print('...done.')
        return task
