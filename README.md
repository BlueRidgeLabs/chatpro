ChatPro
=======

Dashboard for managing "Group Chat" applications hosted in [RapidPro](http://rapidpro.io)

Built for UNICEF by [Nyaruka](http://nyaruka.com)

Setting Up a Development Environment
------------------------------------

Install dependencies

```
% virtualenv env
% source env/bin/activate
% pip install -r pip-requires.txt
```

Create the database

 * name: _chat_
 * username: _chat_
 * password: _nyaruka_

Link up a settings file

```
% ln -s chatpro/settings.py.postgres chatpro/settings.py
```

Sync the database, add all our models and create our superuser

```
% python manage.py syncdb
% python manage.py migrate
% python manage.py createsuperuser
```

At this point everything should be good to go, you can start with:

```
% python manage.py runserver
```

To run background tasks, you'll also need to start celery and have a local redis server:

```
% celery -A chatpro worker -l info
```