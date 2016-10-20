# -*- coding: utf-8 -*-

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


class Artifactory(BaseGroovyPlugin):
    source_tree_path = 'jenkins.artifactory'

    def update_dest(self, source, jenkins_url, jenkins_cli_path, **kwargs):
        data = self._tree_read(source, self.source_tree_path)
        if "build_info_proxy" in data:
            try:
                subprocess.call(["java",
                                 "-jar", jenkins_cli_path,
                                 "-s", jenkins_url,
                                 "groovy",
                                 self.groovy_path,
                                 "setGlobalConfig",
                                 str(data["build_info_proxy"]["port"])
                                 ], shell=False)
            except OSError:
                self.logger.exception('Could not find java')
        for server in data["servers"]:
            # Optional params
            resolver_credentials_id = server.get("resolver_credentials_id", "")
            timeout = server.get("timeout", 300)
            bypass_proxy = server.get("bypass_jenkins_proxy", False)
            try:
                subprocess.call(["java",
                                 "-jar", jenkins_cli_path,
                                 "-s", jenkins_url,
                                 "groovy",
                                 self.groovy_path,
                                 "setServerConfig",
                                 server["id"],
                                 server["url"],
                                 server["deployer_credentials_id"],
                                 resolver_credentials_id,
                                 str(timeout),
                                 str(bypass_proxy)
                                 ], shell=False)
            except OSError:
                self.logger.exception('Could not find java')
