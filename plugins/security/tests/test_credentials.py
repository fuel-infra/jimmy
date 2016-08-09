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
security_schema_path = os.path.join(plugins_dir, 'security', 'resources', 'schema.yaml')
jenkins_yaml_path = os.path.join(jimmy_dir, 'sample', 'input', 'jenkins.yaml')


class TestSecurityPlugin(base.TestCase):

    def setup_method(self, method):
        self.runner = CliRunner()

    def teardown_method(self, method):
        mockfs.restore_builtins()

    @mock.patch('lib.core.load_py_modules')
    @mock.patch('subprocess.call')
    def test_cli_call_for_ldap_conf(self, mock_subp, mock_modules):
        with open(security_schema_path, 'r') as f:
            mock_security_schema = f.read()
        self.mfs = mockfs.replace_builtins()
        self.mfs.add_entries({os.path.join(jimmy_dir, 'lib', 'schema.yaml'): self.jimmy_schema,
                              os.path.join(jimmy_dir, 'jimmy.yaml'): self.mock_jimmy_yaml,
                              security_schema_path: mock_security_schema,
                              jenkins_yaml_path: '\n'.join(
                                  [
                                    'jenkins:',
                                    '  security:',
                                    '    ldap:',
                                    '      server: ldap://mirantis.com:3268',
                                    '      root_bind:',
                                    '        dn: dc=mirantis,dc=com',
                                    '        allow_blank: false',
                                    '      search:',
                                    '        user_filter: userPrincipalName={0}',
                                    '      manager:',
                                    '        name: mngr@mirantis.com',
                                    '        password: passwd',
                                    '      access:',
                                    '      - name: amihura',
                                    '        permissions:',
                                    '        - overall',
                                    '        - credentials',
                                    '        - gerrit',
                                    '    cli_user:',
                                    '      name: jenkins-manager',
                                    '      public_key: sssh-rsa AAAAB3NzaC'
                                  ])
                              })
        sys.path.insert(0, plugins_dir)
        import security
        import read_source
        sys.path.pop(0)
        mock_modules.return_value = [security, read_source]
        os.chdir(jimmy_dir)
        result = self.runner.invoke(cli)
        print result.output
        calls = [call(['java',
                       '-jar', '<< path to jenkins-cli.jar >>',
                       '-s', 'http://localhost:8080', 'groovy',
                       plugins_dir + '/' + 'security/resources/jenkins.groovy',
                       'set_security_ldap',
                       'ldap://mirantis.com:3268',
                       'dc=mirantis,dc=com',
                       'userPrincipalName={0}',
                       'False',
                       '',
                       '',
                       'mngr@mirantis.com',
                       'passwd',
                       'jenkins-manager',
                       'sssh-rsa AAAAB3NzaC'],
                      shell=False),
                 call(['java',
                       '-jar', '<< path to jenkins-cli.jar >>',
                       '-s', 'http://localhost:8080', 'groovy',
                       plugins_dir + '/' + 'security/resources/jenkins.groovy',
                       'set_permissions_matrix',
                       'amihura',
                       'overall,credentials,gerrit',
                       '',
                       '',
                       '',
                       '',
                       'ldap'],
                      shell=False)]
        mock_subp.assert_has_calls(calls, any_order=True)
        assert 2 == mock_subp.call_count, "subprocess call should be equal to 2"

    @mock.patch('lib.core.load_py_modules')
    @mock.patch('subprocess.call')
    def test_cli_call_for_password_conf(self, mock_subp, mock_modules):
        with open(security_schema_path, 'r') as f:
            mock_security_schema = f.read()
        self.mfs = mockfs.replace_builtins()
        self.mfs.add_entries({os.path.join(jimmy_dir, 'lib', 'schema.yaml'): self.jimmy_schema,
                              os.path.join(jimmy_dir, 'jimmy.yaml'): self.mock_jimmy_yaml,
                              security_schema_path: mock_security_schema,
                              jenkins_yaml_path: '\n'.join(
                                  [
                                    'jenkins:',
                                    '  security:',
                                    '    password:',
                                    '      access:',
                                    '      - name: amihura',
                                    '        email: amihura@example.com',
                                    '        password: passwd',
                                    '        permissions:',
                                    '        - overall',
                                    '        - credentials',
                                    '        - gerrit',
                                    '    cli_user:',
                                    '      name: jenkins-manager',
                                    '      public_key: sssh-rsa AAAAB3NzaC',
                                    '      password: password'
                                  ])
                              })
        sys.path.insert(0, plugins_dir)
        import security
        import read_source
        sys.path.pop(0)
        mock_modules.return_value = [security, read_source]
        os.chdir(jimmy_dir)
        self.runner.invoke(cli)
        calls = [call(['java',
                       '-jar', '<< path to jenkins-cli.jar >>',
                       '-s', 'http://localhost:8080', 'groovy',
                       plugins_dir + '/' + 'security/resources/jenkins.groovy',
                       'set_security_password',
                       'jenkins-manager',
                       'sssh-rsa AAAAB3NzaC',
                       'password'],
                      shell=False),
                 call(['java',
                       '-jar', '<< path to jenkins-cli.jar >>',
                       '-s', 'http://localhost:8080', 'groovy',
                       plugins_dir + '/' + 'security/resources/jenkins.groovy',
                       'set_permissions_matrix',
                       'amihura',
                       'overall,credentials,gerrit',
                       'amihura@example.com',
                       'passwd',
                       '',
                       '',
                       'password'],
                      shell=False)]
        mock_subp.assert_has_calls(calls, any_order=True)
        assert 2 == mock_subp.call_count, "subprocess call should be equal to 2"

    @mock.patch('lib.core.load_py_modules')
    @mock.patch('subprocess.call')
    def test_cli_call_for_unsecured_conf(self, mock_subp, mock_modules):
        with open(security_schema_path, 'r') as f:
            mock_security_schema = f.read()
        self.mfs = mockfs.replace_builtins()
        self.mfs.add_entries({os.path.join(jimmy_dir, 'lib', 'schema.yaml'): self.jimmy_schema,
                              os.path.join(jimmy_dir, 'jimmy.yaml'): self.mock_jimmy_yaml,
                              security_schema_path: mock_security_schema,
                              jenkins_yaml_path: '\n'.join(
                                  [
                                    'jenkins:',
                                    '  security:',
                                    '    unsecured: true'
                                  ])
                              })
        sys.path.insert(0, plugins_dir)
        import security
        import read_source
        sys.path.pop(0)
        mock_modules.return_value = [security, read_source]
        os.chdir(jimmy_dir)
        self.runner.invoke(cli)
        calls = [call(['java',
                       '-jar', '<< path to jenkins-cli.jar >>',
                       '-s', 'http://localhost:8080', 'groovy',
                       plugins_dir + '/' + 'security/resources/jenkins.groovy',
                       'set_unsecured'],
                      shell=False)]
        mock_subp.assert_has_calls(calls, any_order=True)
        assert 1 == mock_subp.call_count, "subprocess call should be equal to 1"


class TestSecuritySchema(object):

    def setup_method(self, method):
        with open(security_schema_path, 'r') as f:
            mock_security_schema = f.read()
        self.mfs = mockfs.replace_builtins()
        self.mfs.add_entries({security_schema_path: mock_security_schema})
        self.schema = yaml_reader.read(security_schema_path)

    def teardown_method(self, method):
        mockfs.restore_builtins()

    def test_valid_oneof_ldap_data(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              'ldap:',
              '  server: ldap://mirantis.com:3268',
              '  root_bind:',
              '    dn: dc=mirantis,dc=com',
              '    allow_blank: false',
              '  search:',
              '    user_filter: userPrincipalName={0}',
              '  manager:',
              '    name: mngr@mirantis.com',
              '    password: passwd',
              '  access:',
              '  - name: amihura',
              '    permissions:',
              '    - overall',
              '    - credentials',
              '    - gerrit',
              'cli_user:',
              '  name: jenkins-manager',
              '  public_key: sssh-rsa AAAAB3NzaC'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        jsonschema.validate(repo_data, self.schema)

    def test_valid_oneof_password_data(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              'password:',
              '  access:',
              '  - name: amihura',
              '    email: amihura@example.com',
              '    password: passwd',
              '    permissions:',
              '    - overall',
              '    - credentials',
              '    - gerrit',
              'cli_user:',
              '  name: jenkins-manager',
              '  public_key: sssh-rsa AAAAB3NzaC'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        jsonschema.validate(repo_data, self.schema)

    def test_valid_oneof_unsecured_data(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              'unsecured: true',
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        jsonschema.validate(repo_data, self.schema)

    def test_ldap_validation_fail_if_server_is_not_string(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              'ldap:',
              '  server: 123',
              '  root_bind:',
              '    dn: dc=mirantis,dc=com',
              '    allow_blank: false',
              '  search:',
              '    user_filter: userPrincipalName={0}',
              '  manager:',
              '    name: mngr@mirantis.com',
              '    password: passwd',
              'cli_user:',
              '  name: jenkins-manager',
              '  public_key: sssh-rsa AAAAB3NzaC'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "123 is not of type 'string'"

    def test_ldap_validation_fail_if_dn_is_not_string(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              'ldap:',
              '  server: ldap://mirantis.com:3268',
              '  root_bind:',
              '    dn: 123',
              '    allow_blank: false',
              '  search:',
              '    user_filter: userPrincipalName={0}',
              '  manager:',
              '    name: mngr@mirantis.com',
              '    password: passwd',
              'cli_user:',
              '  name: jenkins-manager',
              '  public_key: sssh-rsa AAAAB3NzaC'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "123 is not of type 'string'"

    def test_ldap_validation_fail_if_allow_blank_is_not_bool(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              'ldap:',
              '  server: ldap://mirantis.com:3268',
              '  root_bind:',
              '    dn: dc=mirantis,dc=com',
              '    allow_blank: 123',
              '  search:',
              '    user_filter: userPrincipalName={0}',
              '  manager:',
              '    name: mngr@mirantis.com',
              '    password: passwd',
              'cli_user:',
              '  name: jenkins-manager',
              '  public_key: sssh-rsa AAAAB3NzaC'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "123 is not of type 'boolean'"

    def test_ldap_validation_fail_if_user_filter_is_not_string(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              'ldap:',
              '  server: ldap://mirantis.com:3268',
              '  root_bind:',
              '    dn: dc=mirantis,dc=com',
              '    allow_blank: false',
              '  search:',
              '    user_filter: 123',
              '  manager:',
              '    name: mngr@mirantis.com',
              '    password: passwd',
              'cli_user:',
              '  name: jenkins-manager',
              '  public_key: sssh-rsa AAAAB3NzaC'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "123 is not of type 'string'"

    def test_ldap_validation_fail_if_group_base_is_not_string(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              'ldap:',
              '  server: ldap://mirantis.com:3268',
              '  root_bind:',
              '    dn: dc=mirantis,dc=com',
              '    allow_blank: false',
              '  search:',
              '    user_filter: userPrincipalName={0}',
              '    group_base: 123',
              '  manager:',
              '    name: mngr@mirantis.com',
              '    password: passwd',
              'cli_user:',
              '  name: jenkins-manager',
              '  public_key: sssh-rsa AAAAB3NzaC'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "123 is not of type 'string'"

    def test_ldap_validation_fail_if_user_base_is_not_string(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              'ldap:',
              '  server: ldap://mirantis.com:3268',
              '  root_bind:',
              '    dn: dc=mirantis,dc=com',
              '    allow_blank: false',
              '  search:',
              '    user_filter: userPrincipalName={0}',
              '    user_base: 123',
              '  manager:',
              '    name: mngr@mirantis.com',
              '    password: passwd',
              'cli_user:',
              '  name: jenkins-manager',
              '  public_key: sssh-rsa AAAAB3NzaC'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "123 is not of type 'string'"

    def test_ldap_validation_fail_if_manager_name_is_not_string(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              'ldap:',
              '  server: ldap://mirantis.com:3268',
              '  root_bind:',
              '    dn: dc=mirantis,dc=com',
              '    allow_blank: false',
              '  search:',
              '    user_filter: userPrincipalName={0}',
              '  manager:',
              '    name: 123',
              '    password: passwd',
              'cli_user:',
              '  name: jenkins-manager',
              '  public_key: sssh-rsa AAAAB3NzaC'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "123 is not of type 'string'"

    def test_ldap_validation_fail_if_manager_password_is_not_string(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              'ldap:',
              '  server: ldap://mirantis.com:3268',
              '  root_bind:',
              '    dn: dc=mirantis,dc=com',
              '    allow_blank: false',
              '  search:',
              '    user_filter: userPrincipalName={0}',
              '  manager:',
              '    name: mngr@mirantis.com',
              '    password: 123',
              'cli_user:',
              '  name: jenkins-manager',
              '  public_key: sssh-rsa AAAAB3NzaC'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "123 is not of type 'string'"

    def test_validation_fail_if_cli_username_is_not_string(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              'ldap:',
              '  server: ldap://mirantis.com:3268',
              '  root_bind:',
              '    dn: dc=mirantis,dc=com',
              '    allow_blank: false',
              '  search:',
              '    user_filter: userPrincipalName={0}',
              '  manager:',
              '    name: mngr@mirantis.com',
              '    password: passwd',
              'cli_user:',
              '  name: 123',
              '  public_key: sssh-rsa AAAAB3NzaC'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "123 is not of type 'string'"

    def test_validation_fail_if_cli_pubkey_is_not_string(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              'ldap:',
              '  server: ldap://mirantis.com:3268',
              '  root_bind:',
              '    dn: dc=mirantis,dc=com',
              '    allow_blank: false',
              '  search:',
              '    user_filter: userPrincipalName={0}',
              '  manager:',
              '    name: mngr@mirantis.com',
              '    password: passwd',
              'cli_user:',
              '  name: jenkins-manager',
              '  public_key: 123'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "123 is not of type 'string'"

    def test_ldap_validation_fail_if_access_name_is_not_string(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              'ldap:',
              '  server: ldap://mirantis.com:3268',
              '  root_bind:',
              '    dn: dc=mirantis,dc=com',
              '    allow_blank: false',
              '  search:',
              '    user_filter: userPrincipalName={0}',
              '  manager:',
              '    name: mngr@mirantis.com',
              '    password: passwd',
              '  access:',
              '  - name: 123',
              '    permissions:',
              '    - overall',
              '    - credentials',
              '    - gerrit',
              'cli_user:',
              '  name: jenkins-manager',
              '  public_key: ssh-rsa AAB'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "123 is not of type 'string'"

    def test_ldap_validation_fail_if_permissions_not_enum(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              'ldap:',
              '  server: ldap://mirantis.com:3268',
              '  root_bind:',
              '    dn: dc=mirantis,dc=com',
              '    allow_blank: false',
              '  search:',
              '    user_filter: userPrincipalName={0}',
              '  manager:',
              '    name: mngr@mirantis.com',
              '    password: passwd',
              '  access:',
              '  - name: test',
              '    permissions:',
              '    - test',
              '    - credentials',
              '    - gerrit',
              'cli_user:',
              '  name: jenkins-manager',
              '  public_key: sssh-rsa AAAAB3NzaC'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "'test' is not one of " \
                                        "['overall', 'credentials', 'gerrit', 'manage-ownership', " \
                                        "'slave', 'job', 'run', 'view', 'scm']"

    def test_ldap_validation_fail_for_user_filter_required_property(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              'ldap:',
              '  server: ldap://mirantis.com:3268',
              '  root_bind:',
              '    dn: dc=mirantis,dc=com',
              '    allow_blank: false',
              '  search:',
              '    group_base: ou=group',
              '  manager:',
              '    name: mngr@mirantis.com',
              '    password: passwd',
              'cli_user:',
              '  name: jenkins-manager',
              '  public_key: sssh-rsa AAAAB3NzaC'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "'user_filter' is a required property"

    def test_validation_fail_for_cli_user_name_required_property(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              'ldap:',
              '  server: ldap://mirantis.com:3268',
              '  root_bind:',
              '    dn: dc=mirantis,dc=com',
              '    allow_blank: false',
              '  search:',
              '    user_filter: userPrincipalName={0}',
              '  manager:',
              '    name: mngr@mirantis.com',
              '    password: passwd',
              'cli_user:',
              '  public_key: sssh-rsa AAAAB3NzaC'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "'name' is a required property"

    def test_validation_fail_for_cli_user_pubkey_required_property(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              'ldap:',
              '  server: ldap://mirantis.com:3268',
              '  root_bind:',
              '    dn: dc=mirantis,dc=com',
              '    allow_blank: false',
              '  search:',
              '    user_filter: userPrincipalName={0}',
              '  manager:',
              '    name: mngr@mirantis.com',
              '    password: passwd',
              'cli_user:',
              '  name: jenkins-manager',
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "'public_key' is a required property"

    def test_ldap_validation_fail_for_manager_name_required_property(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              'ldap:',
              '  server: ldap://mirantis.com:3268',
              '  root_bind:',
              '    dn: dc=mirantis,dc=com',
              '    allow_blank: false',
              '  search:',
              '    user_filter: userPrincipalName={0}',
              '  manager:',
              '    password: passwd',
              'cli_user:',
              '  name: jenkins-manager',
              '  public_key: sssh-rsa AAAAB3NzaC'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "'name' is a required property"

    def test_ldap_validation_fail_for_manager_password_required_property(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              'ldap:',
              '  server: ldap://mirantis.com:3268',
              '  root_bind:',
              '    dn: dc=mirantis,dc=com',
              '    allow_blank: false',
              '  search:',
              '    user_filter: userPrincipalName={0}',
              '  manager:',
              '    name: mngr@mirantis.com',
              'cli_user:',
              '  name: jenkins-manager',
              '  public_key: sssh-rsa AAAAB3NzaC'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "'password' is a required property"

    def test_ldap_validation_fail_for_server_required_property(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              'ldap:',
              '  root_bind:',
              '    dn: dc=mirantis,dc=com',
              '    allow_blank: false',
              '  search:',
              '    user_filter: userPrincipalName={0}',
              '  manager:',
              '    name: mngr@mirantis.com',
              '    password: passwd',
              'cli_user:',
              '  name: jenkins-manager',
              '  public_key: sssh-rsa AAAAB3NzaC'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "'server' is a required property"

    def test_ldap_validation_fail_for_root_bind_required_property(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              'ldap:',
              '  server: ldap://mirantis.com:3268',
              '  search:',
              '    user_filter: userPrincipalName={0}',
              '  manager:',
              '    name: mngr@mirantis.com',
              '    password: passwd',
              'cli_user:',
              '  name: jenkins-manager',
              '  public_key: sssh-rsa AAAAB3NzaC'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "'root_bind' is a required property"

    def test_ldap_validation_fail_for_search_required_property(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              'ldap:',
              '  server: ldap://mirantis.com:3268',
              '  root_bind:',
              '    dn: dc=mirantis,dc=com',
              '    allow_blank: false',
              '  manager:',
              '    name: mngr@mirantis.com',
              '    password: passwd',
              'cli_user:',
              '  name: jenkins-manager',
              '  public_key: sssh-rsa AAAAB3NzaC'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "'search' is a required property"

    def test_ldap_validation_fail_for_manager_required_property(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              'ldap:',
              '  server: ldap://mirantis.com:3268',
              '  root_bind:',
              '    dn: dc=mirantis,dc=com',
              '    allow_blank: false',
              '  search:',
              '    user_filter: userPrincipalName={0}',
              'cli_user:',
              '  name: jenkins-manager',
              '  public_key: sssh-rsa AAAAB3NzaC'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "'manager' is a required property"

    def test_ldap_validation_fail_if_access_not_array(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              'ldap:',
              '  server: ldap://mirantis.com:3268',
              '  root_bind:',
              '    dn: dc=mirantis,dc=com',
              '    allow_blank: false',
              '  search:',
              '    user_filter: userPrincipalName={0}',
              '  access: 123',
              '  manager:',
              '    name: mngr@mirantis.com',
              '    password: passwd',
              'cli_user:',
              '  name: jenkins-manager',
              '  public_key: sssh-rsa AAAAB3NzaC'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "123 is not of type 'array'"

    def test_ldap_validation_fail_if_search_not_object(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              'ldap:',
              '  server: ldap://mirantis.com:3268',
              '  root_bind:',
              '    dn: dc=mirantis,dc=com',
              '    allow_blank: false',
              '  search: 123',
              '  manager:',
              '    name: mngr@mirantis.com',
              '    password: passwd',
              'cli_user:',
              '  name: jenkins-manager',
              '  public_key: sssh-rsa AAAAB3NzaC'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "123 is not of type 'object'"

    def test_ldap_validation_fail_if_root_dn_not_object(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              'ldap:',
              '  server: ldap://mirantis.com:3268',
              '  root_bind: 123',
              '  search:',
              '    user_filter: userPrincipalName={0}',
              '  manager:',
              '    name: mngr@mirantis.com',
              '    password: passwd',
              'cli_user:',
              '  name: jenkins-manager',
              '  public_key: sssh-rsa AAAAB3NzaC'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "123 is not of type 'object'"

    def test_validation_fail_if_cli_user_not_object(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              'ldap:',
              '  server: ldap://mirantis.com:3268',
              '  root_bind:',
              '    dn: dc=mirantis,dc=com',
              '    allow_blank: false',
              '  search:',
              '    user_filter: userPrincipalName={0}',
              '  manager:',
              '    name: mngr@mirantis.com',
              '    password: passwd',
              'cli_user: 123',
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "123 is not of type 'object'"

    def test_password_validation_fail_if_access_name_is_not_string(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              'password:',
              '  access:',
              '  - name: 123',
              '    email: amihura@example.com',
              '    password: passwd',
              '    permissions:',
              '    - overall',
              '    - credentials',
              '    - gerrit',
              'cli_user:',
              '  name: jenkins-manager',
              '  public_key: sssh-rsa AAAAB3NzaC'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "123 is not of type 'string'"

    def test_password_validation_fail_if_email_is_not_string(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              'password:',
              '  access:',
              '  - name: amihura',
              '    email: 123',
              '    password: passwd',
              '    permissions:',
              '    - overall',
              '    - credentials',
              '    - gerrit',
              'cli_user:',
              '  name: jenkins-manager',
              '  public_key: sssh-rsa AAAAB3NzaC'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "123 is not of type 'string'"

    def test_password_validation_fail_if_password_is_not_string(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              'password:',
              '  access:',
              '  - name: amihura',
              '    email: amihura@example.com',
              '    password: 123',
              '    permissions:',
              '    - overall',
              '    - credentials',
              '    - gerrit',
              'cli_user:',
              '  name: jenkins-manager',
              '  public_key: sssh-rsa AAAAB3NzaC'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "123 is not of type 'string'"

    def test_password_validation_fail_if_full_name_is_not_string(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              'password:',
              '  access:',
              '  - name: amihura',
              '    email: amihura@example.com',
              '    password: passwd',
              '    full_name: 123',
              '    permissions:',
              '    - overall',
              '    - credentials',
              '    - gerrit',
              'cli_user:',
              '  name: jenkins-manager',
              '  public_key: sssh-rsa AAAAB3NzaC'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "123 is not of type 'string'"

    def test_password_validation_fail_if_pub_key_is_not_string(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              'password:',
              '  access:',
              '  - name: amihura',
              '    email: amihura@example.com',
              '    password: passwd',
              '    ssh_public_key: 123',
              '    permissions:',
              '    - overall',
              '    - credentials',
              '    - gerrit',
              'cli_user:',
              '  name: jenkins-manager',
              '  public_key: sssh-rsa AAAAB3NzaC'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "123 is not of type 'string'"

    def test_password_validation_fail_for_access_name_required_property(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              'password:',
              '  access:',
              '  - email: amihura@example.com',
              '    password: passwd',
              '    ssh_public_key: ssh AAA',
              '    permissions:',
              '    - overall',
              '    - credentials',
              '    - gerrit',
              'cli_user:',
              '  name: jenkins-manager',
              '  public_key: sssh-rsa AAAAB3NzaC'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "'name' is a required property"

    def test_password_validation_fail_for_access_perms_required_property(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              'password:',
              '  access:',
              '  - name: amihura',
              '    email: amihura@example.com',
              '    password: passwd',
              '    ssh_public_key: 123',
              'cli_user:',
              '  name: jenkins-manager',
              '  public_key: sssh-rsa AAAAB3NzaC'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "'permissions' is a required property"

    def test_password_validation_fail_for_access_email_required_property(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              'password:',
              '  access:',
              '  - name: amihura',
              '    password: passwd',
              '    ssh_public_key: 123',
              '    permissions:',
              '    - overall',
              '    - credentials',
              '    - gerrit',
              'cli_user:',
              '  name: jenkins-manager',
              '  public_key: sssh-rsa AAAAB3NzaC'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "'email' is a required property"

    def test_password_validation_fail_for_access_password_required_property(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              'password:',
              '  access:',
              '  - name: amihura',
              '    email: amihura@example.com',
              '    ssh_public_key: 123',
              '    permissions:',
              '    - overall',
              '    - credentials',
              '    - gerrit',
              'cli_user:',
              '  name: jenkins-manager',
              '  public_key: sssh-rsa AAAAB3NzaC'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "'password' is a required property"

    def test_validation_fail_if_unsecured_not_bool(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              'unsecured: 123'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "123 is not of type 'boolean'"

    def test_validation_fail_for_ldap_additional_properties(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              'ldap:',
              '  server: ldap://mirantis.com:3268',
              '  root_bind:',
              '    dn: dc=mirantis,dc=com',
              '    allow_blank: false',
              '  search:',
              '    user_filter: userPrincipalName={0}',
              '  manager:',
              '    name: mngr@mirantis.com',
              '    password: passwd',
              '  test: test',
              'cli_user:',
              '  name: jenkins-manager',
              '  public_key: sssh-rsa AAAAB3NzaC'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "Additional properties are not allowed ('test' was unexpected)"

    def test_validation_fail_for_password_additional_properties(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              'password:',
              '  test: test',
              'cli_user:',
              '  name: jenkins-manager',
              '  public_key: sssh-rsa AAAAB3NzaC'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "Additional properties are not allowed ('test' was unexpected)"

    def test_validation_fail_for_unsecured_additional_properties(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              'unsecured: true',
              'test: test'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "Additional properties are not allowed ('test' was unexpected)"
