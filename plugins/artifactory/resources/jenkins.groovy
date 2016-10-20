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
import net.sf.json.JSONObject;
import net.sf.json.JSONSerializer;

class Actions {
  Actions(out) { this.out = out }
  def out

  void setGlobalConfig(
    String proxyPort=null
  ) {

    def inst = Jenkins.getInstance()
    def descr = inst.getDescriptor("org.jfrog.hudson.ArtifactoryBuilder")

    // enable credentials plugin usage
    descr.setUseCredentialsPlugin(true)

    // set build-info proxy settings
    def proxy = [ buildInfoProxyEnabled : true,
                  buildInfoProxyPort : proxyPort ]
    JSONObject proxyConfig = (JSONObject) JSONSerializer.toJSON(proxy)
    descr.configureProxy(proxyConfig)
    descr.initDefaultCertPaths()

    // commit setings
    descr.save()
    inst.save()
  }

  void setServerConfig(
    String serverId,
    String artifactoryUrl,
    String deployerCredentialsId,
    String resolverCredentialsId=null,
    String timeout=null,
    String bypassProxy=null
  ) {

    // create CredentialsConfig objects for deployer and resolver
    CredentialsConfig deployerCredentialsConfig = new CredentialsConfig(
      null, null, deployerCredentialsId, false
    )

    CredentialsConfig resolverCredentialsConfig

    if (resolverCredentialsId != null && resolverCredentialsId !="") {
      resolverCredentialsConfig = new CredentialsConfig(
        null, null, resolverCredentialsId, true
      )
    } else {
      resolverCredentialsConfig = deployerCredentialsConfig
    }

    // create ArtifactoryServer configuration
    ArtifactoryServer serverConfig = new ArtifactoryServer(
      serverId,
      artifactoryUrl,
      deployerCredentialsConfig,
      resolverCredentialsConfig,
      timeout.toInteger(),
      bypassProxy.toBoolean()
    )

    def inst = Jenkins.getInstance()
    def descr = inst.getDescriptor("org.jfrog.hudson.ArtifactoryBuilder")
    def servers = descr.getArtifactoryServers() ?: []

    for (ArtifactoryServer server : servers) {
      if (server.getName() == serverId) {
        servers = servers.minus(server)
      }
    }

    servers = servers.plus(serverConfig)

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
