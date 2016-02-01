/*
*  Copyright 2016 Mirantis, Inc.
*
*  Licensed under the Apache License, Version 2.0 (the "License"); you may
*  not use this file except in compliance with the License. You may obtain
*  a copy of the License at
*
*       http://www.apache.org/licenses/LICENSE-2.0
*
*  Unless required by applicable law or agreed to in writing, software
*  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
*  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
*  License for the specific language governing permissions and limitations
*  under the License.
*/

import hudson.plugins.gearman.GearmanPluginConfig

enable = args[0]
port = args[1]
host = args[2]


//removing '' quotes, jenkins cli bug workaround
host = host.replaceAll('^\'|\'$', '')
//getting gearman config
GearmanPluginConfig config = GearmanPluginConfig.get()
//setting gerrit configuration
config.enablePlugin = Boolean.parseBoolean(enable)
config.host = host
config.port = Integer.parseInt(port)
//saving config
config.save()
