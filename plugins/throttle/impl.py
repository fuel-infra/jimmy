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


class ThrottleConcurrentPlugin(BaseGroovyPlugin):
    source_tree_path = 'jenkins.throttle'

    def update_dest(self, source, jenkins_url, jenkins_cli_path, **kwargs):
        data = self._tree_read(source, self.source_tree_path)
        try:
            subprocess.call(["java",
                             "-jar", jenkins_cli_path,
                             "-s", jenkins_url,
                             "groovy",
                             self.groovy_path,
                             "clear_categories",
                             ], shell=False)
        except OSError:
            self.logger.exception('Could not find java')

        for p in data["categories"]:
            # Check for existing 'max_per_labeled_node' in dict
            # If exists collect values to list
            if "max_per_labeled_node" in p:
                throttled_node_label_list = [
                    node_label["throttled_node_label"]
                    for node_label in p["max_per_labeled_node"]]
                max_conc_per_labeled_list = [
                    conc_per_label["max_concurrent_per_labeled"]
                    for conc_per_label in p["max_per_labeled_node"]]
            else:
                throttled_node_label_list = ''
                max_conc_per_labeled_list = ''

            try:
                subprocess.call(["java",
                                 "-jar", jenkins_cli_path,
                                 "-s", jenkins_url,
                                 "groovy",
                                 self.groovy_path,
                                 "create_throttle_category",
                                 p["category_name"],
                                 str(p["max_total_concurrent_builds"]),
                                 str(p["max_concurrent_bulds_per_node"]),
                                 ",".join(throttled_node_label_list),
                                 ",".join(map(str, max_conc_per_labeled_list))
                                 ], shell=False)
            except OSError:
                self.logger.exception('Could not find java')
