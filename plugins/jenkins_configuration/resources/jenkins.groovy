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

import jenkins.model.JenkinsLocationConfiguration
import jenkins.model.Jenkins
import hudson.markup.RawHtmlMarkupFormatter
import hudson.markup.EscapedMarkupFormatter
import org.jenkinsci.plugins.UnsafeMarkupFormatter


class Actions {
  Actions(out) { this.out = out }
  def out

  void setAdminEmail(
    String adminEmail
  ) {

    adminEmail = adminEmail.replaceAll('^\'|\'$', '')

    def loc = JenkinsLocationConfiguration.get()
    loc.setAdminAddress(adminEmail)
    loc.save()
  }

  void setAgentTcpPort(
    String agentTcpPort
  ) {

    Jenkins jenkins = Jenkins.getInstance()

    if (jenkins.getSlaveAgentPort() != Integer.parseInt(agentTcpPort)) {
      jenkins.setSlaveAgentPort(Integer.parseInt(agentTcpPort))
    }

    jenkins.save()
  }

  void setLocationUrl(
    String locationUrl
  ) {

    locationUrl = locationUrl.replaceAll('^\'|\'$', '')

    def loc = JenkinsLocationConfiguration.get()
    loc.setUrl(locationUrl)
    loc.save()
  }

  void setMarkupFormatter(
    String markupFormatter
  ) {

    Jenkins jenkins = Jenkins.getInstance()
    if (markupFormatter == "raw-html") {
      jenkins.setMarkupFormatter(new RawHtmlMarkupFormatter(false))
    } else if (markupFormatter == "plain-text") {
      jenkins.setMarkupFormatter(new EscapedMarkupFormatter())
    } else if (markupFormatter == "unsafe") {
      jenkins.setMarkupFormatter(new UnsafeMarkupFormatter())
    }

    jenkins.save()
  }

  void setNumExecutors(
    String numOfExecutors
  ) {

    Jenkins jenkins = Jenkins.getInstance()

    if (jenkins.getNumExecutors() != Integer.parseInt(numOfExecutors)) {
      jenkins.setNumExecutors(Integer.parseInt(numOfExecutors))
    }

    jenkins.save()
  }

  void setScmCheckoutRetryCount(
    String scmCheckoutRetryCound
  ) {

    Jenkins jenkins = Jenkins.getInstance()

    if (jenkins.getScmCheckoutRetryCount() != Integer.parseInt(scmCheckoutRetryCound)) {
      jenkins.setScmCheckoutRetryCount(Integer.parseInt(scmCheckoutRetryCound))
    }

    jenkins.save()
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
