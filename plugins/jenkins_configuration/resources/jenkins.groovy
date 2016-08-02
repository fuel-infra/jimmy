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


admin_email = args[0]
markup_format = args[1]
num_of_executors = args[2]
scm_checkout_retry_count = args[3]

// removing '', jenkins cli bug workaround
admin_email = admin_email.replaceAll('^\'|\'$', '')
//setting system admin email
def loc = JenkinsLocationConfiguration.get()
loc.setAdminAddress(admin_email)
loc.save()

//setting markup formatter
Jenkins jenkins = Jenkins.getInstance()
if (markup_format == "raw-html") {
  jenkins.setMarkupFormatter(new RawHtmlMarkupFormatter(false))
} else if (markup_format == "plain-text") {
  jenkins.setMarkupFormatter(new EscapedMarkupFormatter())
} else if (markup_format == "unsafe") {
  jenkins.setMarkupFormatter(new UnsafeMarkupFormatter())
}
//setting number of executors for master node
if (jenkins.getNumExecutors() != Integer.parseInt(num_of_executors)) {
  jenkins.setNumExecutors(Integer.parseInt(num_of_executors))
}
//setting scm checkout retry count
if (jenkins.getScmCheckoutRetryCount() != Integer.parseInt(scm_checkout_retry_count)) {
  jenkins.setScmCheckoutRetryCount(Integer.parseInt(scm_checkout_retry_count))
}
jenkins.save()
