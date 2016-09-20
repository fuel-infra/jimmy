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

import jenkins.model.Jenkins
import org.jfrog.hudson.ArtifactoryServer
import org.jfrog.hudson.CredentialsConfig

class Actions {
  Actions(out) { this.out = out }
  def out

  void set_artifactory_config(
    String server_id,
    String artifactory_url,
    String deployer_credentials_id,
    String resolver_credentials_id=null,
    String timeout=null,
    String bypass_proxy=null
  ) {

    CredentialsConfig deployer_credentials_config = new CredentialsConfig(
      null, null, deployer_credentials_id, false
    )

    CredentialsConfig resolver_credentials_config

    if (resolver_credentials_id != null && resolver_credentials_id !="") {
      resolver_credentials_config = new CredentialsConfig(
        null, null, resolver_credentials_id, true
      )
    } else {
      resolver_credentials_config = deployer_credentials_config
    }

    ArtifactoryServer server_config = new ArtifactoryServer(
      server_id,
      artifactory_url,
      deployer_credentials_config,
      resolver_credentials_config,
      timeout.toInteger(),
      bypass_proxy.toBoolean()
    )

    def servers = [server_config]


    def inst = Jenkins.getInstance()
    def descr = inst.getDescriptor("org.jfrog.hudson.ArtifactoryBuilder")

    descr.setUseCredentialsPlugin(true)
    descr.setArtifactoryServers(servers)
    // commit setings
    descr.save()
    inst.save()
  }
}

///////////////////////////////////////////////////////////////////////////////
// CLI Argument Processing
///////////////////////////////////////////////////////////////////////////////

actions = new Actions(out)
action = args[0]
if (args.length < 2) {
  actions."$action"()
} else {
  actions."$action"(*args[1..-1])
}
