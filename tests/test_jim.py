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

import mockfs
import os
import pytest
import jsonschema
from lib.common import yaml_reader
from tests import base

jimmy_dir = os.path.dirname(os.path.dirname(__file__))
jimmy_schema_path = os.path.join(jimmy_dir, 'lib', 'schema.yaml')
jimmy_yaml_path = os.path.join(jimmy_dir, 'jimmy.yaml')


class TestJimmySchema(base.TestCase):

    def teardown_method(self, method):
        mockfs.restore_builtins()

    def test_valid_repo_data(self):
        self.mfs = mockfs.replace_builtins()
        self.mfs.add_entries({jimmy_schema_path: self.jimmy_schema,
                              jimmy_yaml_path: self.mock_jimmy_yaml})
        schema = yaml_reader.read(jimmy_schema_path)
        repo_data = yaml_reader.read(jimmy_yaml_path)
        jsonschema.validate(repo_data, schema)

    def test_validation_fail_for_envs_required_property(self):
        with open(jimmy_yaml_path, 'r') as f:
            jimmy_yaml = f.read()
            mock_jimmy_yaml = jimmy_yaml.replace("envs:", "")
        self.mfs = mockfs.replace_builtins()
        self.mfs.add_entries({jimmy_yaml_path: mock_jimmy_yaml,
                              jimmy_schema_path: self.jimmy_schema})
        schema = yaml_reader.read(jimmy_schema_path)
        jimmy_yaml_data = yaml_reader.read(jimmy_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(jimmy_yaml_data, schema)
        assert excinfo.value.message == "'envs' is a required property"

    def test_validation_fail_for_pipelines_required_property(self):
        self.mfs = mockfs.replace_builtins()
        self.mfs.add_entries({jimmy_schema_path: self.jimmy_schema,
                              jimmy_yaml_path: '\n'.join(
                                  [
                                      'plugin-directories:',
                                      '  - ./plugins',
                                      'defaults:',
                                      '  inject:',
                                      '    jenkins_cli_path: /var/cache/jenkins/war/WEB-INF/jenkins-cli.jar',
                                      'setup:',
                                      '  - name: setup',
                                      'teardown:',
                                      '  - name: teardown',
                                      'envs:',
                                      '  main:',
                                      '    jenkins_url: http://localhost:8080'
                                  ])
                              })
        schema = yaml_reader.read(jimmy_schema_path)
        jimmy_yaml_data = yaml_reader.read(jimmy_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(jimmy_yaml_data, schema)
        assert excinfo.value.message == "'pipelines' is a required property"

    def test_validation_fail_for_additional_properties(self):
        with open(jimmy_yaml_path, 'r') as f:
            jimmy_yaml = f.read()
            mock_jimmy_yaml = jimmy_yaml.replace("plugin-directories:", "test:")
        self.mfs = mockfs.replace_builtins()
        self.mfs.add_entries({jimmy_yaml_path: mock_jimmy_yaml,
                              jimmy_schema_path: self.jimmy_schema})
        schema = yaml_reader.read(jimmy_schema_path)
        jimmy_yaml_data = yaml_reader.read(jimmy_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(jimmy_yaml_data, schema)
        assert excinfo.value.message == "Additional properties are not allowed ('test' was unexpected)"
