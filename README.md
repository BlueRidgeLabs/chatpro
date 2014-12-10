ChatPro
=======

Dashboard for managing "Group Chat" applications hosted in [RapidPro](http://rapidpro.io)

Built for UNICEF by Nyaruka - http://nyaruka.com

Getting Started
================

Install dependencies
```
% virtualenv env
% source env/bin/activate
% pip install -r pip-requires.txt
```

Link up a settings file (you'll need to create the postgres db first, username: 'chat' password: 'nyaruka')
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
