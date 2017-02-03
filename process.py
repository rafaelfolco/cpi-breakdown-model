#  Copyright 2017 IBM corp.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
"""Run a command for a given amount of time"""

import signal
import subprocess
import threading


class Command(threading.Thread):
    def __init__(self, cmd, timeout):
        threading.Thread.__init__(self)
        self.cmd = cmd
        self.start()
        self.join(timeout)

        if self.is_alive():
            self.p.send_signal(signal.SIGINT)
            self.join()

    def run(self):
        self.p = subprocess.Popen(self.cmd, stdout=subprocess.PIPE)
        self.p.wait()
