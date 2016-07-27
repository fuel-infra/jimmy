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

import hudson.model.Item
import hudson.model.Computer
import hudson.model.Hudson
import hudson.model.Run
import hudson.model.View
import jenkins.model.JenkinsLocationConfiguration
import jenkins.model.Jenkins
import hudson.markup.RawHtmlMarkupFormatter
import hudson.markup.EscapedMarkupFormatter
import hudson.security.GlobalMatrixAuthorizationStrategy
import hudson.security.AuthorizationStrategy
import hudson.security.Permission
import org.jenkinsci.plugins.UnsafeMarkupFormatter

class Actions {
  Actions(out) { this.out = out }
  def out

  void set_main_configuration(
    String admin_email=null,
    String markup_format=null,
    String num_of_executors=null,
    String scm_checkout_retry_count=null
    ) {
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
  }

  void create_update_user(String user, String email, String password=null, String name=null, String pub_keys=null) {

    //removing '' quotes, jenkins cli bug workaround
    email = email.replaceAll('^\'|\'$', '')
    name = name.replaceAll('^\'|\'$', '')
    pub_keys = pub_keys.replaceAll('^\'|\'$', '')

    def set_user = hudson.model.User.get(user)
    set_user.setFullName(name)
    def email_property = new hudson.tasks.Mailer.UserProperty(email)
    set_user.addProperty(email_property)
    def pw_details = hudson.security.HudsonPrivateSecurityRealm.Details.fromPlainPassword(password)
    set_user.addProperty(pw_details)
    if (pub_keys != null && pub_keys !="") {
      def ssh_keys_property = new org.jenkinsci.main.modules.cli.auth.ssh.UserPropertyImpl(pub_keys)
      set_user.addProperty(ssh_keys_property)
    }
    set_user.save()
  }

  void set_security_password(String user, String email, String password, String name=null, String pub_keys=null, String s2m_acl=null) {
    def instance = Jenkins.getInstance()
    def overwrite_permissions
    def strategy
    def realm
    strategy = new hudson.security.GlobalMatrixAuthorizationStrategy()
    if (!(instance.getAuthorizationStrategy() instanceof hudson.security.GlobalMatrixAuthorizationStrategy)) {
      overwrite_permissions = 'true'
    }
    create_update_user(user, email, password, name, pub_keys)
    for (Permission p : Item.PERMISSIONS.getPermissions()) {
      strategy.add(p,user)
    }
    for (Permission p : Computer.PERMISSIONS.getPermissions()) {
      strategy.add(p,user)
    }
    for (Permission p : Hudson.PERMISSIONS.getPermissions()) {
      strategy.add(p,user)
    }
    for (Permission p : Run.PERMISSIONS.getPermissions()) {
      strategy.add(p,user)
    }
    for (Permission p : View.PERMISSIONS.getPermissions()) {
      strategy.add(p,user)
    }
    realm = new hudson.security.HudsonPrivateSecurityRealm(false)
    // apply new strategy&realm
    if (overwrite_permissions == 'true') {
      instance.setAuthorizationStrategy(strategy)
      instance.setSecurityRealm(realm)
    }
    // commit new settings permanently (in config.xml)
    instance.save()
  }

  void set_unsecured() {
    def instance = Jenkins.getInstance()
    def strategy
    def realm
    strategy = new hudson.security.AuthorizationStrategy.Unsecured()
    realm = new hudson.security.HudsonPrivateSecurityRealm(false, false, null)
    instance.setAuthorizationStrategy(strategy)
    instance.setSecurityRealm(realm)
    instance.save()
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
