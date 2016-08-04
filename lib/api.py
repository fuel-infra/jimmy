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
        """
        Directory on file system where module with this class is located

        :rtype: str
        """
        return os.path.dirname((__import__(self.__class__.__module__)).__file__)

    def build_relative_path(self, subpath):
        """
        Get path relative to directory with current class
        :rtype: str
        """
        return os.path.join(self.class_base_dir, subpath)


class BaseGroovyPlugin(Plugin):
    """
    Base class for Grovy plugins definitions

    :cvar source_tree_path: path on context which contains plugin related data
    :cvar rel_path_schema: relative path to jsonschema for plugin data on context tree
    :cvar rel_path_groovy: relative path to groovy script which stands begind plugin
    """
    source_tree_path = ''
    rel_path_schema = 'resources/schema.yaml'
    rel_path_groovy = 'resources/jenkins.groovy'

    @property
    def groovy_path(self):
        """
        Absolute path on filesystem to groovy script

        :rtype: str
        """
        return os.path.join(self.class_base_dir, self.rel_path_groovy)

    def __init__(self):
        self.schema = None
        self.skip = False

    def check_applicable(self, source, **k):
        """
        Check whether this plugin should run or not

        This method is a build step.
        Most of the plugins do require some configuration subtree on config.
        If there are no required configuration, then plugin could not be applied.

        :param source: jimmy config
        :type source: dict

        :rtype: None
        """
        subtree = self._tree_read(source, self.source_tree_path)
        if not subtree:
            self.logger.info(
                'Module {} is not applicable for this YAML configuration'.format(self.__class__.__name__))
            self.skip = True

    def setup(self, **kwargs):
        """
        Setup plugin

        This method is a build step where all required resources are fetched

        :rtype: None
        """
        self.logger.info('Reading schema from {}'.format(self.rel_path_schema))
        self.schema = self.yaml_reader.read(self.build_relative_path(self.rel_path_schema))

    def validate_source(self, source, **k):
        """
        Validates config

        This method is a build step where subtree of config related to plugin is
        checked against its jsonschema.

        :rtype: None
        """
        subtree = self._tree_read(source, self.source_tree_path)
        self.jsonschema_validator.validate(subtree, self.schema)
