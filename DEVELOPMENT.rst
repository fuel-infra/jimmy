Jimmy is a command line tool for managing jenkins configuration through the simple
descriptions in YAML format.


Repo Structure
==============

``jimmy.py``

  Main executable script.

``jimmy.yaml``

  Main configuration file containing parameters and steps to invoke.

``requirements.txt``

  Python requirements to run Jimmy.

``sample/input/jenkins.yaml``

  Jenkins YAML description file.

``sample/input/secrets``

  Directory containing secret data.

``lib/``

  Directory containing libs for loggers, schema readers, validators.

``plugins/plugin-name/``

  Each plugin is python module or package. Jimmy itself is just a runner which performs some pipelines
  specified by jimmy configuration and script parameters. Every other functionality is implemented as
  plugins (which may come with distribution or be added by end-user). For example, ``plugins/gearman/``
  package corresponds to Jenkins Gearman plugin configuration.

``plugins/plugin-name/resources``

  Such directory may contain schemas for validation, groovy scripts or other kind of resources required
  for plugin functionality.


How Jimmy works
=============

Jimmy is a runner which reads and then builds pipeline defined in main configuration file. Main configuration
file jimmy.yaml consists of:
- pipelines and steps to perform
- params or injected data for each step

Jimmy Runner looks for plugins(modules) and loads them. Then invokes these modules(plugins) for each pipeline step
defined in jimmy.yaml. The next steps included in jimmy.yaml:

  - read_source: Read source yaml file with Jenkins configuration
  - build_source: Build and post-process the initial configuration
  - validate_source: Perform validation of post-processed document against jsonschemas or amother kind of checks
  - update_dest: Update jenkins configuration by calling jenkins cli and executing groovy scripts

You can see updated configuration after the all steps are successfully completed.


Plugin description
==================
The Plugin is a base class which gives possibility to easily add other python modules or packages.
This Plugin contain default relative paths to resources for other modules and methods to read source schemas and
validate YAML configuration for this plugin. To write such Plugin you have to add some step in jimmy.yaml
configuration file and then create a method with such name as step name under the Plugin class. And then you can
invoke this Plugin.
Example:

Pipeline step defined in jimmy.yaml:

.. code-block:: yaml

    - name: validate_source
      description: |
        Perform validation of post-processed document against
        jsonschemas or amother kind of checks

      inject:
        source: results.build_source.source

Method definition in Plugin class:

.. code-block:: python

    def validate_source(self, source, **k):
        subtree = self._tree_read(source, self.source_tree_path)
        self.jsonschema_validator.validate(subtree, self.schema)
        return {}

In this example if the validation fails, the method returns an error.


Plugin should return dict with unique keys (if they aren't unique, jimmy will error about it). This dict could be used in further
steps by injecting merged dict of all returned values from all plugins.

Example:

Pipeline steps:

.. code-block:: yaml

  - name: first_step
    description: first step definition
    ...

  - name: second_step
    description: second step definition
    inject:
      my_val: results.first_step.my_val
      my_step_results: results.first_step


Plugin method example:

.. code-block:: python

  def first_step():
      return {'my_val': 1}


How to write your own groovy-based plugin
=========================================

Each plugin is python module or package which may came with distribution or be added by end-user.
To create your own plugin you need:

1) Create new directory for plugin in plugins/plugin-name
2) Create resources with schema and groovy script for this plugin:
   - Schema should describe parameters corresponded to this configuration.
   - Groovy script must update configuration related to this plugin.

3) Create subclass of groovy plugin in plugins/plugin-name/impl.py and define method update_dest which will read
data from source tree and then use subproccess to call jenkins cli and execute groovy script with arguments from source data.


Installation
============

1) Setup venv:

.. code-block:: bash

  $ sudo pip install virtualenv
  $ cd work_folder && virtualenv venv
  $ source venv/bin/activate

2) Clone Jimmy repo:

.. code-block:: bash

  $ git clone https://review.fuel-infra.org/fuel-infra/jimmy
  $ cd jimmy

3) Install the required python packages using pip

.. code-block:: bash

  $ pip install -r requirements.txt


Configuration file
==================

After installation, you will need to specify jenkins_url and path to jenkins_cli in main configuration
file jimmy.yaml located in the root of jimmy directory.

Configure path to Jenkins CLI:

.. code-block:: yaml

  defaults:
    inject:
      jenkins_cli_path: /var/cache/jenkins/war/WEB-INF/jenkins-cli.jar

Configure Jenkins URL:

.. code-block:: yaml

  envs:
    main:
      jenkins_url: http://localhost:8080


Running and Updating configuration
==================================

After it’s installed, you can invoke Jimmy by running 'python jimmy.py'. Make sure that that you have
a configured YAML definition of jenkins configuration and the user you are running from has permissions
at Jenkins. Check that ssh keys configured properly(to establish connection with Jenkins via ssh keys).


Jenkins Configuration Definitions
=================================

Jenkins configuration is specified as yaml file(jenkins.yaml). Then Jimmy use it to update this configuration on jenkins.
The example of defined jenkins configuration in a yaml file:

.. code-block:: yaml

  jenkins:
    gearman:
      enable: true
      host: zuul01-test.infra.mirantis.net
      port: 4730

    gerrit:
      servers:
      - name: test-gerrit-name
        hostname: test-hostname
        username: test-username
        url: http://test.com
        auth_key: /var/lib/jenkins/.ssh/id_rsa
      - name: test-gerrit-name2
        hostname: test-hostname2
        username: test-username2
        url: http://test.com2
        auth_key: /var/lib/jenkins/.ssh/id_rsa


Importing and merging data in yaml definitions
==============================================

It is also possible to import and merge data in yaml from config files or other YAML definitions.
Example of config file(sample/input/secret/admin.cfg):

.. code-block:: ini

  [secret_1]
  username = admin
  password = 1q2w3e
  keyfile = admin.key

Example of text file(sample/input/secret/admin.key):

.. code-block::

  -----BEGIN RSA PRIVATE KEY-----
  ..some data...
  -----END RSA PRIVATE KEY-----


Then in yaml definitions you can import or merge data from different configs and yamls.
Importing data from cfg(admin.cfg):

.. code-block:: yaml

  gerrit:
    servers:
    - name: test-gerrit-name
      hostname: test-hostname
      username: !import-from-cfg:
        sample/input/secret/admin.cfg:secret_1:username
      url: http://test.com
      private_key: !import-from-cfg:
        sample/input/secret/admin.cfg:secret_1:keyfile


You can import key(admin.key) directly:

.. code-block:: yaml

  gerrit:
    servers:
    - hostname: test-hostname
      private_key: !include-relative-text:
        sample/input/secret/admin.key


Merge configs and yamls:

.. code-block:: yaml

  gerrit:
    servers:
        !merge:
          - !include-yaml:  jimmy-configs/includes/gerrit-trigger.yaml
          - !include-conf:  sample/input/admin.cfg


Include other yamls:

.. code-block:: yaml

  gerrit:
    servers:
      include:
          !include-relative-yaml:
            ./include.yaml
