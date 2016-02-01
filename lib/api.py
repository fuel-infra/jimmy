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

import os
from lib.common import TreeHelpersMixin, ReadersMixin, LoggerMixin


class Plugin(TreeHelpersMixin, ReadersMixin, LoggerMixin):
    @property
    def class_base_dir(self):
        return os.path.dirname((__import__(self.__class__.__module__)).__file__)

    def build_relative_path(self, subpath):
        return os.path.join(self.class_base_dir, subpath)


class BaseGroovyPlugin(Plugin):
    rel_path_schema = 'resources/schema.yaml'
    rel_path_groovy = 'resources/jenkins.groovy'

    source_tree_path = ''

    allow_empty = False

    @property
    def groovy_path(self):
        return os.path.join(self.class_base_dir, self.rel_path_groovy)

    def __init__(self):
        self.schema = None

    def setup(self, **kwargs):
        self.logger.info('Reading schema from {}'.format(self.rel_path_schema))
        self.schema = self.yaml_reader.read(self.build_relative_path(self.rel_path_schema))

    def validate_source(self, source, **k):
        subtree = self._tree_read(source, self.source_tree_path)
        self.jsonschema_validator.validate(subtree, self.schema)
