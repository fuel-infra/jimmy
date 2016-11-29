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


class JenkinsConfiguration(BaseGroovyPlugin):
    source_tree_path = 'jenkins.configuration'

    def update_dest(self, source, jenkins_url, jenkins_cli_path, **kwargs):
        data = self._tree_read(source, self.source_tree_path)
        if "admin_email" in data:
            try:
                subprocess.call(["java",
                                 "-jar", jenkins_cli_path,
                                 "-s", jenkins_url,
                                 "groovy",
                                 self.groovy_path,
                                 "setAdminEmail",
                                 "'{0}'".format(data["admin_email"])  # jenkins-cli bug workaround
                                 ], shell=False)
            except OSError:
                self.logger.exception('Could not find java')

        if "agent_tcp_port" in data:
            try:
                subprocess.call(["java",
                                 "-jar", jenkins_cli_path,
                                 "-s", jenkins_url,
                                 "groovy",
                                 self.groovy_path,
                                 "setAgentTcpPort",
                                 str(data["agent_tcp_port"])
                                 ], shell=False)
            except OSError:
                self.logger.exception('Could not find java')

        if "location_url" in data:
            try:
                subprocess.call(["java",
                                 "-jar", jenkins_cli_path,
                                 "-s", jenkins_url,
                                 "groovy",
                                 self.groovy_path,
                                 "setLocationUrl",
                                 "'{0}'".format(data["location_url"])  # jenkins-cli bug workaround
                                 ], shell=False)
            except OSError:
                self.logger.exception('Could not find java')

        if "markup_format" in data:
            try:
                subprocess.call(["java",
                                 "-jar", jenkins_cli_path,
                                 "-s", jenkins_url,
                                 "groovy",
                                 self.groovy_path,
                                 "setMarkupFormatter",
                                 data["markup_format"]
                                 ], shell=False)
            except OSError:
                self.logger.exception('Could not find java')

        if "num_of_executors" in data:
            try:
                subprocess.call(["java",
                                 "-jar", jenkins_cli_path,
                                 "-s", jenkins_url,
                                 "groovy",
                                 self.groovy_path,
                                 "setNumExecutors",
                                 str(data["num_of_executors"])
                                 ], shell=False)
            except OSError:
                self.logger.exception('Could not find java')

        if "scm_checkout_retry_count" in data:
            try:
                subprocess.call(["java",
                                 "-jar", jenkins_cli_path,
                                 "-s", jenkins_url,
                                 "groovy",
                                 self.groovy_path,
                                 "setScmCheckoutRetryCount",
                                 str(data["scm_checkout_retry_count"])
                                 ], shell=False)
            except OSError:
                self.logger.exception('Could not find java')
