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
import hudson.plugins.throttleconcurrents.ThrottleJobProperty

class Actions {
  Actions(out) { this.out = out }
  def out


  void clear_categories() {
    ThrottleJobProperty.DescriptorImpl descriptor = Jenkins.getInstance().getDescriptorByType(ThrottleJobProperty.DescriptorImpl.class)
    def categories = descriptor.getCategories()
    categories.clear()
    descriptor.save()
  }

  void create_throttle_category(
    String categoryName,
    String maxTotConcBuilds=null,
    String maxTotConcPerNode=null,
    String throttleNodeLabel=null,
    String maxTotConcPerNodeLabeled=null
  ) {
    List throttleNodeLabelLst
    List maxTotConcPerNodeLabeledLst
    def nodeLabeledPairs
    //getting descriptor
    ThrottleJobProperty.DescriptorImpl descriptor = Jenkins.getInstance().getDescriptorByType(ThrottleJobProperty.DescriptorImpl.class)
    //getting categories
    def categories = descriptor.getCategories()
    //creating category
    def category = new ThrottleJobProperty.ThrottleCategory(categoryName, Integer.parseInt(maxTotConcPerNode), Integer.parseInt(maxTotConcBuilds), null); 

    if (throttleNodeLabel != '' && maxTotConcPerNodeLabeled != '') {
      throttleNodeLabelLst = throttleNodeLabel.split(',')
      maxTotConcPerNodeLabeledLst = maxTotConcPerNodeLabeled.split(',')
      if (throttleNodeLabelLst.size() == maxTotConcPerNodeLabeledLst.size()) {
        for (int i = 0; i < throttleNodeLabelLst.size(); i++) {
          nodeLabeledPairs = category.getNodeLabeledPairs()
          nodeLabeledPairs.add(new ThrottleJobProperty.NodeLabeledPair(throttleNodeLabelLst.get(i), Integer.parseInt(maxTotConcPerNodeLabeledLst.get(i))))
        }
      } else {
          throw new Exception("the number of values in throttled_node_label doesn't match with values in max_conc_per_labeled")
      }
    }
    categories.add(category)
    descriptor.save()
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
