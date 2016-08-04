# -*- coding: utf-8 -*-

#    Copyright 2016 Mirantis, Inc.
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License along
#    with this program; if not, write to the Free Software Foundation, Inc.,
#    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import os

jimmy_dir = os.path.dirname(os.path.dirname(__file__))


class TestCase(object):

    """Test case base class for all unit tests."""
    def setup(self):
        with open(os.path.join(jimmy_dir, 'lib', 'schema.yaml'), 'r') as f:
            self.jimmy_schema = f.read()
        with open(os.path.join(jimmy_dir, 'jimmy.yaml'), 'r') as f:
            self.jimmy_yaml = f.read()
            self.mock_jimmy_yaml = self.jimmy_yaml.replace(
                "jenkins_cli_path: /var/cache/jenkins/war/WEB-INF/jenkins-cli.jar",
                "jenkins_cli_path: << path to jenkins-cli.jar >>")
