pulp_puppet
===========


This is the ``pulp_puppet``  Plugin for `Pulp Project
3.0+ <https://pypi.org/project/pulpcore/>`__.

Community contributions are encouraged.

* Send us pull requests on `our GitHub repository <https://github.com/pulp/pulp_puppet>`_.
* View and file issues in the `Redmine Tracker
  <https://pulp.plan.io/projects/pulp_puppet/issues>`_.

All REST API examples below use `httpie <https://httpie.org/doc>`__ to
perform the requests.

This documentation makes use of the `jq library <https://stedolan.github.io/jq/>`_
to parse the json received from requests, in order to get the unique urls generated
when objects are created. To follow this documentation as-is please install the jq
library with:

``$ sudo dnf install jq``

Install ``pulpcore``
--------------------

Follow the `installation
instructions <docs.pulpproject.org/en/3.0/nightly/installation/instructions.html>`__
provided with pulpcore.

Install plugin
--------------

This document assumes that you have
`installed pulpcore <https://docs.pulpproject.org/en/3.0/nightly/installation/instructions.html>`_
into a the virtual environment ``pulpvenv``.

From Source
***********

.. code-block:: bash

   source /path/to/pulpvenv/bin/activate
   cd pulp_puppet
   pip install -e .

Make and Run Migrations
-----------------------

.. code-block:: bash

   pulp-manager makemigrations pulp_puppet
   pulp-manager migrate pulp_puppet

Run Services
------------

.. code-block:: bash

   pulp-manager runserver
   sudo systemctl restart pulp_resource_manager
   sudo systemctl restart pulp_worker@1
   sudo systemctl restart pulp_worker@2


Create a repository ``foo``
---------------------------

``$ http POST http://localhost:8000/api/v3/repositories/ name=foo``

``$ export REPO_HREF=$(http :8000/api/v3/repositories/ | jq -r '.results[] | select(.name == "foo") | ._href')``

Add an Importer to repository ``foo``
-------------------------------------

Add important details about your Importer and provide examples.

``$ http POST http://localhost:8000/api/v3/importers/puppet/ some=params repository=$REPO_HREF``

.. code:: json

    {
        "_href": "http://localhost:8000/api/v3/importers/puppet/$UUID/",
        ...
    }

``$ export IMPORTER_HREF=$(http :8000/api/v3/importers/puppet/ | jq -r '.results[] | select(.name == "bar") | ._href')``


Sync repository ``foo`` using Importer ``bar``
----------------------------------------------

Use ``puppet`` Importer:

``$ http POST $IMPORTER_HREF'sync/'``


Add a Publisher to repository ``foo``
-------------------------------------

``$ http POST http://localhost:8000/api/v3/publishers/puppet/ name=bar repository=$REPO_HREF``

.. code:: json

    {
        "_href": "http://localhost:8000/api/v3/publishers/puppet/$UUID/",
        ...
    }

``$ export PUBLISHER_HREF=$(http :8000/api/v3/publishers/puppet/ | jq -r '.results[] | select(.name == "bar") | ._href')``


Create a Publication using Publisher ``bar``
--------------------------------------------

``$ http POST http://localhost:8000/api/v3/publications/ publisher=$PUBLISHER_HREF``

.. code:: json

    [
        {
            "_href": "http://localhost:8000/api/v3/tasks/fd4cbecd-6c6a-4197-9cbe-4e45b0516309/",
            "task_id": "fd4cbecd-6c6a-4197-9cbe-4e45b0516309"
        }
    ]

``$ export PUBLICATION_HREF=$(http :8000/api/v3/publications/ | jq -r --arg PUBLISHER_HREF "$PUBLISHER_HREF" '.results[] | select(.publisher==$PUBLISHER_HREF) | ._href')``

Add a Distribution to Publisher ``bar``
---------------------------------------

``$ http POST http://localhost:8000/api/v3/distributions/ name='baz' publisher=$PUBLISHER_HREF publication=$PUBLICATION_HREF``


Check status of a task
----------------------

``$ http GET http://localhost:8000/api/v3/tasks/82e64412-47f8-4dd4-aa55-9de89a6c549b/``

Download ``foo.tar.gz`` from Pulp
---------------------------------

``$ http GET http://localhost:8000/content/foo/foo.tar.gz``
