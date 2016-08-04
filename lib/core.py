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

import importlib
from itertools import chain
import logging
import os
from pkg_resources import resource_filename
import sys

from lib.api import Plugin, BaseGroovyPlugin
from lib.common import TreeHelpersMixin, ReadersMixin, LoggerMixin

logger = logging.getLogger(__name__)


def load_py_modules(*paths):
    """:returns: modules from plugins-directory"""

    modules = []
    logger.debug('Loading modules from {}'.format(', '.join(paths)))
    abspaths = [os.path.abspath(path) for path in paths]

    for path in abspaths:
        try:
            sys.path.insert(0, path)

            for item in os.listdir(path):
                itempath = os.path.join(path, item)

                if os.path.isfile(os.path.join(itempath, '__init__.py')):
                    logger.info("Importing {itempath}".format(**locals()))
                    modules.append(importlib.import_module(item))

                if itempath.endswith('.py'):
                    logger.info("Importing {itempath}".format(**locals()))
                    modules.append(importlib.import_module(item[:-3]))
        finally:
            sys.path.pop(0)

    return modules


def extract_plugins(*modules):
    """:returns: plugins found in imported modules"""

    plugins = []

    for module in modules:
        logger.debug('Looking for plugins in module "{}"'.format(module.__name__))

        for itemname in dir(module):
            if itemname.startswith('_'):
                continue

            item = getattr(module, itemname)

            if not isinstance(item, type):
                continue

            if item is Plugin:
                continue

            if item is BaseGroovyPlugin:
                continue

            if issubclass(item, Plugin):
                logger.info('Found plugin: "{}"'.format(item.__name__))
                plugins.append(item)

    return plugins


def load_plugins(*paths):
    return extract_plugins(*load_py_modules(*paths))


class Runner(TreeHelpersMixin, ReadersMixin, LoggerMixin):
    schema_rel_path = 'schema.yaml'

    @property
    def schema_path(self):
        """:returns: absolute path for configuration schema"""

        return os.path.join(os.path.dirname(__file__), self.schema_rel_path)

    def __init__(self, conf_path, pipeline_name, env_name):
        self.conf_path = conf_path
        self.pipeline_name = pipeline_name
        self.env_name = env_name

        self.ctx = {
            'plugins': [],
            'config': {},
            'results': {},
            'env': {}
        }

        self.steps = []

    # --- ctx shortcuts ---

    @property
    def config(self):
        return self.ctx['config']

    @property
    def plugins(self):
        return self.ctx['plugins']

    @property
    def env(self):
        return self.ctx['env']

    # --- main workflow related methods ---

    def run(self):
        self.read_conf()
        self.build_steps()
        self.set_env()
        self.load_plugins()
        self.execute_steps()

    def read_conf(self):
        """Read jimmy yaml configuration file and validate it using schema"""

        self.config.update(self.yaml_reader.read(self.conf_path))
        schema = self.yaml_reader.read(self.schema_path)
        try:
            self.jsonschema_validator.validate(self.config, schema)
        except self.jsonschema_validator.ValidationError as e:
            self.logger.error('Config is not valid: "{}", path: "{}"'.format(e.message, '.'.join(map(str, e.path))))

    def build_steps(self):
        """Build pipeline, steps from jimmy yaml configuration file"""

        pipeline = self._tree_read(self.config, ['pipelines', self.pipeline_name])

        config = self.config

        if not pipeline:
            self.logger.error('No such pipeline {}').format(self.pipeline_name)

        self.logger.info('Pipeline is: \n{}'.format(self.yaml_renderer.render(pipeline)))

        self.logger.info('Building pipeline steps')
        for step in chain(
                self._tree_read(self.config, ['setup'], []),
                self._tree_read(pipeline, ['steps'], []),
                self._tree_read(config, ['teardown'], []),
        ):
            step_name = step['name']

            inject = {}
            for k, v in chain(
                    self._tree_read(config, ['defaults', 'inject'], {}).iteritems(),
                    self._tree_read(config, ['defaults', 'inject', step_name], {}).iteritems(),
                    self._tree_read(pipeline, ['inject'], {}).iteritems(),
                    self._tree_read(step, ['inject'], {}).iteritems()
            ):
                inject[k] = v

            params = {}
            for k, v in chain(
                    self._tree_read(config, ['defaults', 'params'], {}).iteritems(),
                    self._tree_read(config, ['defaults', 'params', step_name], {}).iteritems(),
                    self._tree_read(pipeline, ['params'], {}).iteritems(),
                    self._tree_read(step, ['params'], {}).iteritems()
            ):
                if k not in inject:
                    params[k] = v

            _step = {'name': step_name}
            if inject:
                _step['inject'] = inject
            if params:
                _step['params'] = params

            self.steps.append(_step)
        self.logger.debug('Pipeline steps will be: \n{}'.format(self.yaml_renderer.render(pipeline)))

    def set_env(self):
        """Setup environment"""

        self.logger.debug('Setup env')
        self.ctx['env'].update(self._tree_read(self.config, ['envs', self.env_name], {}))

    def get_default_plugins_path(self):
        """Get default plugins"""

        resource_package = __name__
        plugins_dir = '../plugins'
        default_plugins_path = os.path.abspath(resource_filename(resource_package, plugins_dir))

        return default_plugins_path

    def load_plugins(self):
        """Loading plugins"""

        self.logger.info('Loading Plugins')
        plugin_paths = self._tree_read(self.config, ['plugin-directories'], [])
        if self._tree_read(self.config, ['include-default-plugins'], True):
            plugin_paths.append(self.get_default_plugins_path())
        self.plugins.extend([p() for p in load_plugins(*plugin_paths)])

    def execute_steps(self):
        """Execute pipeline steps and invoke plugins for each step"""

        self.logger.debug('Executing pipeline "{}"'.format(self.pipeline_name))

        for step in self.steps:
            step_name = step['name']
            self.logger.info('Executing step "{}"'.format(step_name))

            for plugin in self.plugins:
                if hasattr(plugin, step_name) and not plugin.skip:
                    params = self._tree_read(step, ['params'], {})
                    injections = {
                        key: self._tree_read(self.ctx, ctx_path)
                        for key, ctx_path
                        in self._tree_read(step, ['inject'], {}).iteritems()
                    }

                    kwargs = {}

                    kwargs.update(params)
                    kwargs.update(injections)

                    self.logger.debug('Invoking plugin "{}"'.format(plugin.__class__.__name__))
                    try:
                        value = getattr(plugin, step_name)(**kwargs)
                        if value:
                            self._tree_update(self.ctx, ['results', step_name], value)
                    except StandardError as e:
                        self.logger.error(e)
                        raise
