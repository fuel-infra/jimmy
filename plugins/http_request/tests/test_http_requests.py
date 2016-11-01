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

import mock
import mockfs
import os
import pytest
import sys
import jsonschema
from jimmy import cli
from mock import call
from click.testing import CliRunner
from lib.common import yaml_reader
from tests import base

plugins_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
jimmy_dir = os.path.dirname(plugins_dir)
http_request_schema_path = os.path.join(plugins_dir, 'http_request', 'resources', 'schema.yaml')
jenkins_yaml_path = os.path.join(jimmy_dir, 'sample', 'input', 'jenkins.yaml')


class TestHttpRequestPlugin(base.TestCase):

    def setup_method(self, method):
        self.runner = CliRunner()

    def teardown_method(self, method):
        mockfs.restore_builtins()

    @mock.patch('lib.core.load_py_modules')
    @mock.patch('subprocess.call')
    def test_cli_call(self, mock_subp, mock_modules):
        with open(http_request_schema_path, 'r') as f:
            mock_http_request_schema = f.read()
        self.mfs = mockfs.replace_builtins()
        self.mfs.add_entries({os.path.join(jimmy_dir, 'lib', 'schema.yaml'): self.jimmy_schema,
                              os.path.join(jimmy_dir, 'jimmy.yaml'): self.mock_jimmy_yaml,
                              http_request_schema_path: mock_http_request_schema,
                              jenkins_yaml_path: '\n'.join(
                                  [
                                      'jenkins:',
                                      '  http_request:',
                                      '    basic_auth:',
                                      '    - key_name: testauth',
                                      '      username: user',
                                      '      password: secret',
                                      '    - key_name: testauth2',
                                      '      username: user2',
                                      '      password: secret2'
                                  ])
                              })
        sys.path.insert(0, plugins_dir)
        import http_request
        import read_source
        sys.path.pop(0)
        mock_modules.return_value = [http_request, read_source]
        os.chdir(jimmy_dir)
        self.runner.invoke(cli)
        calls = [call(['java',
                       '-jar', '<< path to jenkins-cli.jar >>',
                       '-s', 'http://localhost:8080', 'groovy',
                       plugins_dir + '/' + 'http_request/resources/jenkins.groovy',
                       'setBasicDigestAuth',
                       'testauth',
                       'user',
                       'secret'],
                      shell=False),
                 call(['java',
                       '-jar', '<< path to jenkins-cli.jar >>',
                       '-s', 'http://localhost:8080', 'groovy',
                       plugins_dir + '/' + 'http_request/resources/jenkins.groovy',
                       'setBasicDigestAuth',
                       'testauth2',
                       'user2',
                       'secret2'],
                      shell=False)]
        mock_subp.assert_has_calls(calls, any_order=True)
        assert 2 == mock_subp.call_count, "subprocess call should be equal to 2"


class TestHttpRequestSchema(object):

    def setup_method(self, method):
        with open(http_request_schema_path, 'r') as f:
            mock_http_request_schema = f.read()
        self.mfs = mockfs.replace_builtins()
        self.mfs.add_entries({http_request_schema_path: mock_http_request_schema})
        self.schema = yaml_reader.read(http_request_schema_path)

    def teardown_method(self, method):
        mockfs.restore_builtins()

    def test_valid_repo_data(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              '    basic_auth:',
              '    - key_name: testauth',
              '      username: user',
              '      password: secret',
              '    - key_name: testauth2',
              '      username: user2',
              '      password: secret2'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        jsonschema.validate(repo_data, self.schema)

    def test_validation_fail_if_key_name_is_not_string(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              '    basic_auth:',
              '    - key_name: 123',
              '      username: user',
              '      password: secret'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "123 is not of type 'string'"

    def test_validation_fail_if_username_is_not_string(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              '    basic_auth:',
              '    - key_name: testauth',
              '      username: 123',
              '      password: secret'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "123 is not of type 'string'"

    def test_validation_fail_if_password_is_not_string(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              '    basic_auth:',
              '    - key_name: testauth',
              '      username: user',
              '      password: 123'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "123 is not of type 'string'"

    def test_validation_fail_for_key_name_required_property(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              '    basic_auth:',
              '    - username: user',
              '      password: secret'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "'key_name' is a required property"

    def test_validation_fail_for_username_required_property(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              '    basic_auth:',
              '    - key_name: testauth',
              '      password: secret'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "'username' is a required property"

    def test_validation_fail_for_password_required_property(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              '    basic_auth:',
              '    - key_name: testauth',
              '      username: user'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "'password' is a required property"

    def test_validation_fail_if_libraries_is_not_array(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              '    basic_auth:',
              '      key_name: testauth',
              '      username: user',
              '      password: secret'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "{'username': 'user', 'key_name': 'testauth', 'password': 'secret'} " \
            "is not of type 'array'"

    def test_validation_fail_for_additional_properties(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              '    basic_auth:',
              '    - key_name: testauth',
              '      username: user',
              '      password: secret',
              '      test: test'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "Additional properties are not allowed ('test' was unexpected)"
