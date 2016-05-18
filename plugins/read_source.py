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

from lib.api import Plugin


class MainPlugin(Plugin):

    def __init__(self):
        self.skip = False

    def read_source(self, path, **kwargs):
        return {
            'source': self.yaml_reader.read(path)
        }

    def build_source(self, source, **k):
        return {
            'source': source
        }
