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

import logging

import click

from lib.common import LOG_LEVELS
from lib.common import LOG_LEVELS_NAMES_LOWER
from lib.core import Runner

logger = logging.getLogger()


@click.command()
@click.option(
    '-l', '--log-level',
    default='debug',
    type=click.Choice(LOG_LEVELS_NAMES_LOWER))
@click.option(
    '-c', '--conf-path',
    default='jimmy.yaml',
    type=click.Path(exists=True))
@click.option(
    '-e', '--env-name',
    default='main',
    type=click.STRING)
@click.argument(
    'pipeline_name',
    default='main',
    type=click.STRING)
def cli(log_level, conf_path, env_name, pipeline_name):
    logging.basicConfig()
    logger.setLevel(LOG_LEVELS[log_level.upper()])
    Runner(conf_path, pipeline_name, env_name).run()


if __name__ == '__main__':
    cli()
