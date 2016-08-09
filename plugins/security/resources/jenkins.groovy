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
import hudson.security.GlobalMatrixAuthorizationStrategy
import hudson.security.AuthorizationStrategy
import hudson.security.Permission
import jenkins.model.Jenkins
import com.cloudbees.plugins.credentials.CredentialsProvider
import com.cloudbees.plugins.credentials.common.StandardUsernameCredentials
import com.cloudbees.plugins.credentials.domains.SchemeRequirement
import com.cloudbees.plugins.credentials.impl.UsernamePasswordCredentialsImpl
import com.sonyericsson.hudson.plugins.gerrit.trigger.PluginImpl
import hudson.scm.SCM


class Actions {
  Actions(out) { this.out = out }
  def out

  // Creates or updates user
  //
  void create_update_user(String user, String email=null, String passwd=null, String name=null, String pub_keys=null) {
    def set_user = hudson.model.User.get(user)
    if (name != null && name !="") {
      set_user.setFullName(name)
    }
    if (email != null && email !="") {
      def email_property = new hudson.tasks.Mailer.UserProperty(email)
      set_user.addProperty(email_property)
    }
    if (passwd != null && passwd !="") {
      def pw_details = hudson.security.HudsonPrivateSecurityRealm.Details.fromPlainPassword(passwd)
      set_user.addProperty(pw_details)
    }
    if (pub_keys != null && pub_keys !="") {
      def ssh_keys_property = new org.jenkinsci.main.modules.cli.auth.ssh.UserPropertyImpl(pub_keys)
      set_user.addProperty(ssh_keys_property)
    }
    set_user.save()
  }

  // Sets up security for the Jenkins Master instance.
  //
  void set_security_ldap(
    String server=null,
    String rootDN=null,
    String userSearch=null,
    String inhibitInferRootDN=null,
    String userSearchBase=null,
    String groupSearchBase=null,
    String managerDN=null,
    String managerPassword=null,
    String ldapuser,
    String pub_keys=null,
    String email="",
    String password="",
    String name=""
  ) {

    if (inhibitInferRootDN==null) {
      inhibitInferRootDN = false
    }
    def instance = Jenkins.getInstance()
    def strategy
    def realm
    strategy = new hudson.security.GlobalMatrixAuthorizationStrategy()
    create_update_user(ldapuser, email, password, name, pub_keys)

    for (Permission p : Item.PERMISSIONS.getPermissions()) {
      strategy.add(p,ldapuser)
    }
    for (Permission p : Computer.PERMISSIONS.getPermissions()) {
      strategy.add(p,ldapuser)
    }
    for (Permission p : Hudson.PERMISSIONS.getPermissions()) {
      strategy.add(p,ldapuser)
    }
    for (Permission p : Run.PERMISSIONS.getPermissions()) {
      strategy.add(p,ldapuser)
    }
    for (Permission p : View.PERMISSIONS.getPermissions()) {
      strategy.add(p,ldapuser)
    }
     for (Permission p : CredentialsProvider.GROUP.getPermissions()) {
      strategy.add(p,ldapuser)
    }
    for (Permission p : PluginImpl.PERMISSION_GROUP.getPermissions()) {
      strategy.add(p,ldapuser)
    }
    for (Permission p : SCM.PERMISSIONS.getPermissions()) {
      strategy.add(p,ldapuser)
    }
    realm = new hudson.security.LDAPSecurityRealm(
      server, rootDN, userSearchBase, userSearch, groupSearchBase, managerDN, managerPassword, inhibitInferRootDN.toBoolean()
    )
    // apply new strategy&realm
    instance.setAuthorizationStrategy(strategy)
    instance.setSecurityRealm(realm)
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

  void set_security_password(String user, String pub_keys=null, String password=null, String email=null, String name=null) {
    def instance = Jenkins.getInstance()
    def overwrite_permissions
    def strategy
    def realm
    strategy = new hudson.security.GlobalMatrixAuthorizationStrategy()

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
    for (Permission p : CredentialsProvider.GROUP.getPermissions()) {
      strategy.add(p,user)
    }
    for (Permission p : PluginImpl.PERMISSION_GROUP.getPermissions()) {
      strategy.add(p,user)
    }
    for (Permission p : SCM.PERMISSIONS.getPermissions()) {
      strategy.add(p,user)
    }
    if (instance.getSecurityRealm() instanceof hudson.security.HudsonPrivateSecurityRealm) {
      realm = instance.getSecurityRealm()
    } else {
      realm = new hudson.security.HudsonPrivateSecurityRealm(false)
    }
    // apply new strategy&realm
    instance.setAuthorizationStrategy(strategy)
    instance.setSecurityRealm(realm)
    // commit new settings permanently (in config.xml)
    instance.save()
  }

  void set_permissions_matrix(
    String user,
    String permissions,
    String email=null,
    String password=null,
    String name=null,
    String pub_keys=null,
    String security_model
  ) {
    def instance = Jenkins.getInstance()
    def strategy
    strategy = instance.getAuthorizationStrategy()
    List perms = permissions.split(',')

    if (security_model == 'password') {
      create_update_user(user, email, password, name, pub_keys)
    }

    if (perms.contains("job")) {
      for (Permission p : Item.PERMISSIONS.getPermissions()) {
        strategy.add(p,user)
      }
    }
    if (perms.contains("view")) {
      for (Permission p : View.PERMISSIONS.getPermissions()) {
        strategy.add(p,user)
      }
    }
    if (perms.contains("slave")) {
      for (Permission p : Computer.PERMISSIONS.getPermissions()) {
        strategy.add(p,user)
      }
    }
    if (perms.contains("overall")) {
      for (Permission p : Hudson.PERMISSIONS.getPermissions()) {
        strategy.add(p,user)
      }
    }
    if (perms.contains("run")) {
      for (Permission p : Run.PERMISSIONS.getPermissions()) {
        strategy.add(p,user)
      }
    }
    if (perms.contains("credentials")) {
        for (Permission p : CredentialsProvider.GROUP.getPermissions()) {
        strategy.add(p,user)
      }
    }
    if (perms.contains("gerrit")) {
      for (Permission p : PluginImpl.PERMISSION_GROUP.getPermissions()) {
        strategy.add(p,user)
      }
    }
    if (perms.contains("scm")) {
      for (Permission p : SCM.PERMISSIONS.getPermissions()) {
        strategy.add(p,user)
      }
    }
    instance.setAuthorizationStrategy(strategy)
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

