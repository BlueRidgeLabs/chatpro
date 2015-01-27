#ChatPro

Dashboard for managing "Group Chat" applications hosted in [RapidPro](http://rapidpro.io)

Built for UNICEF by [Nyaruka](http://nyaruka.com).

##Development Setup

Install dependencies

```
% virtualenv env
% source env/bin/activate
% pip install -r pip-requires.txt
```

Create the database

 * name: _chatpro_
 * username: _chatpro_
 * password: _nyaruka_

Link up a settings file

```
% ln -s chatpro/settings.py.postgres chatpro/settings.py
```

Sync the database, add all our models and create our superuser

```
% python manage.py syncdb
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

###Running Tests

```
% coverage run --source="." manage.py test --verbosity=2 --noinput
% coverage report -m --include="chatpro/*" --omit="*/migrations/*,*/tests.py"
```

##RapidPro Integration

To notify ChatPro when a new chat message has been received, add the following webhook to your group chat flow:

 * URL: _/api/v1/message/new/_
 * Method: _POST_
 * Query parameters:
     * contact: the UUID of the contact that received the message
     * text: the text of the message
     * group: the UUID of the contact group that the message was routed to
     * token: your organization's ChatPro secret token
 
For example:

```
http://chat.rapidpro.io/api/v1/message/new/?contact=@contact.uuid&text=@step.value&group=bef530c4-5d84-4c1e-ad82-7a563866446c&token=1234567890
```

To notify ChatPro when a new chat contact has been registered, add the following webhook to your registration flow:

 * URL: _/api/v1/contact/new/_
 * Method: _POST_
 * Query parameters:
     * contact: the UUID of the contact that received the message
     * group: the UUID of the contact group that contact has joined
     * token: your organization's ChatPro secret token
 
For example:

```
http://chat.rapidpro.io/api/v1/contact/new/?contact=@contact.uuid&group=bef530c4-5d84-4c1e-ad82-7a563866446c&token=1234567890
```

To notify ChatPro when a contact has left group chat

 * URL: _/api/v1/contact/del/_
 * Method: _POST_
 * Query parameters:
     * contact: the UUID of the contact that received the message
     * token: your organization's ChatPro secret token
 
For example:

```
http://chat.rapidpro.io/api/v1/message/new/?contact=@contact.uuid&token=1234567890
```
