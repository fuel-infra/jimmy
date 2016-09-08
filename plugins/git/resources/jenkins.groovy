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

git_email = args[0]
git_name = args[1]

// removing '', jenkins cli bug workaround
git_email = git_email.replaceAll('^\'|\'$', '')
git_name = git_name.replaceAll('^\'|\'$', '')

// get Jenkins instance
def inst = Jenkins.getInstance()

// get git plugin descriptor
def descr = inst.getDescriptor("hudson.plugins.git.GitSCM")

// set git email and name
descr.setGlobalConfigEmail(git_email)
descr.setGlobalConfigName(git_name)

// save changes
descr.save()
