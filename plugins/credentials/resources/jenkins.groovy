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
import com.cloudbees.jenkins.plugins.sshcredentials.impl.*
import com.cloudbees.jenkins.plugins.sshcredentials.impl.*
import com.cloudbees.plugins.credentials.*
import com.cloudbees.plugins.credentials.*
import com.cloudbees.plugins.credentials.common.*
import com.cloudbees.plugins.credentials.domains.*
import com.cloudbees.plugins.credentials.domains.*
import com.cloudbees.plugins.credentials.impl.*
import com.cloudbees.plugins.credentials.impl.*
import hudson.model.User
import hudson.plugins.sshslaves.*
import jenkins.model.*

class Actions {
  Actions(out) { this.out = out }
  def out


  private credentialsForUser(String id, String username) {
    def matcher
    def availableCredentials =
      CredentialsProvider.lookupCredentials(
        StandardUsernameCredentials.class,
        Jenkins.getInstance(),
        hudson.security.ACL.SYSTEM,
        new SchemeRequirement("ssh")
      )
    if (id != "") {
      matcher = CredentialsMatchers.withId(id)
    } else {
      matcher = CredentialsMatchers.withUsername(username)
    }
    def matched = CredentialsMatchers.firstOrNull(
      availableCredentials,
      matcher
    )
    return matched
  }

  void updateCredentials(String scope,
                         String username,
                         String password="",
                         String description="",
                         String privateKey="",
                         String id="") {

    //removing '' quotes, jenkins cli bug workaround
    scope = scope.replaceAll('^\'|\'$', '')
    username = username.replaceAll('^\'|\'$', '')
    password = password.replaceAll('^\'|\'$', '')
    description = description.replaceAll('^\'|\'$', '')
    privateKey = privateKey.replaceAll('^\'|\'$', '')
    id = id.replaceAll('^\'|\'$', '')

    def globalDomain = Domain.global()
    def credentialsStore =
      Jenkins.instance.getExtensionList(
        'com.cloudbees.plugins.credentials.SystemCredentialsProvider'
      )[0].getStore()

    def credsScope
    if (scope == "global") {
      credsScope = CredentialsScope.GLOBAL
    } else if (scope == "system") {
      credsScope = CredentialsScope.SYSTEM
    }

    if (password == "") {
      User userId = User.get(username)
      password = userId.getProperty(jenkins.security.ApiTokenProperty.class).getApiToken()
    }

    def credentials
    if (privateKey == "") {
      credentials = new UsernamePasswordCredentialsImpl(
        credsScope,
        id,
        description,
        username,
        password
      )
    } else {
      def keySource
      if (privateKey.startsWith('-----BEGIN')) {
        keySource = new BasicSSHUserPrivateKey.DirectEntryPrivateKeySource(privateKey)
      } else if (privateKey.startsWith('from-jenkins-ssh-dir')) {
        keySource = new BasicSSHUserPrivateKey.UsersPrivateKeySource()
      } else {
        keySource = new BasicSSHUserPrivateKey.FileOnMasterPrivateKeySource(privateKey)
      }
      credentials = new BasicSSHUserPrivateKey(
        credsScope,
        id,
        username,
        keySource,
        password,
        description
      )
    }
    // Create or update the credentials in the Jenkins instance
    def existingCredentials = credentialsForUser(id, username)
    if(existingCredentials != null) {
      credentialsStore.updateCredentials(
        globalDomain,
        existingCredentials,
        credentials
      )
    } else {
      credentialsStore.addCredentials(globalDomain, credentials)
    }
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
