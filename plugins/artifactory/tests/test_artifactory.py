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
artifactory_schema_path = os.path.join(plugins_dir, 'artifactory', 'resources', 'schema.yaml')
jenkins_yaml_path = os.path.join(jimmy_dir, 'sample', 'input', 'jenkins.yaml')


class TestArtifactoryPlugin(base.TestCase):

    def setup_method(self, method):
        self.runner = CliRunner()

    def teardown_method(self, method):
        mockfs.restore_builtins()

    @mock.patch('lib.core.load_py_modules')
    @mock.patch('subprocess.call')
    def test_cli_call(self, mock_subp, mock_modules):
        with open(artifactory_schema_path, 'r') as f:
            mock_artifactory_schema = f.read()
        self.mfs = mockfs.replace_builtins()
        self.mfs.add_entries({os.path.join(jimmy_dir, 'lib', 'schema.yaml'): self.jimmy_schema,
                              os.path.join(jimmy_dir, 'jimmy.yaml'): self.mock_jimmy_yaml,
                              artifactory_schema_path: mock_artifactory_schema,
                              jenkins_yaml_path: '\n'.join(
                                  [
                                      'jenkins:',
                                      '  artifactory:',
                                      '    build_info_proxy:',
                                      '      port: 9876',
                                      '    servers:',
                                      '    - id: artifactory-server',
                                      '      url: artifactory.example.com',
                                      '      deployer_credentials_id: artifactory-credentials',
                                      '      resolver_credentials_id: resolver-credentials',
                                      '      timeout: 600',
                                      '      bypass_jenkins_proxy: false',
                                      '    - id: artifactory-server-dev',
                                      '      url: artifactory-dev.example.com',
                                      '      deployer_credentials_id: artifactory-dev-credentials',
                                      '      resolver_credentials_id: resolver-dev-credentials',
                                      '      timeout: 600',
                                      '      bypass_jenkins_proxy: false'
                                  ])
                              })
        sys.path.insert(0, plugins_dir)
        import artifactory
        import read_source
        sys.path.pop(0)
        mock_modules.return_value = [artifactory, read_source]
        os.chdir(jimmy_dir)
        self.runner.invoke(cli)
        calls = [call(['java',
                       '-jar', '<< path to jenkins-cli.jar >>',
                       '-s', 'http://localhost:8080', 'groovy',
                       plugins_dir + '/' + 'artifactory/resources/jenkins.groovy',
                       'setGlobalConfig',
                       '9876'
                       ], shell=False),
                 call(['java',
                       '-jar', '<< path to jenkins-cli.jar >>',
                       '-s', 'http://localhost:8080', 'groovy',
                       plugins_dir + '/' + 'artifactory/resources/jenkins.groovy',
                       'setServerConfig',
                       'artifactory-server',
                       'artifactory.example.com',
                       'artifactory-credentials',
                       'resolver-credentials',
                       '600',
                       'False'
                       ], shell=False),
                 call(['java',
                       '-jar', '<< path to jenkins-cli.jar >>',
                       '-s', 'http://localhost:8080', 'groovy',
                       plugins_dir + '/' + 'artifactory/resources/jenkins.groovy',
                       'setServerConfig',
                       'artifactory-server-dev',
                       'artifactory-dev.example.com',
                       'artifactory-dev-credentials',
                       'resolver-dev-credentials',
                       '600',
                       'False'
                       ], shell=False)]
        mock_subp.assert_has_calls(calls, any_order=True)
        assert 3 == mock_subp.call_count, "subprocess call should be equal to 3"


class TestArtifactorySchema(object):

    def setup_method(self, method):
        with open(artifactory_schema_path, 'r') as f:
            mock_artifactory_schema = f.read()
        self.mfs = mockfs.replace_builtins()
        self.mfs.add_entries({artifactory_schema_path: mock_artifactory_schema})
        self.schema = yaml_reader.read(artifactory_schema_path)

    def teardown_method(self, method):
        mockfs.restore_builtins()

    def test_valid_repo_data(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              'build_info_proxy:',
              '  port: 9876',
              'servers:',
              '- id: artifactory-server',
              '  url: artifactory.example.com',
              '  deployer_credentials_id: artifactory-credentials',
              '  resolver_credentials_id: resolver-credentials',
              '  timeout: 600',
              '  bypass_jenkins_proxy: False'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        jsonschema.validate(repo_data, self.schema)

    def test_validation_fail_if_port_is_not_integer(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              'build_info_proxy:',
              '  port: test',
              'servers:',
              '  url: artifactory.example.com',
              '  deployer_credentials_id: artifactory-credentials'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "'test' is not of type 'integer'"

    def test_validation_fail_for_servers_not_array(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              'servers:',
              '  url: artifactory.example.com',
              '  deployer_credentials_id: artifactory-credentials'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "{'url': 'artifactory.example.com'," \
            " 'deployer_credentials_id': 'artifactory-credentials'} is not of type 'array'"

    def test_validation_fail_for_id_required_property(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              'servers:',
              '- url: artifactory.example.com',
              '  deployer_credentials_id: artifactory-credentials',
              '  resolver_credentials_id: resolver-credentials',
              '  timeout: 600',
              '  bypass_jenkins_proxy: False'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "'id' is a required property"

    def test_validation_fail_for_url_required_property(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              'servers:',
              '- id: artifactory-server',
              '  deployer_credentials_id: artifactory-credentials',
              '  resolver_credentials_id: resolver-credentials',
              '  timeout: 600',
              '  bypass_jenkins_proxy: False'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "'url' is a required property"

    def test_validation_fail_for_deployer_credentials_required_property(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              'servers:',
              '- id: artifactory-server',
              '  url: artifactory.example.com',
              '  resolver_credentials_id: resolver-credentials',
              '  timeout: 600',
              '  bypass_jenkins_proxy: False'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "'deployer_credentials_id' is a required property"

    def test_validation_fail_if_id_is_not_string(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              'servers:',
              '- id: 123',
              '  url: artifactory.example.com',
              '  deployer_credentials_id: artifactory-credentials',
              '  resolver_credentials_id: resolver-credentials',
              '  timeout: 600',
              '  bypass_jenkins_proxy: False'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "123 is not of type 'string'"

    def test_validation_fail_if_url_is_not_string(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              'servers:',
              '- id: artifactory-server',
              '  url: 123',
              '  deployer_credentials_id: artifactory-credentials',
              '  resolver_credentials_id: resolver-credentials',
              '  timeout: 600',
              '  bypass_jenkins_proxy: False'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "123 is not of type 'string'"

    def test_validation_fail_if_deployer_credentials_is_not_string(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              'servers:',
              '- id: artifactory-server',
              '  url: artifactory.example.com',
              '  deployer_credentials_id: 123',
              '  resolver_credentials_id: resolver-credentials',
              '  timeout: 600',
              '  bypass_jenkins_proxy: False'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "123 is not of type 'string'"

    def test_validation_fail_if_resolver_credentials_is_not_string(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              'servers:',
              '- id: artifactory-server',
              '  url: artifactory.example.com',
              '  deployer_credentials_id: artifactory-credentials',
              '  resolver_credentials_id: 123',
              '  timeout: 600',
              '  bypass_jenkins_proxy: False'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "123 is not of type 'string'"

    def test_validation_fail_if_timeout_is_not_integer(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              'servers:',
              '- id: artifactory-server',
              '  url: artifactory.example.com',
              '  deployer_credentials_id: artifactory-credentials',
              '  resolver_credentials_id: resolver-credentials',
              '  timeout: test',
              '  bypass_jenkins_proxy: False'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "'test' is not of type 'integer'"

    def test_validation_fail_if_bypass_proxy_is_not_boolean(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              'servers:',
              '- id: artifactory-server',
              '  url: artifactory.example.com',
              '  deployer_credentials_id: artifactory-credentials',
              '  resolver_credentials_id: resolver-credentials',
              '  timeout: 600',
              '  bypass_jenkins_proxy: test'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "'test' is not of type 'boolean'"

    def test_validation_fail_for_additional_properties(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              'servers:',
              '- id: artifactory-server',
              '  url: artifactory.example.com',
              '  deployer_credentials_id: artifactory-credentials',
              '  resolver_credentials_id: resolver-credentials',
              '  timeout: 600',
              '  bypass_jenkins_proxy: False',
              '  test: test'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "Additional properties are not allowed ('test' was unexpected)"
