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
import datetime
import demo
import os
import re
import xmlrpc.client

#print('\n\n\n\npath: {0}'.format(os.path.abspath(demo.__file__)))
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
            # Retrieve the type from the ecu object
            ecu_type = ecu.ecu_type
            #print('\becu_type:\t{0}'.format(ecu_type))
            # Query the database for updates for ecu_type and select the last one (i.e., most recent update)
            ecu_type_updates = db(db.ecu_db.ecu_type == ecu_type).select().last()
            # If the last update for this ecu_type id is > ecu.id then there's a newer update available
            # so append the vehicle id to the available update list
            if ecu_type_updates.id > e:
                available_update_list.append(v.id)
                break
            else:
                continue

            #ecu_type_updates = db(db.ecu_db.ecu_type == ecu_type).select()
            #print('\becu_type_updates:\t{0}'.format(ecu_type_updates))
            #for name_update in ecu_type_updates:
            #    # Iterate through to determine if id # is > current ecu_id (not ideal, but straight-forward solution
            #    #   versus checking the version #'s b/n the updates
            #    if name_update.id > e:
            #        if v.id not in available_update_list:
            #            available_update_list.append(v.id)
            #        #print('\nAppended the current vehicle: {0}'.format(v.id))
            #        break
            #    else:
            #        #print('\nCurrent id: {0} is <= e {1}'.format(name_update.id, e))
            #        continue

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
    print('ALL RECORDS BABY!!!')
    grid = SQLFORM.grid(db.ecu_db.supplier_name==auth.user.username,user_signature=False, csv=False)
    return locals()


@auth.requires_login()
def update_form():
    print('\ncreating supplier now')
    supplier = xmlrpc.client.ServerProxy('http://' + str(demo.MAIN_REPO_SERVICE_HOST) +
                                            ':' + str(demo.MAIN_REPO_SERVICE_PORT))
    print(request.args)
    record = db.ecu_db(request.args(1))
    print(record)
    form=SQLFORM(db.ecu_db)#, record)
    #form=SQLFORM(db.ecu_db, record)
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


        # Adding the update to the supplier_repo
        cwd = os.getcwd()
        print('current working directory: {0}'.format(cwd))
        update_image = form.vars.update_image
        #print('directory of update_image: {0}'.format(update_image))
        # After getting the file image name, convert the name of the file from hex to ascii
        # and use this value to populate the supplier db with
        filename = return_filename(update_image)
        #fname_after_split=str(update_image).split('.')[-2]
        #fname = bytes.fromhex(fname_after_split).decode('utf-8')
        #print('fname: {0}'.format(fname))

        # Add uploaded images to supplier repo + write to repo
        supplier.add_target_to_supplier_repo(cwd+'/applications/UPTANE/static/uploads/'+update_image, filename)
        #print('supplier.add_target_to_supplier_repo: {0}\n'.format(var1))
        supplier.write_supplier_repo()
        #print('write_supplier_repo: {0}'.format(var2))


        meta = create_meta(form.vars.ecu_type + '_' + form.vars.update_version)
        id_added = db.ecu_db.update_or_insert((db.ecu_db.supplier_name == auth.user.username) &
                                        (db.ecu_db.ecu_type == form.vars.ecu_type) &
                                        (db.ecu_db.update_version == form.vars.update_version),
                                        ecu_type=form.vars.ecu_type,
                                        update_version=form.vars.update_version,
                                        supplier_name=auth.user.username,
                                        metadata=meta,
                                        update_image=form.vars.update_image)
        print('id_added: {0}\necu:{1}'.format(id_added, db.ecu_db.id==id_added))
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
    print('\n\nCREATE_VEHICLE()')
    director = xmlrpc.client.ServerProxy('http://' + str(demo.DIRECTOR_SERVER_HOST) +
                                        ':' + str(demo.DIRECTOR_SERVER_PORT))
    print('\n\nAFTER CREATING DIRECTOR@ ADDR: {0}:{1}'.format(str(demo.DIRECTOR_SERVER_HOST), str(demo.DIRECTOR_SERVER_PORT)))

    # Add a new vehicle to the director repo (which includes writing to the repo)
    director.add_new_vehicle(form.vars.vin)
    # Necessary? - EAC
    director.write_director_repo(form.vars.vin)

    # There's a different public key for Primary and Secondary ECU's
    #print('demo.DIRECTOR_SERVER_HOST:PORT;  {0}:{1}'.format(demo.DIRECTOR_SERVER_HOST, demo.DIRECTOR_SERVER_PORT))
    #print('uptane.WORKING_DIR;  {0}'.format(uptane.WORKING_DIR))
    #print('demo.DEMO_DIR;  {0}'.format(demo.DEMO_DIR))
    #print('DEMO_KEYS_DIR: {0}\njoin with os: {1}'.format(
    #        demo.DEMO_KEYS_DIR, os.path.join(demo.DEMO_KEYS_DIR, 'primary')))
    pri_ecu_key = demo.import_public_key('primary')
    sec_ecu_key = demo.import_public_key('secondary')
    ecu_pub_key = ''
    print('\n\n\ncreating vehicle now\n{0}\ttype: {1}\n'.format(form.vars, type(form.vars)))
    print('pri_ecu_key: {0}\nsec_ecu_key: {1}\necu_pub_key: {2}'.format(pri_ecu_key, sec_ecu_key, ecu_pub_key))
    for e_id in form.vars.ecu_list:
        ecu = db(db.ecu_db.id==e_id).select().first()

        # Retrieve the filename to add the target to the director
        cwd = os.getcwd()
        filename = return_filename(ecu.update_image)
        filepath = cwd + str('/applications/UPTANE/test_uploads/'+filename)

        # Determine if ECU is primary or secondary
        isPrimary = True if ecu.ecu_type == 'INFO' else False

        # If it's a secondary, then add the target to the director and write to the director repo
        if not isPrimary:
            director.add_target_to_director(filepath, filename, form.vars.vin, ecu.ecu_type+str(form.vars.vin))
        #    director.write_director_repo(form.vars.vin)

        # Register the ecu w/ the vehicle
        ecu_pub_key = pri_ecu_key if isPrimary else sec_ecu_key
        print('\necu.ecu_type: {0} + form.vars.vin: {1}\tisPrimary: {2}'.format(ecu.ecu_type, form.vars.vin, isPrimary))
        # only register ecus ONCE - correct?
        director.register_ecu_serial(ecu.ecu_type+str(form.vars.vin), ecu_pub_key, form.vars.vin, isPrimary)
        # Necessary?
        #director.write_director_repo(form.vars.vin)



@auth.requires_login()
def get_supplier_versions(list_of_vehicles):
    info = db(db.ecu_db.ecu_type=='INFO').select().last()
    bcu = db(db.ecu_db.ecu_type=='BCU').select().last()
    tcu = db(db.ecu_db.ecu_type=='TCU').select().last()
    print('\n\ninfo: {0}\nbcu: {1}\ntcu: {2}'.format(info, bcu, tcu))
    supplier_version = str(bcu.ecu_type) + " : " + str(bcu.update_version) + '\n' + \
                       str(info.ecu_type) + " : " + str(info.update_version) + '\n' + \
                       str(tcu.ecu_type) + " : " + str(tcu.update_version)

    for vehicle in list_of_vehicles:
        # Assume all vehicles have TCU, BCU, and INFO
        vehicle.update_record(supplier_version=supplier_version)

@auth.requires_login()
def get_director_versions(list_of_vehicles):
    for vehicle in list_of_vehicles:#db(db.vehicle_db.oem==auth.user.username).select():
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
        # Director Str Version
        vehicle.update_record(director_version = director_version)
        #db.vehicle_db(db.vehicle_db.id == vehicle).update_record(director_version = director_version)
        # Dictionary Version
        #db.vehicle_db(db.vehicle_db.id == vehicle).update_record(director_version = version_dict)

@auth.requires_login()
def get_vehicle_versions(list_of_vehicles):
    director = xmlrpc.client.ServerProxy('http://' + str(demo.DIRECTOR_SERVER_HOST) +
                                            ':' + str(demo.DIRECTOR_SERVER_PORT))
    print('director created')
    #print('last vehicle manifest: {0}'.format(director.get_last_vehicle_manifest('111')))


    # Add a new vehicle to the director repo (then write to director repo)
    for vehicle in list_of_vehicles:#db(db.vehicle_db.oem==auth.user.username).select():
        print('vehicle: {0} : vin#: {1}'.format(vehicle, vehicle.vin))
        try:
            vv = director.get_last_vehicle_manifest(vehicle.vin)
            print('\nvv: {0}'.format(vv))
            # Parsing through vehicle version manifest for pertinent information
            if 'signed' in vv:
                print(vv['signed']['ecu_version_manifests'])
            vehicle.update_record(vehicle_version=vv)
            #director.get_last_vehicle_manifest(vehicle.vin)
        except Exception:
            vehicle.update_record(vehicle_version='None')
            print('did not work with this error: {0}'.format(Exception))

@auth.requires_login()
def get_time_elapsed(list_of_vehicles):
    for vehicle in list_of_vehicles:
        cur_time = datetime.datetime.now()
        checkin_date = vehicle.checkin_date
        elapsed_time = cur_time - checkin_date

        # Convert the elapsed_time to days (d), hours (h), minutes (m), and seconds (s)
        d = divmod(elapsed_time.total_seconds(), 86400)
        h = divmod(d[1], 3600)
        m = divmod(h[1], 60)
        s = m[1]

        elapsed_time_string = '{0} days'.format(int(d[0]))
        #elapsed_time_string = '{0} days, {1} hours, {2} minutes'.format(int(d[0]),int(h[0]),int(m[0]))
        vehicle.update_record(time_elapsed=elapsed_time_string)


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
            db.ecu_db.id.readable=False
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
        list_of_vehicles = db(db.vehicle_db.oem==auth.user.username).select()
        get_supplier_versions(list_of_vehicles)
        get_director_versions(list_of_vehicles)
        #get_vehicle_versions(list_of_vehicles)
        get_time_elapsed(list_of_vehicles)
        db.vehicle_db.id.readable=False
        db_contents = SQLFORM.grid(db.vehicle_db.oem==auth.user.username, create=True,
                                   selectable=lambda vehicle_id: selected_vehicle(vehicle_id), csv=False,
                                   searchable=False, details=False, editable=True, oncreate=create_vehicle,
                                   selectable_submit_button='View Vehicle Data',
                                   maxtextlengths={'vehicle_db.supplier_version' : 50,
                                                   'vehicle_db.director_version'  : 50,#,
                                                   'vehicle_db.vehicle_version'  : 50})#,
                                   #links = [lambda row: A('Director Updates', body=lambda row:row.virtual1)])
                                   # HREF link to another page - may be good for 'available updates': links = [lambda row: A('Director Updates', _href=URL("default","show",args=[row.id]))])
        print('request.args: {0}\n'.format(request.args))

        # If we are adding a new vehicle to the database
        if 'new' in request.args:
            print('db_contents: {0}\ttype: {1}\n\n'.format(db_contents, type(db_contents)))
            # Regex used to find all ecu 'options' within the db_contents div tag
            reg_val = re.findall("\>\d{1,3}\<", str(db_contents))
            # If there is a match, pull value from ecu_db
            if reg_val:
                for reg in reg_val:
                    print('reg!: {0}\n'.format(reg))
                    ecu_id= reg[1:-1]
                    ecu = db(db.ecu_db.id==ecu_id).select().first()
                    ecu_name = ecu.ecu_type
                    ecu_ver  = ecu.update_version
                    ecu_str  = '>' + ecu_name + ' - ' + ecu_ver + '<'

                    # Find old 'option' string and replace with newly retrieved ECU Type + Version
                    db_contents = gluon.html.XML(str(db_contents).replace(reg, ecu_str))


        changed_ecu_list = request.vars['changed_ecu_list']
        edited_vehicle=request.vars['vehicle_id']
        print('changed ecu_list: {0}'.format(changed_ecu_list))
        print('edited_vehicle: {0}'.format(edited_vehicle))
        print('\nDetermining vehicles w/ available updates')
        available_updates = []
        #available_updates = determine_available_updates()

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

    print('time for the query: {0}'.format(query))
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
                                      selectable_submit_button='Create Bundle',
                                      onupdate=create_bundle_update()),
                vehicle_note=vehicle_note)#, selected=ecu_id_list))
    #return dict(ecu_list=SQLFORM.grid((db.ecu_db.ecu_type=='ecu1') | (db.ecu_db.ecu_type=='ecu2')))
    #redirect(URL('ecu_list', vars=dict(ecu_list=SQLFORM.grid((db.ecu_db.ecu_type=='ecu1') | (db.ecu_db.ecu_type=='ecu1'))))

    #db_contents = SQLFORM.grid(db.vehicle_db.oem==auth.user.username, selectable=lambda vehicle_id: selected_vehicle(vehicle_id))

@auth.requires_login()
def create_bundle_update():
    print('\n\nUP inside the update')


@auth.requires_login()
def selected_ecus(selected_ecus):
    print('inside selected ecus')
    ecu_id_list = request.vars['ecu_id_list']
    changed_ecu_list = []
    vehicle_id = request.vars['vehicle_id']

    isPrimary = False
    isSecondary = False
    for ecu in selected_ecus:
        if str(ecu) not in ecu_id_list:
            changed_ecu_list.append(ecu)
        else:
            print(str(ecu) + ' is in the list!')

    print('changed_ecu_list: {0}'.format(changed_ecu_list))
    if changed_ecu_list:
        db.vehicle_db(db.vehicle_db.id == vehicle_id).update_record(ecu_list=selected_ecus)
        if len(changed_ecu_list) == 1:

            director = xmlrpc.client.ServerProxy('http://' + str(demo.DIRECTOR_SERVER_HOST) +
                                                    ':' + str(demo.DIRECTOR_SERVER_PORT))

            # Do a check to see if it's the Primary or Secondary (potentially add it after appending to
            #   changed_ecu_list w/ boolean isPrimary, isSecondary)

            cur_ecu = db(db.ecu_db.id==changed_ecu_list[0]).select().first()
            print('\ncur_ecu: {0}'.format(cur_ecu))

            isPrimary = True if cur_ecu.ecu_type == 'INFO' else False

            print('\ncur_ecu: {0}'.format(cur_ecu))
            print('\nisPrimary: {0}'.format(isPrimary))

            # Add the bundle to the vehicle
            cwd = os.getcwd()
            print('\ncwd now2: {0}'.format(cwd))

            # Retrieve the filename
            filename = return_filename(cur_ecu.update_image)
            filepath = cwd + str('/applications/UPTANE/test_uploads/'+filename)


            vehicle_id = request.vars['vehicle_id']
            #print('vehicle_id: {0}'.format(vehicle_id))
            vin = db(db.vehicle_db.id==vehicle_id).select().first().vin
            ecu_serial = cur_ecu.ecu_type+str(vin)

            print('filepath: {0}\nfilename: {1}\nvin: {2}\necu_serial: {3}'.format(filepath, filename, vin, ecu_serial))

            director.add_target_to_director(filepath, filename, vin, ecu_serial)
            director.write_director_repo(vin)

            pri_ecu_key = demo.import_public_key('primary')
            sec_ecu_key = demo.import_public_key('secondary')
            ecu_pub_key = ''

            # Register the ecu w/ the vehicle
            isPrimary = True if cur_ecu.ecu_type == 'INFO' else False
            ecu_pub_key = pri_ecu_key if isPrimary else sec_ecu_key
            print('\necu.type+vin: {0}{1}\tform.vars.vin: {2}\tisPrimary: {3}'.format(cur_ecu.ecu_type, str(vin), vin, isPrimary))
            # only register ecus ONCE - correct?
            director.register_ecu_serial(cur_ecu.ecu_type+str(vin), ecu_pub_key, vin, isPrimary)





    redirect(URL('index', vars=dict(ecu_id_list=ecu_id_list, selected_ecu_list=selected_ecus, changed_ecu_list=changed_ecu_list, vehicle_id=vehicle_id)))

@auth.requires_login()
def return_filename(update_image):
    print('update_image: {0}'.format(update_image))

    # After getting the file image name, convert the name of the file from hex to ascii
    # and use this value to populate the supplier db with
    fname_after_split=str(update_image).split('.')[-2]
    filename = bytes.fromhex(fname_after_split).decode('utf-8')
    print('filename: {0}'.format(filename))
    return str(filename)

@auth.requires_login()
def hack1():
    print('\n\nHack1 CLICKED!!!!')
    director = xmlrpc.client.ServerProxy('http://' + str(demo.DIRECTOR_SERVER_HOST) +
                                        ':' + str(demo.DIRECTOR_SERVER_PORT))
    # Commenting this out b/c may not contain TEST_VIN in db
    #var2=director.get_last_vehicle_manifest('TEST_VIN')
    #print('Heres the output: {0}'.format(var2))
@auth.requires_login()
def hack2():
    print('\n\nHack2 CLICKED!!!!')
    director = xmlrpc.client.ServerProxy('http://' + str(demo.DIRECTOR_SERVER_HOST) +
                                        ':' + str(demo.DIRECTOR_SERVER_PORT))

@auth.requires_login()
def hack3():
    print('\n\nHack3 CLICKED!!!!')
    director = xmlrpc.client.ServerProxy('http://' + str(demo.DIRECTOR_SERVER_HOST) +
                                        ':' + str(demo.DIRECTOR_SERVER_PORT))

@auth.requires_login()
def hack4():
    print('\n\nHack4 CLICKED!!!!')
    director = xmlrpc.client.ServerProxy('http://' + str(demo.DIRECTOR_SERVER_HOST) +
                                        ':' + str(demo.DIRECTOR_SERVER_PORT))

@auth.requires_login()
def hack5():
    print('\n\nHack5 CLICKED!!!!')
    director = xmlrpc.client.ServerProxy('http://' + str(demo.DIRECTOR_SERVER_HOST) +
                                        ':' + str(demo.DIRECTOR_SERVER_PORT))

@auth.requires_login()
def hack6():
    print('\n\nHack6 CLICKED!!!!')
    director = xmlrpc.client.ServerProxy('http://' + str(demo.DIRECTOR_SERVER_HOST) +
                                        ':' + str(demo.DIRECTOR_SERVER_PORT))

@auth.requires_login()
def fix1():
    print('\n\nFix1 CLICKED!!!!')
    director = xmlrpc.client.ServerProxy('http://' + str(demo.DIRECTOR_SERVER_HOST) +
                                        ':' + str(demo.DIRECTOR_SERVER_PORT))

@auth.requires_login()
def fix2():
    print('\n\nFix2 CLICKED!!!!')
    director = xmlrpc.client.ServerProxy('http://' + str(demo.DIRECTOR_SERVER_HOST) +
                                        ':' + str(demo.DIRECTOR_SERVER_PORT))

@auth.requires_login()
def fix3():
    print('\n\nFix3 CLICKED!!!!')
    director = xmlrpc.client.ServerProxy('http://' + str(demo.DIRECTOR_SERVER_HOST) +
                                        ':' + str(demo.DIRECTOR_SERVER_PORT))

@auth.requires_login()
def fix4():
    print('\n\nFix4 CLICKED!!!!')
    director = xmlrpc.client.ServerProxy('http://' + str(demo.DIRECTOR_SERVER_HOST) +
                                        ':' + str(demo.DIRECTOR_SERVER_PORT))

@auth.requires_login()
def fix5():
    print('\n\nFix5 CLICKED!!!!')
    director = xmlrpc.client.ServerProxy('http://' + str(demo.DIRECTOR_SERVER_HOST) +
                                        ':' + str(demo.DIRECTOR_SERVER_PORT))

@auth.requires_login()
def fix6():
    print('\n\nFix6 CLICKED!!!!')
    director = xmlrpc.client.ServerProxy('http://' + str(demo.DIRECTOR_SERVER_HOST) +
                                        ':' + str(demo.DIRECTOR_SERVER_PORT))
