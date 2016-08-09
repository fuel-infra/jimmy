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


class Security(BaseGroovyPlugin):
    source_tree_path = 'jenkins.security'

    def update_dest(self, source, jenkins_url, jenkins_cli_path, **kwargs):
        data = self._tree_read(source, self.source_tree_path)
        if "ldap" in data:
            # Optional parameters
            user_search_base = data["ldap"]["search"].get("user_base", "")
            group_search_base = data["ldap"]["search"].get("group_base", "")
            try:
                subprocess.call(["java",
                                 "-jar", jenkins_cli_path,
                                 "-s", jenkins_url,
                                 "groovy",
                                 self.groovy_path,
                                 "set_security_ldap",
                                 data["ldap"]["server"],
                                 data["ldap"]["root_bind"]["dn"],
                                 data["ldap"]["search"]["user_filter"],
                                 str(data["ldap"]["root_bind"]["allow_blank"]),
                                 user_search_base,
                                 group_search_base,
                                 data["ldap"]["manager"]["name"],
                                 data["ldap"]["manager"]["password"],
                                 data["cli_user"]["name"],
                                 data["cli_user"]["public_key"]
                                 ], shell=False)
            except OSError:
                self.logger.exception('Could not find java')

        elif "password" in data:
            try:
                subprocess.call(["java",
                                 "-jar", jenkins_cli_path,
                                 "-s", jenkins_url,
                                 "groovy",
                                 self.groovy_path,
                                 "set_security_password",
                                 data["cli_user"]["name"],
                                 data["cli_user"]["public_key"],
                                 data["cli_user"]["password"]
                                 ], shell=False)
            except OSError:
                self.logger.exception('Could not find java')

        elif "unsecured" in data:
            try:
                subprocess.call(["java",
                                 "-jar", jenkins_cli_path,
                                 "-s", jenkins_url,
                                 "groovy",
                                 self.groovy_path,
                                 "set_unsecured"
                                 ], shell=False)
            except OSError:
                self.logger.exception('Could not find java')
        # If ldap realm is set need just to add ldap users/groups in matrix
        # If user/password(Jenkins own db) realm  is set need to
        # create jenkins users and add them to matrix
        if "ldap" in data or "password" in data:
            if "ldap" in data:
                realm = "ldap"
            elif "password" in data:
                realm = "password"
            realm_data = data[realm]
            if "access" in realm_data:
                for p in realm_data["access"]:
                    name = p.get("name", "")
                    permissions = p.get("permissions", "")
                    email = p.get("email", "")
                    password = p.get("password", "")
                    full_name = p.get("full_name", "")
                    ssh_public_key = p.get("ssh_public_key", "")
                    try:
                        subprocess.call(["java",
                                         "-jar", jenkins_cli_path,
                                         "-s", jenkins_url,
                                         "groovy",
                                         self.groovy_path,
                                         "set_permissions_matrix",
                                         name,
                                         ",".join(map(str, permissions)),
                                         email,
                                         password,
                                         full_name,
                                         ssh_public_key,
                                         realm
                                         ], shell=False)
                    except OSError:
                        self.logger.exception('Could not find java')
