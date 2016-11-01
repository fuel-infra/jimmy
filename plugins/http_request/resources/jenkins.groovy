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
import jenkins.plugins.http_request.auth.BasicDigestAuthentication

class Actions {
  Actions(out) { this.out = out }
  def out

  void setBasicDigestAuth(String keyName,
                          String userName,
                          String password) {

    // get http requests settings descriptor and current BasicDigestAuthentication list
    def inst = Jenkins.getInstance()
    def descr = inst.getDescriptor("jenkins.plugins.http_request.HttpRequestGlobalConfig")

    List basicDigestAuths = descr.getBasicDigestAuthentications() ?: []

    BasicDigestAuthentication authConfig = new BasicDigestAuthentication(keyName, userName, password)

    // replace or add basic auth configuration
    for (BasicDigestAuthentication config : basicDigestAuths) {
      if (config.getKeyName() == keyName) {
        basicDigestAuths = basicDigestAuths.minus(config)
      }
    }

    basicDigestAuths = basicDigestAuths.plus(authConfig)

    // save auth list and global settings
    descr.setBasicDigestAuthentications(basicDigestAuths)
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
