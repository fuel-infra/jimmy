#  Copyright 2016 Mirantis, Inc.
#
#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.

import subprocess
from lib.api import BaseGroovyPlugin


class Credentials(BaseGroovyPlugin):
    source_tree_path = 'jenkins.credentials'

    def update_dest(self, source, jenkins_url, jenkins_cli_path, **kwargs):
        data = self._tree_read(source, self.source_tree_path)
        if "password" in data:
            for p in data["password"]:
                cred_id = p.get("id", "")
                description = p.get("description", "")
                try:
                    subprocess.call(["java",
                                     "-jar", jenkins_cli_path,
                                     "-s", jenkins_url,
                                     "groovy",
                                     self.groovy_path,
                                     "update_credentials",
                                     "'{0}'".format(p["scope"]),  # jenkins-cli bug workaround
                                     "'{0}'".format(p["username"]),
                                     "'{0}'".format(p["password"]),
                                     "'{0}'".format(description),
                                     "''",  # place for a private_key
                                     "'{0}'".format(cred_id)
                                     ], shell=False)
                except OSError:
                    self.logger.exception('Could not find java')

        if "ssh" in data:
            for s in data["ssh"]:
                cred_id = s.get("id", "")
                passphrase = s.get("passphrase", "")
                description = s.get("description", "")
                try:
                    subprocess.call(["java",
                                     "-jar", jenkins_cli_path,
                                     "-s", jenkins_url,
                                     "groovy",
                                     self.groovy_path,
                                     "update_credentials",
                                     "'{0}'".format(s["scope"]),  # jenkins-cli bug workaround
                                     "'{0}'".format(s["username"]),
                                     "'{0}'".format(passphrase),
                                     "'{0}'".format(description),
                                     "'{0}'".format(s["private_key"]),
                                     "'{0}'".format(cred_id)
                                     ], shell=False)
                except OSError:
                    self.logger.exception('Could not find java')
