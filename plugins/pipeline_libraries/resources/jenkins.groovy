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
import hudson.plugins.git.GitSCM
import hudson.plugins.git.BranchSpec
import hudson.plugins.git.SubmoduleConfig
import hudson.plugins.git.extensions.GitSCMExtension
import org.jenkinsci.plugins.workflow.libs.LibraryConfiguration
import org.jenkinsci.plugins.workflow.libs.GlobalLibraries
import org.jenkinsci.plugins.workflow.libs.SCMRetriever

class Actions {
  Actions(out) { this.out = out }
  def out

  void set_global_library(String name,
                          String url,
                          String branch,
                          String defaultVersion,
                          String implicit,
                          String versionOverride) {

    // create SCM object using provided url and branch variables
    def libraryGit = new GitSCM(GitSCM.createRepoList(url, null),
                                Collections.singletonList(new BranchSpec("*/" + branch)),
                                false,
                                Collections.<SubmoduleConfig>emptyList(),
                                null,
                                null,
                                Collections.<GitSCMExtension>emptyList())

    // create library configuration
    def libraryRetriever = new SCMRetriever(libraryGit)
    def libraryConfig = new LibraryConfiguration(name, libraryRetriever)

    // set additional parameters
    libraryConfig.setAllowVersionOverride(versionOverride.toBoolean())
    libraryConfig.setDefaultVersion(defaultVersion)
    libraryConfig.setImplicit(implicit.toBoolean())

    // get global libraries setting descriptor and current libraries list
    def inst = Jenkins.getInstance()
    def descr = inst.getDescriptor("org.jenkinsci.plugins.workflow.libs.GlobalLibraries")

    List libraries = descr.getLibraries()

    // replace or add library configuration
    for (LibraryConfiguration config : libraries) {
      if (config.getName() == name) {
        libraries = libraries.minus(config)
      }
    }

    libraries = libraries.plus(libraryConfig)

    // save libraries list and global settings
    descr.setLibraries(libraries)
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
