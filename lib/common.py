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

from ConfigParser import RawConfigParser
from copy import copy
import jsonschema
import os
import logging

import yaml

logger = logging.getLogger(__name__)

# --- logging ---

# noinspection PyProtectedMember
LOG_LEVELS = {
    k: v
    for k, v in logging._levelNames.iteritems()
    if not isinstance(k, int)}
LOG_LEVELS_NAMES_LOWER = [ll.lower() for ll in LOG_LEVELS.keys()]


# --- Mixins for logger, readers, tree helpers ---

class LoggerMixin(object):
    @property
    def logger(self):
        return logging.getLogger(
            '.'.join((
                self.__class__.__module__,
                self.__class__.__name__)))


class ReadersMixin(object):
    @property
    def yaml_reader(self):
        return yaml_reader

    @property
    def conf_reader(self):
        return conf_reader

    @property
    def proplist_reader(self):
        return proplist_reader

    @property
    def jsonschema_validator(self):
        return jsonschema_validator

    @property
    def yaml_renderer(self):
        return yaml_renderer


class TreeHelpersMixin(object):
    @staticmethod
    def _tree_read(src, path, default=None):
        if isinstance(path, basestring):
            path = path.split('.')

        for part in path:
            src = (src or {}).get(part)

        if src is None:
            return default

        return src

    @staticmethod
    def _tree_write(dst, path, value):
        if isinstance(path, basestring):
            path = path.split('.')
        else:
            path = copy(path)

        last = path.pop(len(path) - 1)

        for part in path:
            dst = dst.setdefault(part, {})
        dst[last] = value
        return value

    @staticmethod
    def _tree_check(src, path):
        if isinstance(path, basestring):
            path = path.split('.')
            intype = 'str'
        else:
            path = copy(path)
            intype = 'list'

        exists = []
        for part in path:
            if part not in src:
                break

            src = src[part]
            exists.append(part)

        if intype == 'str':
            return '.'.join(exists)
        else:
            return exists

    def _tree_update(self, src, path, value):
        dest = self._tree_read(src, path)
        if not dest:
            self._tree_write(src, path, value)
        else:
            dest.update(value)


# --- readers ---

class YamlWithImportsLoader(yaml.Loader):
    # http://stackoverflow.com/a/12252293/1243636
    def __init__(self, *args, **kwargs):
        super(YamlWithImportsLoader, self).__init__(*args, **kwargs)

        if 'root' in kwargs:
            self.root = kwargs['root']
        elif isinstance(self.stream, file):
            self.root = os.path.dirname(self.stream.name)
        else:
            self.root = os.path.curdir

        # yaml.Loader requires unbound method ..
        self.add_constructor('!include-relative-yaml:', self.__class__._include_relative_yaml)
        self.add_constructor('!include-relative-text:', self.__class__._include_relative_text)
        self.add_constructor('!include-relative-proplist:', self.__class__._include_relative_proplist)
        self.add_constructor('!import-from-cfg:', self.__class__._import_from_cfg)

    def _include_relative_text(self, node):
        filename = os.path.join(self.root, self.construct_scalar(node))
        with open(filename, 'r') as f:
            data = f.read()
        return data

    def _include_relative_yaml(self, node):
        old_root = self.root
        filename = os.path.join(self.root, self.construct_scalar(node))
        self.root = os.path.dirname(filename)
        data = yaml.load(open(filename, 'r'), type(self))
        self.root = old_root
        return data

    def _include_relative_proplist(self, node):
        filename = os.path.join(self.root, self.construct_scalar(node))
        return proplist_reader.read(filename)

    def _import_from_cfg(self, node):
        input_str = self.construct_scalar(node)

        file_path, section_name, option_name = input_str.split(':')

        cfg = conf_reader.read(file_path)

        data = cfg[section_name][option_name]
        return data


class YamlReader(ReadersMixin, LoggerMixin):
    Loader = YamlWithImportsLoader

    def read(self, path_to_file):
        path_to_file = os.path.abspath(path_to_file)

        if not os.path.isfile(path_to_file):
            self.logger.error('No such file {}'.format(path_to_file))
            raise LookupError

        self.logger.info('Reading yaml file "{}"'.format(path_to_file))

        with open(path_to_file, 'r') as f:
            output = yaml.load(f, self.Loader)

        if not output:
            self.logger.error('File {} is empty'.format(path_to_file))
            raise ValueError

        return output


yaml_reader = YamlReader()


class ConfReader(ReadersMixin, LoggerMixin):
    def read(self, path_to_file):
        path_to_file = os.path.abspath(path_to_file)
        self.logger.info('Reading config file "{}"'.format(path_to_file))
        assert os.path.exists(path_to_file)
        parser = RawConfigParser(allow_no_value=True)
        parser.read(path_to_file)

        output = {
            section: {
                option: value

                for option, value in parser.items(section)}
            for section in parser.sections()}

        return output


conf_reader = ConfReader()


class ProplistReader(ReadersMixin, LoggerMixin):
    def read(self, path_to_file):
        path_to_file = os.path.abspath(path_to_file)
        assert os.path.exists(path_to_file)
        self.logger.info('Reading proplist file "{}"'.format(path_to_file))

        output = {}
        with open(path_to_file, 'rt') as f:
            for line in f:
                if line.startswith('#') or line.startswith('\n'):
                    continue
                k, v = line.split('=', 1)
                output[k.strip()] = v.strip()

        return output


proplist_reader = ProplistReader()


# --- validators ---

class JsonschemaValidator(ReadersMixin, LoggerMixin):
    def validate(self, doc, schema):
        try:
            jsonschema.validate(doc, schema)
        except:
            raise  # todo raise own types

    ValidationError = jsonschema.exceptions.ValidationError


jsonschema_validator = JsonschemaValidator()


# --- renderers ---

class YamlRenderer(ReadersMixin, LoggerMixin):
    def render(self, obj):
        return yaml.dump(obj, default_flow_style=False)


yaml_renderer = YamlRenderer()
