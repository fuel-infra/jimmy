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

import com.sonyericsson.hudson.plugins.gerrit.trigger.config.Config
import com.sonyericsson.hudson.plugins.gerrit.trigger.GerritServer
import com.sonyericsson.hudson.plugins.gerrit.trigger.PluginImpl
import net.sf.json.JSONObject;
import net.sf.json.JSONSerializer;

hostname = args[0]
auth_key = args[1]
name = args[2]
url = args[3]
username = args[4]

//removing '' quotes, jenkins cli bug workaround
hostname = hostname.replaceAll('^\'|\'$', '')
auth_key = auth_key.replaceAll('^\'|\'$', '')
name = name.replaceAll('^\'|\'$', '')
url = url.replaceAll('^\'|\'$', '')
username = username.replaceAll('^\'|\'$', '')

Config config

if (PluginImpl.getInstance().getServer(name) == null) {
  GerritServer defaultServer = new GerritServer(name)
  config = defaultServer.getConfig()
  PluginImpl.getInstance().addServer(defaultServer)
  defaultServer.start()
} else {
  config = PluginImpl.getInstance().getServer(name).getConfig()
}

//buildCurrentPatchesOnly can be set only via JSON now
def buildOnlyCurrent = [buildCurrentPatchesOnly: [abortNewPatchsets: false, abortManualPatchsets: false]]
JSONObject currentPatchset = (JSONObject) JSONSerializer.toJSON(buildOnlyCurrent)

config.setValues(currentPatchset)
config.setGerritHostName(hostname)
config.setGerritFrontEndURL(url)
config.setGerritUserName(username)
config.setGerritAuthKeyFile(new File(auth_key))
PluginImpl.getInstance().save()
