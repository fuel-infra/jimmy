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
pipeline_libraries_schema_path = os.path.join(plugins_dir, 'pipeline_libraries', 'resources', 'schema.yaml')
jenkins_yaml_path = os.path.join(jimmy_dir, 'sample', 'input', 'jenkins.yaml')


class TestPipelineLibrariesPlugin(base.TestCase):

    def setup_method(self, method):
        self.runner = CliRunner()

    def teardown_method(self, method):
        mockfs.restore_builtins()

    @mock.patch('lib.core.load_py_modules')
    @mock.patch('subprocess.call')
    def test_cli_call(self, mock_subp, mock_modules):
        with open(pipeline_libraries_schema_path, 'r') as f:
            mock_pipeline_libraries_schema = f.read()
        self.mfs = mockfs.replace_builtins()
        self.mfs.add_entries({os.path.join(jimmy_dir, 'lib', 'schema.yaml'): self.jimmy_schema,
                              os.path.join(jimmy_dir, 'jimmy.yaml'): self.mock_jimmy_yaml,
                              pipeline_libraries_schema_path: mock_pipeline_libraries_schema,
                              jenkins_yaml_path: '\n'.join(
                                  [
                                      'jenkins:',
                                      '  pipeline_libraries:',
                                      '    libraries:',
                                      '    - name: shared-lib',
                                      '      git_url: https://github.com/example/shared-lib',
                                      '      git_branch: master',
                                      '      default_version: release-0.1',
                                      '      load_implicitly: true',
                                      '      allow_version_override: false',
                                      '    - name: shared-lib-dev',
                                      '      git_url: https://github.com/example/shared-lib-dev',
                                      '      git_branch: master',
                                      '      default_version: master',
                                      '      load_implicitly: false',
                                      '      allow_version_override: true'
                                  ])
                              })
        sys.path.insert(0, plugins_dir)
        import pipeline_libraries
        import read_source
        sys.path.pop(0)
        mock_modules.return_value = [pipeline_libraries, read_source]
        os.chdir(jimmy_dir)
        self.runner.invoke(cli)
        calls = [call(['java',
                       '-jar', '<< path to jenkins-cli.jar >>',
                       '-s', 'http://localhost:8080', 'groovy',
                       plugins_dir + '/' + 'pipeline_libraries/resources/jenkins.groovy',
                       'set_global_library',
                       'shared-lib',
                       'https://github.com/example/shared-lib',
                       'master',
                       'release-0.1',
                       'True',
                       'False'],
                      shell=False),
                 call(['java',
                       '-jar', '<< path to jenkins-cli.jar >>',
                       '-s', 'http://localhost:8080', 'groovy',
                       plugins_dir + '/' + 'pipeline_libraries/resources/jenkins.groovy',
                       'set_global_library',
                       'shared-lib-dev',
                       'https://github.com/example/shared-lib-dev',
                       'master',
                       'master',
                       'False',
                       'True'],
                      shell=False)]
        print calls
        mock_subp.assert_has_calls(calls, any_order=True)
        assert 2 == mock_subp.call_count, "subprocess call should be equal to 2"


class TestPipelineLibrariesSchema(object):

    def setup_method(self, method):
        with open(pipeline_libraries_schema_path, 'r') as f:
            mock_pipeline_libraries_schema = f.read()
        self.mfs = mockfs.replace_builtins()
        self.mfs.add_entries({pipeline_libraries_schema_path: mock_pipeline_libraries_schema})
        self.schema = yaml_reader.read(pipeline_libraries_schema_path)

    def teardown_method(self, method):
        mockfs.restore_builtins()

    def test_valid_repo_data(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              '    libraries:',
              '    - name: shared-lib',
              '      git_url: https://github.com/example/shared-lib',
              '      git_branch: master',
              '      default_version: release-0.1',
              '      load_implicitly: true',
              '      allow_version_override: false',
              '    - name: shared-lib-dev',
              '      git_url: https://github.com/example/shared-lib-dev',
              '      git_branch: master',
              '      default_version: master',
              '      load_implicitly: false',
              '      allow_version_override: true'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        jsonschema.validate(repo_data, self.schema)

    def test_validation_fail_if_name_is_not_string(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              '    libraries:',
              '    - name: 123',
              '      git_url: https://github.com/example/shared-lib',
              '      git_branch: master',
              '      default_version: release-0.1',
              '      load_implicitly: true',
              '      allow_version_override: false'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "123 is not of type 'string'"

    def test_validation_fail_if_git_url_is_not_string(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              '    libraries:',
              '    - name: shared-lib',
              '      git_url: 123',
              '      git_branch: master',
              '      default_version: release-0.1',
              '      load_implicitly: true',
              '      allow_version_override: false'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "123 is not of type 'string'"

    def test_validation_fail_if_git_branch_is_not_string(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              '    libraries:',
              '    - name: shared-lib',
              '      git_url: https://github.com/example/shared-lib',
              '      git_branch: 123',
              '      default_version: release-0.1',
              '      load_implicitly: true',
              '      allow_version_override: false'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "123 is not of type 'string'"

    def test_validation_fail_if_default_version_is_not_string(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              '    libraries:',
              '    - name: shared-lib',
              '      git_url: https://github.com/example/shared-lib',
              '      git_branch: master',
              '      default_version: 123',
              '      load_implicitly: true',
              '      allow_version_override: false'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "123 is not of type 'string'"

    def test_validation_fail_if_load_implicitly_is_not_boolean(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              '    libraries:',
              '    - name: shared-lib',
              '      git_url: https://github.com/example/shared-lib',
              '      git_branch: master',
              '      default_version: release-0.1',
              '      load_implicitly: 123',
              '      allow_version_override: false'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "123 is not of type 'boolean'"

    def test_validation_fail_if_allow_version_override_is_not_string(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              '    libraries:',
              '    - name: shared-lib',
              '      git_url: https://github.com/example/shared-lib',
              '      git_branch: master',
              '      default_version: release-0.1',
              '      load_implicitly: true',
              '      allow_version_override: 123',
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "123 is not of type 'boolean'"

    def test_validation_fail_for_name_required_property(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              '    libraries:',
              '    - git_url: https://github.com/example/shared-lib',
              '      git_branch: master',
              '      default_version: release-0.1',
              '      load_implicitly: true',
              '      allow_version_override: false'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "'name' is a required property"

    def test_validation_fail_for_git_url_required_property(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              '    libraries:',
              '    - name: shared-lib',
              '      git_branch: master',
              '      default_version: release-0.1',
              '      load_implicitly: true',
              '      allow_version_override: false',
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "'git_url' is a required property"

    def test_validation_fail_for_git_branch_required_property(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              '    libraries:',
              '    - name: shared-lib',
              '      git_url: https://github.com/example/shared-lib',
              '      default_version: release-0.1',
              '      load_implicitly: true',
              '      allow_version_override: false'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "'git_branch' is a required property"

    def test_validation_fail_for_default_version_required_property(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              '    libraries:',
              '    - name: shared-lib',
              '      git_url: https://github.com/example/shared-lib',
              '      git_branch: master',
              '      load_implicitly: true',
              '      allow_version_override: false'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "'default_version' is a required property"

    def test_validation_fail_for_load_implicitly_required_property(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              '    libraries:',
              '    - name: shared-lib',
              '      git_url: https://github.com/example/shared-lib',
              '      git_branch: master',
              '      default_version: release-0.1',
              '      allow_version_override: false'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "'load_implicitly' is a required property"

    def test_validation_fail_for_allow_version_override_required_property(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              '    libraries:',
              '    - name: shared-lib',
              '      git_url: https://github.com/example/shared-lib',
              '      git_branch: master',
              '      default_version: release-0.1',
              '      load_implicitly: true'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "'allow_version_override' is a required property"

    def test_validation_fail_if_libraries_is_not_array(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              'libraries: 123'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "123 is not of type 'array'"

    def test_validation_fail_for_additional_properties(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              '    libraries:',
              '    - name: shared-lib',
              '      git_url: https://github.com/example/shared-lib',
              '      git_branch: master',
              '      default_version: release-0.1',
              '      load_implicitly: true',
              '      allow_version_override: true',
              '      test: test'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "Additional properties are not allowed ('test' was unexpected)"
