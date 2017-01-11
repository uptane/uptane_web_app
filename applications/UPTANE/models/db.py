# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# This scaffolding model makes your app work on Google App Engine too
# File is released under public domain and you can use without limitations
# -------------------------------------------------------------------------

if request.global_settings.web2py_version < "2.14.1":
    raise HTTP(500, "Requires web2py 2.13.3 or newer")

# -------------------------------------------------------------------------
# if SSL/HTTPS is properly configured and you want all HTTP requests to
# be redirected to HTTPS, uncomment the line below:
# -------------------------------------------------------------------------
# request.requires_https()

# -------------------------------------------------------------------------
# app configuration made easy. Look inside private/appconfig.ini
# -------------------------------------------------------------------------
from gluon.contrib.appconfig import AppConfig

# -------------------------------------------------------------------------
# once in production, remove reload=True to gain full speed
# -------------------------------------------------------------------------
myconf = AppConfig(reload=True)

if not request.env.web2py_runtime_gae:
    # ---------------------------------------------------------------------
    # if NOT running on Google App Engine use SQLite or other DB
    # ---------------------------------------------------------------------
    db = DAL(myconf.get('db.uri'),
             pool_size=myconf.get('db.pool_size'),
             migrate_enabled=myconf.get('db.migrate'),
             check_reserved=['all'])#,
             #fake_migrate_all=True)
else:
    # ---------------------------------------------------------------------
    # connect to Google BigTable (optional 'google:datastore://namespace')
    # ---------------------------------------------------------------------
    db = DAL('google:datastore+ndb')
    # ---------------------------------------------------------------------
    # store sessions and tickets there
    # ---------------------------------------------------------------------
    session.connect(request, response, db=db)
    # ---------------------------------------------------------------------
    # or store session in Memcache, Redis, etc.
    # from gluon.contrib.memdb import MEMDB
    # from google.appengine.api.memcache import Client
    # session.connect(request, response, db = MEMDB(Client()))
    # ---------------------------------------------------------------------

# -------------------------------------------------------------------------
# by default give a view/generic.extension to all actions from localhost
# none otherwise. a pattern can be 'controller/function.extension'
# -------------------------------------------------------------------------
response.generic_patterns = ['*'] if request.is_local else []
# -------------------------------------------------------------------------
# choose a style for forms
# -------------------------------------------------------------------------
response.formstyle = myconf.get('forms.formstyle')  # or 'bootstrap3_stacked' or 'bootstrap2' or other
response.form_label_separator = myconf.get('forms.separator') or ''

# -------------------------------------------------------------------------
# (optional) optimize handling of static files
# -------------------------------------------------------------------------
# response.optimize_css = 'concat,minify,inline'
# response.optimize_js = 'concat,minify,inline'

# -------------------------------------------------------------------------
# (optional) static assets folder versioning
# -------------------------------------------------------------------------
# response.static_version = '0.0.0'

# -------------------------------------------------------------------------
# Here is sample code if you need for
# - email capabilities
# - authentication (registration, login, logout, ... )
# - authorization (role based authorization)
# - services (xml, csv, json, xmlrpc, jsonrpc, amf, rss)
# - old style crud actions
# (more options discussed in gluon/tools.py)
# -------------------------------------------------------------------------

from gluon.tools import Auth, Service, PluginManager

# host names must be a list of allowed host names (glob syntax allowed)
auth = Auth(db, host_names=myconf.get('host.names'), secure=True)
service = Service()
plugins = PluginManager()

# -------------------------------------------------------------------------
# create all tables needed by auth if not custom tables
# -------------------------------------------------------------------------
auth.define_tables(username=True, signature=True)

# -------------------------------------------------------------------------
# configure email
# -------------------------------------------------------------------------
mail = auth.settings.mailer
mail.settings.server = 'logging' if request.is_local else myconf.get('smtp.server')
mail.settings.sender = myconf.get('smtp.sender')
mail.settings.login = myconf.get('smtp.login')
mail.settings.tls = myconf.get('smtp.tls') or False
mail.settings.ssl = myconf.get('smtp.ssl') or False

# -------------------------------------------------------------------------
# configure auth policy
# -------------------------------------------------------------------------
auth.settings.registration_requires_verification = False
auth.settings.registration_requires_approval = False
auth.settings.reset_password_requires_verification = True

# -------------------------------------------------------------------------
# Define your tables below (or better in another model file) for example
#
# >>> db.define_table('mytable', Field('myfield', 'string'))
#
# Fields can be 'string','text','password','integer','double','boolean'
#       'date','time','datetime','blob','upload', 'reference TABLENAME'
# There is an implicit 'id integer autoincrement' field
# Consult manual for more options, validators, etc.
#


db.define_table('ecu_db',
                db.Field.Virtual('serial', lambda row: str(row.ecu_db.id)+'.'+str(row.ecu_db.ecu_type)+':'+str(row.ecu_db.update_version)),
                db.Field('supplier_name', 'string', length=25, default=auth.user.username if auth.user else None, readable=False, writable=False),
                db.Field('ecu_type', 'string', requires=IS_IN_SET(['BCU', 'INFO', 'TCU'])),
                db.Field('update_version', 'string', length=25,  requires=IS_NOT_EMPTY()),
                db.Field('update_image', 'upload', uploadfolder=request.folder+'static/uploads' ,required=True, requires=IS_NOT_EMPTY()),
                db.Field('metadata', 'string', required=True, requires=IS_NOT_EMPTY(), readable=False, writable=False),
                fake_migrate=False,
                migrate=True)

db.define_table('vehicle_db',
                db.Field('vin', 'string', length=25, unique=True),
                db.Field('note', 'string', length=25, requires=IS_NOT_EMPTY()),
                db.Field('oem', 'string', length=25, default=auth.user.username if auth.user else None, readable=False, writable=False),
                db.Field('ecu_list', 'list:reference ecu_db', required=True, readable=False),
                db.Field('supplier_version', 'string', required=True, writable=False, default=''),
                db.Field('director_version', 'string', required=True, writable=False, default=''),# requires=IS_NOT_EMPTY()),
                #db.Field.Method('virtual1', lambda row: row.vehicle_db.ecu_list),# requires=IS_NOT_EMPTY()),
                #db.Field.Virtual('displays_ecu_id', lambda row: row.vehicle_db.ecu_list),# requires=IS_NOT_EMPTY()),
                db.Field('vehicle_version', 'string', length=25, required=True, writable=False, default='', requires=IS_NOT_EMPTY()),
                db.Field('status', 'string', length=25, required=True, writable=False, readable=False, default='Good'),
                db.Field('time_elapsed', 'string', length=25, default='', writable=False),
                db.Field('checkin_date', 'datetime', length=25, required=True, requires=IS_NOT_EMPTY(), readable=False),
                fake_migrate=False,
                migrate=True)


# More API examples for controllers:
#
# >>> db.mytable.insert(myfield='value')
# >>> rows = db(db.mytable.myfield == 'value').select(db.mytable.ALL)
# >>> for row in rows: print row.id, row.myfield
# -------------------------------------------------------------------------

# -------------------------------------------------------------------------
# after defining tables, uncomment below to enable auditing
# -------------------------------------------------------------------------
# auth.enable_record_versioning(db)