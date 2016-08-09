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
throttle_schema_path = os.path.join(plugins_dir, 'throttle', 'resources', 'schema.yaml')
jenkins_yaml_path = os.path.join(jimmy_dir, 'sample', 'input', 'jenkins.yaml')


class TestThrottlePlugin(base.TestCase):

    def setup_method(self, method):
        self.runner = CliRunner()

    def teardown_method(self, method):
        mockfs.restore_builtins()

    @mock.patch('lib.core.load_py_modules')
    @mock.patch('subprocess.call')
    def test_cli_call(self, mock_subp, mock_modules):
        with open(throttle_schema_path, 'r') as f:
            mock_throttle_schema = f.read()
        self.mfs = mockfs.replace_builtins()
        self.mfs.add_entries({os.path.join(jimmy_dir, 'lib', 'schema.yaml'): self.jimmy_schema,
                              os.path.join(jimmy_dir, 'jimmy.yaml'): self.mock_jimmy_yaml,
                              throttle_schema_path: mock_throttle_schema,
                              jenkins_yaml_path: '\n'.join(
                                  [
                                      'jenkins:',
                                      '  throttle:',
                                      '    categories:',
                                      '    - category_name: category1',
                                      '      max_total_concurrent_builds: 1',
                                      '      max_concurrent_bulds_per_node: 0',
                                      '      max_per_labeled_node:',
                                      '      - throttled_node_label: slave-label1',
                                      '        max_concurrent_per_labeled: 1',
                                      '      - throttled_node_label: slave-label2',
                                      '        max_concurrent_per_labeled: 1',
                                      '    - category_name: category2',
                                      '      max_total_concurrent_builds: 1',
                                      '      max_concurrent_bulds_per_node: 0'
                                  ])
                              })
        sys.path.insert(0, plugins_dir)
        import throttle
        import read_source
        sys.path.pop(0)
        mock_modules.return_value = [throttle, read_source]
        os.chdir(jimmy_dir)
        self.runner.invoke(cli)
        calls = [call(['java',
                       '-jar', '<< path to jenkins-cli.jar >>',
                       '-s', 'http://localhost:8080', 'groovy',
                       plugins_dir + '/' + 'throttle/resources/jenkins.groovy',
                       'clear_categories'],
                      shell=False),
                 call(['java',
                       '-jar', '<< path to jenkins-cli.jar >>',
                       '-s', 'http://localhost:8080', 'groovy',
                       plugins_dir + '/' + 'throttle/resources/jenkins.groovy',
                       'create_throttle_category',
                       'category1', '1', '0', 'slave-label1,slave-label2', '1,1'],
                      shell=False),
                 call(['java',
                       '-jar', '<< path to jenkins-cli.jar >>',
                       '-s', 'http://localhost:8080', 'groovy',
                       plugins_dir + '/' + 'throttle/resources/jenkins.groovy',
                       'create_throttle_category',
                       'category2', '1', '0', '', ''],
                      shell=False)
                 ]
        mock_subp.assert_has_calls(calls, any_order=True)
        assert 3 == mock_subp.call_count, "subprocess call should be equal to 3"


class TestThrottleSchema(object):

    def setup_method(self, method):
        with open(throttle_schema_path, 'r') as f:
            mock_throttle_schema = f.read()
        self.mfs = mockfs.replace_builtins()
        self.mfs.add_entries({throttle_schema_path: mock_throttle_schema})
        self.schema = yaml_reader.read(throttle_schema_path)

    def teardown_method(self, method):
        mockfs.restore_builtins()

    def test_valid_repo_data(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              'categories:',
              '- category_name: category1',
              '  max_total_concurrent_builds: 1',
              '  max_concurrent_bulds_per_node: 0',
              '  max_per_labeled_node:',
              '  - throttled_node_label: slave-label1',
              '    max_concurrent_per_labeled: 1'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        jsonschema.validate(repo_data, self.schema)

    def test_validation_fail_if_category_name_is_not_string(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              'categories:',
              '- category_name: 123',
              '  max_total_concurrent_builds: 1',
              '  max_concurrent_bulds_per_node: 0',
              '  max_per_labeled_node:',
              '  - throttled_node_label: slave-label1',
              '    max_concurrent_per_labeled: 1'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "123 is not of type 'string'"

    def test_validation_fail_if_max_total_concurrent_builds_is_not_num(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              'categories:',
              '- category_name: category1',
              '  max_total_concurrent_builds: test',
              '  max_concurrent_bulds_per_node: 0',
              '  max_per_labeled_node:',
              '  - throttled_node_label: slave-label1',
              '    max_concurrent_per_labeled: 1'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "'test' is not of type 'number'"

    def test_validation_fail_if_max_concurrent_bulds_per_node_is_not_num(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              'categories:',
              '- category_name: category1',
              '  max_total_concurrent_builds: 1',
              '  max_concurrent_bulds_per_node: test',
              '  max_per_labeled_node:',
              '  - throttled_node_label: slave-label1',
              '    max_concurrent_per_labeled: 1'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "'test' is not of type 'number'"

    def test_validation_fail_if_throttled_node_label_is_not_string(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              'categories:',
              '- category_name: category1',
              '  max_total_concurrent_builds: 1',
              '  max_concurrent_bulds_per_node: 0',
              '  max_per_labeled_node:',
              '  - throttled_node_label: 123',
              '    max_concurrent_per_labeled: 1'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "123 is not of type 'string'"

    def test_validation_fail_if_max_concurrent_per_labeled_is_not_num(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              'categories:',
              '- category_name: category1',
              '  max_total_concurrent_builds: 1',
              '  max_concurrent_bulds_per_node: 0',
              '  max_per_labeled_node:',
              '  - throttled_node_label: slave-label1',
              '    max_concurrent_per_labeled: test'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "'test' is not of type 'number'"

    def test_password_validation_fail_for_category_name_required_property(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              'categories:',
              '- max_total_concurrent_builds: 1',
              '  max_concurrent_bulds_per_node: 0',
              '  max_per_labeled_node:',
              '  - throttled_node_label: slave-label1',
              '    max_concurrent_per_labeled: 1'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "'category_name' is a required property"

    def test_password_validation_fail_for_max_total_conc_builds_required_property(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              'categories:',
              '- category_name: category1',
              '  max_concurrent_bulds_per_node: 0',
              '  max_per_labeled_node:',
              '  - throttled_node_label: slave-label1',
              '    max_concurrent_per_labeled: 1'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "'max_total_concurrent_builds' is a required property"

    def test_password_validation_fail_for_max_conc_builds_per_node_required_property(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              'categories:',
              '- category_name: category1',
              '  max_total_concurrent_builds: 1',
              '  max_per_labeled_node:',
              '  - throttled_node_label: slave-label1',
              '    max_concurrent_per_labeled: 1'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "'max_concurrent_bulds_per_node' is a required property"

    def test_password_validation_fail_for_throttled_node_label_required_property(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              'categories:',
              '- category_name: category1',
              '  max_total_concurrent_builds: 1',
              '  max_concurrent_bulds_per_node: 0',
              '  max_per_labeled_node:',
              '  - max_concurrent_per_labeled: 1'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "'throttled_node_label' is a required property"

    def test_password_validation_fail_for_max_concurrent_per_labeled_required_property(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              'categories:',
              '- category_name: category1',
              '  max_total_concurrent_builds: 1',
              '  max_concurrent_bulds_per_node: 0',
              '  max_per_labeled_node:',
              '  - throttled_node_label: slave-label1'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "'max_concurrent_per_labeled' is a required property"

    def test_validation_fail_if_categories_not_array(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              'categories: 123'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "123 is not of type 'array'"

    def test_validation_fail_if_max_per_labeled_node_not_array(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              'categories:',
              '- category_name: category1',
              '  max_total_concurrent_builds: 1',
              '  max_concurrent_bulds_per_node: 0',
              '  max_per_labeled_node: 123'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "123 is not of type 'array'"

    def test_validation_fail_for_categories_additional_properties(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              'categories:',
              '- category_name: category1',
              '  max_total_concurrent_builds: 1',
              '  max_concurrent_bulds_per_node: 0',
              '  test: test'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "Additional properties are not allowed ('test' was unexpected)"

    def test_validation_fail_for_max_per_labeled_node_additional_properties(self):
        self.mfs.add_entries({jenkins_yaml_path: '\n'.join(
            [
              'categories:',
              '- category_name: category1',
              '  max_total_concurrent_builds: 1',
              '  max_concurrent_bulds_per_node: 0',
              '  max_per_labeled_node:',
              '  - throttled_node_label: slave-label1',
              '    max_concurrent_per_labeled: 1',
              '    test: test'
            ])
        })
        repo_data = yaml_reader.read(jenkins_yaml_path)
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(repo_data, self.schema)
        assert excinfo.value.message == "Additional properties are not allowed ('test' was unexpected)"
