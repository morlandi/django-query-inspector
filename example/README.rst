
Install
=======

Create a virtualenv, then ...

Install Django dependencies:

.. code-block:: bash

    pip install -r requirements.txt

Initialize database tables:

.. code-block:: bash

    python manage.py migrate

Create a super-user for the admin:

.. code-block:: bash

    python manage.py createsuperuser

Optionally, load some sample data::

    gunzip -c backend/fixtures/backend.json.gz | python manage.py loaddata --format=json -

Run
===

.. code-block:: bash

    python manage.py runserver

Visit http://127.0.0.1:8000/
