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


class PipelineLibraries(BaseGroovyPlugin):
    source_tree_path = 'jenkins.pipeline_libraries'

    def update_dest(self, source, jenkins_url, jenkins_cli_path, **kwargs):
        data = self._tree_read(source, self.source_tree_path)
        for lib in data["libraries"]:
            try:
                subprocess.call(["java",
                                 "-jar", jenkins_cli_path,
                                 "-s", jenkins_url,
                                 "groovy",
                                 self.groovy_path,
                                 "set_global_library",
                                 lib["name"],
                                 lib["git_url"],
                                 lib["git_branch"],
                                 lib["default_version"],
                                 str(lib["load_implicitly"]),
                                 str(lib["allow_version_override"])
                                 ], shell=False)
            except OSError:
                self.logger.exception('Could not find java')
