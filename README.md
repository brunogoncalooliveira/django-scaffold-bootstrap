django-scaffold-bootstrap
=========================

**django-scaffold-bootstrap** is a time saver django app that scaffolds a
django model into CRUD operations using the bootstrap template.

**ATTENTION! This works by generating and changing code in your django app, so be carefull when you run this.**

When you scaffold a model, this is added:

 * html, js, css, ... to your ``app/static`` folder
 * one *model_list.html* and a *model_new.html* file for each model in ``app/templates/includes/`` folder
 * a base.html (bootstrap) template in ``app/templates/`` folder

 * templates/includes/* - to your ``app`` folder (contains a *_model_list.html* and *_model_new.html* for each model)
 * templatetags - ``app`` folder


And this is what is changed:

 * settings.py

  checks if exists and adds STATIC_URL and STATIC_ROOT variables if not present.
  Same for MESSAGE_TAGS, django_tables2 and widget_tweaks apps in INSTALLED_APPS.
  It also adds a logging.basicConfig logger.

 * project urls.py

  appends the urls.py of the app if not present

 * app urls.py

  generates "model_list/" url and "model_new" url to the app


 * app tables.py

  generates a Table class for each model, if not present

 * app views.py

  generates ``imports``, and one function ``ViewList`` and ``ViewNew`` for the model


When you execute this command, the scripts tries to download the sbadmin_data.zip from https://github.com/brunogoncalooliveira/django-scaffold-bootstrap. This zip contains all the bootstrap required files, css and js files.


Quick start
-----------

1. Add "scaffold-bootstrap" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = [
        ...
        'scaffold-bootstrap',
    ]

2. Run ``python manage.py --help`` to see if the command is installed::

    [scaffold-bootstrap]
       scaffold_model

3. Run ``python manage.py scaffold-bootstrap name_of_app name_of_model`` to scaffold your model.

4. point your urls.py to one url added (see yours urls.py) [optional]

5. Start the development server and visit http://127.0.0.1:8000/

6. Enjoy
