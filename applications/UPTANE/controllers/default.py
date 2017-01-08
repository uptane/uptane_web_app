# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

# -------------------------------------------------------------------------
# This is a sample controller
# - index is the default action of any application
# - user is required for authentication and authorization
# - download is for downloading files uploaded in the db (does streaming)
# -------------------------------------------------------------------------
from web2py import gluon
from applications.UPTANE.modules.test_external import create_meta
from collections import OrderedDict

@auth.requires_login()
def index():
    """
    example action using the internationalization operator T and flash
    rendered by views/default/index.html or views/generic.html

    if you need a simple wiki simply replace the two lines below with:
    return auth.wiki()
    """
    user = auth.user.username
    # if OEM1
    if user == 'oem1':
        return database_contents()
    # if OEM2
    if user == 'oem2':
        return database_contents()
    # if Supplier 1
    if user == 'supplier1':
        return dict(form=update_form(), db_contents=database_contents())#,form=update_form())
    # if Supplier 2
    if user == 'supplier2':
        return dict(form=update_form(), db_contents=database_contents())
    else:
        return dict(message=T('Hello unknown user..'))

@auth.requires_login()
def hacked():
    print(' HACKED  !!!')
    return database_contents()

def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    http://..../[app]/default/user/bulk_register
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    also notice there is http://..../[app]/appadmin/manage/auth to allow administrator to manage users
    """
    return dict(form=auth())


@cache.action()
def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request, db)


def determine_available_updates():
    available_update_list = []
    vehicles =  db(db.vehicle_db.oem == auth.user.username).select()
    print('vehicles:\t {0}'.format(vehicles))
    # Retrieve a list of vehicles associated w/ OEM
    for v in vehicles:
        #print('\bv:\t{0}'.format(v))
        # Iterate through ECUs for each vehicle to determine if a newer one exists
        for e in v.ecu_list:
            #print('\be:\t{0}'.format(e))
            # Retrieve the ecu based off the id
            ecu = db(db.ecu_db.id == e).select().first()
            #print('\becu:\t{0}'.format(ecu))
            # Retrieve the name from the ecu object
            ecu_type = ecu.ecu_type
            #print('\becu_type:\t{0}'.format(ecu_type))
            # Query the database for updates for ecu_type
            ecu_type_updates = db(db.ecu_db.ecu_type == ecu_type).select()
            #print('\becu_type_updates:\t{0}'.format(ecu_type_updates))
            for name_update in ecu_type_updates:
                # Iterate through to determine if id # is > current ecu_id (not ideal, but straight-forward solution
                #   versus checking the version #'s b/n the updates
                if name_update.id > e:
                    if v.id not in available_update_list:
                        available_update_list.append(v.id)
                    #print('\nAppended the current vehicle: {0}'.format(v.id))
                    break
                else:
                    #print('\nCurrent id: {0} is <= e {1}'.format(name_update.id, e))
                    continue

        # If one ECU has an update, end the loop and add the vehicle to the available_update_list
    print(available_update_list)
    return available_update_list

def call():
    """
    exposes services. for example:
    http://..../[app]/default/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    """
    return service()

@auth.requires_login()
def all_records():
    grid = SQLFORM.grid(db.ecu_db.supplier_name==auth.user.username,user_signature=False, csv=False)
    return locals()

@auth.requires_login()
def update_form():
    record = db.ecu_db(request.args(0))
    print(record)
    form=SQLFORM(db.ecu_db, record)
    #print db.tables
    #print db.supplier_db.fields
    #print type(db.supplier_db)
    #print type(db['supplier_db'])
    #print db.supplier_db.applicable_oem.type

    if form.validate():
        #print'applicable_oem: '+ form.vars.applicable_oem
        #print'update_version: '+ form.vars.update_version
        #print'supplier_name: '+ auth.user.username
        #print db(db.supplier_db).select(db.supplier_db.applicable_oem==str(form.vars.applicable_oem))
        #print db(db.supplier_db.applicable_oem==str(form.vars.applicable_oem)).select()

        #val = db(db.supplier_db.applicable_oem==form.vars.applicable_oem).select().first()
        #if val:
        #    val.update_record(supplier_name=auth.user.username,
        #                      update_version=form.vars.update_version)
        #    print 'update'
        #else:
        #    print 'new'
        #print type(db.supplier_db.applicable_oem==form.vars.applicable_oem)
        #print type(db.supplier_db.applicable_oem)
        #print db.supplier_db.update_version==form.vars.update_version
        print('before update_or_insert')
        #exists = db(db.supplier_db).select(db.supplier_db.applicable_oem=str(form.vars.applicable_oem))
        #print exists

        #id_added = db.supplier_db.update_or_insert(supplier_name=auth.user.username,
        #                                     update_version=form.vars.update_version,
        #                                     applicable_oem=form.vars.applicable_oem,
        #                                     update_image=form.vars.update_image)#,
                                             #metadata=meta)
        # print form.vars.applicable_oem
        # print type(form.vars.applicable_oem)
        # print form.vars.update_version
        # print type(form.vars.update_version)
        # print auth.user.username
        # print type(auth.user.username)
        #db.supplier_db.update()

        meta = create_meta(form.vars.ecu_type + '_' + form.vars.update_version)
        id_added = db.ecu_db.update_or_insert((db.ecu_db.supplier_name == auth.user.username) &
                                        (db.ecu_db.ecu_type == form.vars.ecu_type) &
                                        (db.ecu_db.update_version == form.vars.update_version),
                                        ecu_type=form.vars.ecu_type,
                                        update_version=form.vars.update_version,
                                        supplier_name=auth.user.username,
                                        metadata=meta,
                                        update_image=form.vars.update_image)
        print(id_added)
        print('after update or insert')
        response.flash = 'form accepted'
    elif form.process().errors:
        response.flash = 'form has errors'
    else:
        response.flash = 'please fill out the form'
    return form



@auth.requires_login()
def add_ecu_validation(form):
    meta = create_meta('3')
    id_added = db.ecu_db.update_or_insert((db.ecu_db.supplier_name == auth.user.username) &
                                        (db.ecu_db.ecu_type == form.vars.ecu_type) &
                                        (db.ecu_db.update_version == form.vars.update_version),
                                        ecu_type=form.vars.ecu_type,
                                        update_version=form.vars.update_version,
                                        supplier_name=auth.user.username,
                                        metadata=meta,
                                        update_image=form.vars.update_image)

@auth.requires_login()
def create_vehicle(form):
    print('\n\ncreating vehicle now\n{0}\n'.format(form.vars))

@auth.requires_login()
def get_director_versions():
    for vehicle in db(db.vehicle_db.oem==auth.user.username).select():
        #print('\nvehicle: {0}'.format(vehicle))
        director_version = ''
        version_dict = {}
        #print('ecu_list unsorted: {0}\necu_list sorted: {1}'.format(vehicle.ecu_list, sorted(vehicle.ecu_list)))
        for ecu in vehicle.ecu_list:
            ecu_type       = db(db.ecu_db.id==ecu).select().first().ecu_type
            update_version = db(db.ecu_db.id==ecu).select().first().update_version
            version_dict[ecu_type] = update_version
            director_version += ' ' + str(ecu_type) + ' : ' + str(update_version)
            print('director_version: {0}'.format(director_version))
            #print('version_dict: {0}'.format(version_dict))
            print('ordered: version_dict: {0}'.format(OrderedDict(sorted(version_dict.items()))))
        # Director Version
        db.vehicle_db(db.vehicle_db.id == vehicle).update_record(director_version = director_version)
        # Dictionary Version
        #db.vehicle_db(db.vehicle_db.id == vehicle).update_record(director_version = version_dict)
#        print('\nAFTER vehicle: {0}'.format(vehicle))


@auth.requires_login()
def database_contents():
    # return the database contents based off the owner
    #db_contents = T('Hello billy bob..')
    #         db_contents = db(db.items.supplier_name=auth.user.username).select(db.supplier_db.id=1)
    current_user = auth.user.username

    # If it's a supplier, pull up data based off their username
    if current_user == 'supplier1' or current_user == 'supplier2':
        if db.ecu_db.id != '':
            #query = db.supplier_db.supplier_name == 'supplier1'
            #db_set = db(query)
            #rows = db_set.select()
            #print rows
            #for row in rows:
            #    print row
            # The following creates a list of the db_contents that apply to the current user
            #db_contents = []
            db_contents = SQLFORM.grid(db.ecu_db.supplier_name==auth.user.username, searchable=False, csv=False,
                                       create=False)
                                       #onvalidation=add_ecu_validation)

            #for row in db(db.supplier_db.supplier_name == auth.user.username).iterselect():
            #    db_contents.append(row)

            #print db_contents
            #db_contents = db().select(db.supplier_db.supplier_name)
        else:
            db_contents = T('Hello, you have no ecu/vehicles....')
        return db_contents
    #else it's an OEM; so display database applicable to them
    else:
        print('\nrequest: {0}'.format(request.vars['ecu_list']))
        get_director_versions()
        db_contents = SQLFORM.grid(db.vehicle_db.oem==auth.user.username,
                                   selectable=lambda vehicle_id: selected_vehicle(vehicle_id), csv=False,
                                   searchable=False, details=False, editable=True, oncreate=create_vehicle,
                                   selectable_submit_button='View Vehicle Data')#,
                                   #links = [lambda row: A('Director Updates', body=lambda row:row.virtual1)])
                                   # HREF link to another page - may be good for 'available updates': links = [lambda row: A('Director Updates', _href=URL("default","show",args=[row.id]))])
        changed_ecu_list = request.vars['changed_ecu_list']
        edited_vehicle=request.vars['vehicle_id']
        print('changed!!!')
        print(changed_ecu_list)
        print(edited_vehicle)
        print('\nDetermining vehicles w/ available updates')
        available_updates = []
        available_updates = determine_available_updates()

        #db_contents = SQLFORM.smartgrid(db.vehicle_db)
        if changed_ecu_list == None:
            return dict(db_contents=db_contents, available_updates=available_updates)
        else:
            return dict(db_contents=db_contents,changed_ecu_list=changed_ecu_list,edited_vehicle=edited_vehicle,
                        available_updates=available_updates)

@auth.requires_login()
def selected_vehicle(vehicle_id):
    #print vehicle_id[0]
    #print type(vehicle_id[0])
    print('vehicle_id')
    print(vehicle_id)
    vehicle = db(db.vehicle_db.id==vehicle_id[0]).select().first()
    #print selected_vehicle
    #print selected_vehicle.ecu_list
    vehicle_ecu_list = []
    ecu_id_list = []
    ecu_type_list = []
    for ecu in vehicle.ecu_list:
        #print ecu
        #print type(ecu)
        selected_ecu = db(db.ecu_db.id==ecu).select().first()
        #print selected_ecu.ecu_type
        #print type(selected_ecu)
        # Add all ecu_id's to the ecu_id_list
        vehicle_ecu_list.append(selected_ecu)
        ecu_id_list.append(selected_ecu.id)
        # Only add ecu_types if they are not currently in the ecu_type_list
        if selected_ecu.ecu_type not in ecu_type_list:ecu_type_list.append(selected_ecu.ecu_type)
        #name = selected_ecu.ecu_type
        #print name
    print('ecu_id_list')
    print(vehicle_ecu_list)
    #ecu_view = (dict(ecu_list=SQLFORM.grid((db.ecu_db.id==ecu_id_list[0]))))
    #return locals()

    redirect(URL('ecu_list', vars=dict(vehicle_ecu_list=vehicle_ecu_list, ecu_type_list=ecu_type_list, ecu_id_list=ecu_id_list, vehicle_id=vehicle_id)))
    #ecu_list(ecu_id_list)
    #redirect(URL('next', 'list_records', vars=vehicle_id[0]))

@auth.requires_login()
def ecu_list():
    vehicle_ecu_list =  request.vars['vehicle_ecu_list']
    ecu_id_list =  request.vars['ecu_id_list']
    ecu_type_list = request.vars['ecu_type_list']
    vehicle_id = request.vars['vehicle_id']
    vehicle_note = db(db.vehicle_db.id==vehicle_id).select().first().note
    #print ecu_id_list
    #print ecu_type_list
    #print type(ecu_id_list)
    #print len(ecu_type_list)
    # Now have to build the query that will effect what is shown on the screen
    num_ecus = 0
    query = ''
    for ecu in iter(ecu_type_list):
        #print ecu
        num_ecus += 1
        #query+="({0}=='{1}')".format(db.ecu_db.ecu_type,ecu)
        query+="(db.ecu_db.ecu_type=='" + ecu + "')"
        if num_ecus < len(ecu_type_list):
            query+=" | "

    print(query)
    # This line changes our custom query (created above) from a str to a type Query
    # This enables us to send the query as the first argument for SQLFORM.grid()
    mod_query = db(eval(query))
    #new_query = db.ecu_db(eval(query)).select()
    #new_query2 = db.ecu_db(eval(query))
    print(mod_query)
    #print type(mod_query)
    #print new_query2
    #print type(new_query2)
        #ecu_type_list.append(ecu.ecu_type)
    #print 'ecu_type_list'
    #print ecu_type_list
    #print 'afterwards'
    #return dict(ecu_list='Luke, I am your father')
    #return dict(ecu_list=SQLFORM.grid(db.vehicle_db.id==3))
    #records = db(db.ecu_db.ecu_type=='ecu1')
    #print records
    #print 'yep'
    # THIS WORKS
    #return dict(ecu_list=SQLFORM.grid(mod_query))

    #content = dict(ecu_list=SQLFORM.grid(mod_query, selectable=lambda ecu_id: selected_ecus(ecu_id_list)))
    # Uncomment these two lines if you want it to work
    #content=SQLFORM.grid(mod_query, selectable=lambda ecu_id: selected_ecus(ecu_id_list))
    #return content

    return dict(ecu_type_list=ecu_type_list, ecu_id_list=ecu_id_list,
                ecu_list=SQLFORM.grid(mod_query, selectable=lambda ecus: selected_ecus(ecus), csv=False,
                                      orderby=[db.ecu_db.ecu_type, ~db.ecu_db.update_version],
                                      searchable=False,editable=False, deletable=False, create=False,details=False,
                                      selectable_submit_button='Create Bundle'),
                vehicle_note=vehicle_note)#, selected=ecu_id_list))
    #return dict(ecu_list=SQLFORM.grid((db.ecu_db.ecu_type=='ecu1') | (db.ecu_db.ecu_type=='ecu2')))
    #redirect(URL('ecu_list', vars=dict(ecu_list=SQLFORM.grid((db.ecu_db.ecu_type=='ecu1') | (db.ecu_db.ecu_type=='ecu1'))))

    #db_contents = SQLFORM.grid(db.vehicle_db.oem==auth.user.username, selectable=lambda vehicle_id: selected_vehicle(vehicle_id))


@auth.requires_login()
def selected_ecus(selected_ecus):
    print('inside selected ecus')
    ecu_id_list = request.vars['ecu_id_list']
    changed_ecu_list = []
    vehicle_id = request.vars['vehicle_id']
    for ecu in selected_ecus:
        if str(ecu) not in ecu_id_list:
            changed_ecu_list.append(ecu)
        else:
            print(str(ecu) + ' is in the list!')

    print('changed_ecu_list: {0}'.format(changed_ecu_list))
    if changed_ecu_list:
        db.vehicle_db(db.vehicle_db.id == vehicle_id).update_record(ecu_list=selected_ecus)


    redirect(URL('index', vars=dict(ecu_id_list=ecu_id_list, selected_ecu_list=selected_ecus, changed_ecu_list=changed_ecu_list, vehicle_id=vehicle_id)))


