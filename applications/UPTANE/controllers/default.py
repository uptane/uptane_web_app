# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

# -------------------------------------------------------------------------
# This is the main controller
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
        return dict(form=update_form(), db_contents=database_contents())
    # if Supplier 2
    if user == 'supplier2':
        return dict(form=update_form(), db_contents=database_contents())
    else:
        return dict(message=T('Hello unknown user..'))

@auth.requires_login()
def hacked():
    return database_contents()

@auth.requires_login()
def hacked_repo():
    return dict(form=update_form(), db_contents=database_contents())


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
    #print('vehicles:\t {0}'.format(vehicles))
    # Retrieve a list of vehicles associated w/ OEM
    if vehicles:
        for v in vehicles:
            #print('\nv:\t{0}'.format(v))
            # Iterate through ECUs for each vehicle to determine if a newer one exists
            for e in v.ecu_list:
                try:
                    #print('\ne:\t{0}'.format(e))
                    # Retrieve the ecu based off the id
                    ecu = db(db.ecu_db.id == e).select().first()
                    #print('\necu:\t{0}'.format(ecu))
                    # Retrieve the type from the ecu object
                    if ecu:
                        ecu_type = ecu.ecu_type
                        #print('\necu_type:\t{0}'.format(ecu_type))
                        # Query the database for updates for ecu_type and select the last one (i.e., most recent update)
                        ecu_type_updates = db(db.ecu_db.ecu_type == ecu_type).select().last()
                        # If the last update for this ecu_type id is > ecu.id then there's a newer update available
                        # so append the vehicle id to the available update list and break
                        if ecu_type_updates.id > e:
                            available_update_list.append(v.id)
                            break
                        else:
                            continue
                except Exception as e:
                    print('Unable to determine the available updates due to this error: {0}'.format(e))
    #print(available_update_list)
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
    ''' This is the form the Supplier will see at the top of the screen that allows them to upload a new firmware image
    :return: the form that will be utilized by the user
    '''

    imagerepo = xmlrpc.client.ServerProxy('http://' + str(demo.IMAGE_REPO_SERVICE_HOST) +
                                            ':' + str(demo.IMAGE_REPO_SERVICE_PORT))


    #print(request.args)
    record = db.ecu_db(request.args(1))
    #print(record)
    form=SQLFORM(db.ecu_db)#, record)

    if form.validate():
        # Adding the update to the Image (Supplier) Repo
        cwd = os.getcwd()
        update_image = form.vars.update_image

        # After getting the file image name, convert the name of the file from hex to ascii
        # and use this value to populate the imagerepo db with
        filename = return_filename(update_image)

        # Add uploaded images to imagerepo repo + write to repo
        imagerepo.add_target_to_image_repo(cwd+'/applications/UPTANE/static/uploads/'+update_image, filename)
        imagerepo.write_image_repo()

        # Metadata was initially intended to be showed, so this place holder function call was created
        meta = create_meta(form.vars.ecu_type + '_' + form.vars.update_version)

        # Add or Update this instantiation of the ECU in the ECU db
        id_added = db.ecu_db.update_or_insert((db.ecu_db.supplier_name == auth.user.username) &
                                        (db.ecu_db.ecu_type == form.vars.ecu_type) &
                                        (db.ecu_db.update_version == form.vars.update_version),
                                        ecu_type=form.vars.ecu_type,
                                        update_version=form.vars.update_version,
                                        supplier_name=auth.user.username,
                                        metadata=meta,
                                        update_image=form.vars.update_image)
        print('id_added: {0}\necu:{1}'.format(id_added, db.ecu_db.id==id_added))

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
    try:
        #print('\n\nCREATE_VEHICLE()')
        director = xmlrpc.client.ServerProxy('http://' + str(demo.DIRECTOR_SERVER_HOST) +
                                            ':' + str(demo.DIRECTOR_SERVER_PORT))
        #print('\n\nAFTER CREATING DIRECTOR@ ADDR: {0}:{1}'.format(str(demo.DIRECTOR_SERVER_HOST), str(demo.DIRECTOR_SERVER_PORT)))

        # Add a new vehicle to the director repo (which includes writing to the repo)
        director.add_new_vehicle(form.vars.vin)
        director.write_director_repo(form.vars.vin)

        pri_ecu_key = demo.import_public_key('primary')
        sec_ecu_key = demo.import_public_key('secondary')
        ecu_pub_key = ''
        #print('\n\n\ncreating vehicle now\n{0}\ttype: {1}\n'.format(form.vars, type(form.vars)))
        #print('pri_ecu_key: {0}\nsec_ecu_key: {1}\necu_pub_key: {2}'.format(pri_ecu_key, sec_ecu_key, ecu_pub_key))
        for e_id in form.vars.ecu_list:
            ecu = db(db.ecu_db.id==e_id).select().first()

            # Retrieve the filename to add the target to the director
            cwd = os.getcwd()
            filename = return_filename(ecu.update_image)
            filepath = cwd + str('/applications/UPTANE/test_uploads/'+filename)

            # Determine if ECU is primary or secondary
            is_primary = True if ecu.ecu_type == 'INFO' else False

            # If it's a secondary, then add the target to the director and write to the director repo
            if not is_primary:
                director.add_target_to_director(filepath, filename, form.vars.vin, ecu.ecu_type+str(form.vars.vin))
                director.write_director_repo(form.vars.vin)

            # Register the ecu w/ the vehicle
            ecu_pub_key = pri_ecu_key if is_primary else sec_ecu_key
            #print('\necu.ecu_type: {0} + form.vars.vin: {1}\tis_primary: {2}'.format(ecu.ecu_type, form.vars.vin, is_primary))
            # only register ecus ONCE - correct?
            director.register_ecu_serial(ecu.ecu_type+str(form.vars.vin), ecu_pub_key, form.vars.vin, is_primary)
            # Necessary?
            #director.write_director_repo(form.vars.vin)
    except Exception as e:
        print('Unable to create a new vehicle due to the following issue: {0}'.format(e))


@auth.requires_login()
def get_supplier_versions(list_of_vehicles):
    try:
        info = db(db.ecu_db.ecu_type=='INFO').select().last()
        bcu = db(db.ecu_db.ecu_type=='BCU').select().last()
        tcu = db(db.ecu_db.ecu_type=='TCU').select().last()
        #print('\n\ninfo: {0}\nbcu: {1}\ntcu: {2}'.format(info, bcu, tcu))
        supplier_version = str(bcu.ecu_type) + " : " + str(bcu.update_version) + '\n' + \
                           str(info.ecu_type) + " : " + str(info.update_version) + '\n' + \
                           str(tcu.ecu_type) + " : " + str(tcu.update_version)

        for vehicle in list_of_vehicles:
            # Assume all vehicles have TCU, BCU, and INFO
            vehicle.update_record(supplier_version=supplier_version)
    except Exception as e:
        print('Unable to get the supplier versions due to the following error: {0}'.format(e))

@auth.requires_login()
def get_director_versions(list_of_vehicles):
    try:
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
                #print('director_version: {0}'.format(director_version))
                #print('version_dict: {0}'.format(version_dict))
                #print('ordered: version_dict: {0}'.format(OrderedDict(sorted(version_dict.items()))))
            # Director Str Version
            vehicle.update_record(director_version = director_version)
            #db.vehicle_db(db.vehicle_db.id == vehicle).update_record(director_version = director_version)
            # Dictionary Version
            #db.vehicle_db(db.vehicle_db.id == vehicle).update_record(director_version = version_dict)
    except Exception as e:
        print('Unable to get the director versions due to the following error: {0}'.format(e))

@auth.requires_login()
def get_vehicle_versions(list_of_vehicles):
    director = xmlrpc.client.ServerProxy('http://' + str(demo.DIRECTOR_SERVER_HOST) +
                                            ':' + str(demo.DIRECTOR_SERVER_PORT))

    # Iterate through the list of vehicles in order to return the vehicle reported versions
    for vehicle in list_of_vehicles:
        #print('vehicle: {0} : vin#: {1}'.format(vehicle, vehicle.vin))
        try:
            # Currently we're iterating through the 3 ECU types we limit the Supplier in uploading in order to retrieve
            #  their ECU manifests.  These are used to append to the ecu_serial_string.
            ecu_list = ['BCU', 'INFO', 'TCU']
            ecu_serial_string = ''
            # If the default file is returned from the ECU manifests (secondary_firmware.txt), then is_default stays true
            #  and the checkin time for the vehicle will not be updated.  However, if the ECU manifests have a different
            #  file (i.e., the vehicle has 'updated'), then is_default gets set to False and the checkin time shall be
            #  updated.
            is_default = True
            update_checkin_time = False
            # Iterate through the list of ECU's (which is currently hardcoded) and gather their ecu_manifest
            #   From each ecu_manifest, parse the file name of their current image and add it to the ecu_serial_string
            for ecu in ecu_list:
                ecu_manifest = director.get_last_ecu_manifest(str(ecu)+str(vehicle.vin))
                try:
                    file_path = ecu_manifest['signed']['installed_image']['filepath']
                    if file_path == '/secondary_firmware.txt':
                        ecu_serial_string += '{0} : {1}  '.format(str(ecu), 'N/A')
                    else:
                        is_default = False
                        update_checkin_time = True
                        ecu_serial_string += '{0} : {1}  '.format(str(ecu), file_path[-7:-4])
                except Exception:
                    # This is to catch the error received from an ECU manifest that returns an error
                    ecu_serial_string += '{0} : {1}  '.format(str(ecu), 'N/A') if is_default else '{0} : {1}  '.format(str(ecu), '1.0')

            vehicle.update_record(vehicle_version=ecu_serial_string)
            cur_time = datetime.datetime.now()

            vehicle.update_record(checkin_date=cur_time) if update_checkin_time else print('Checkin date will not be updated for vehicle: {0}'.format(vehicle.vin))
        except Exception as e:
            vehicle.update_record(vehicle_version='None')
            print('did not work with this error: {0}'.format(e))

@auth.requires_login()
def get_status(list_of_vehicles):
    director = xmlrpc.client.ServerProxy('http://' + str(demo.DIRECTOR_SERVER_HOST) +
                                            ':' + str(demo.DIRECTOR_SERVER_PORT))

    # Iterate through the list of vehicles in order to return the ECU reported attacks detected
    for vehicle in list_of_vehicles:
        try:
            # Get the vehicle's manifest
            vv = director.get_last_vehicle_manifest(vehicle.vin)
            attack_status = ''
            if 'signed' in vv:
                try:
                    # Retrieve all of the reported ecu_version manifests keys
                    ecu_serials = list(vv['signed']['ecu_version_manifests'].keys())
                    if ecu_serials:
                        for ecu in ecu_serials:
                            # Retrieve the ECU's last manifest to parse the attacks_detected
                            ecu_mani = director.get_last_ecu_manifest(ecu)
                            if ecu_mani:
                                attack_status = ecu_mani['signed']['attacks_detected']
                except Exception:
                    print('Unable to get the ecu_version_manifests from the vehicle manifest.')

            # If the attack_status is not the default of '' then we'll return the reported attack_status
            #   otherwise, we'll return a value of 'Good'
            attack_status = attack_status if attack_status else 'Good'
            vehicle.update_record(status=attack_status)

        except Exception as e:
            vehicle.update_record(status='Unknown')
            print('get_status failed with this error: {0}'.format(e))

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
    # return the database contents based off the current_user
    current_user = auth.user.username

    # If it's a supplier, pull up data based off their username
    if current_user == 'supplier1' or current_user == 'supplier2':
        if db.ecu_db.id != '':
            # The following sets the ID#'s to non-readable and pulls all ECU's created by the current user
            db.ecu_db.id.readable=False
            db_contents = SQLFORM.grid(db.ecu_db.supplier_name==auth.user.username, searchable=False, csv=False,
                                       create=False, editable=False, details=False)
                                       #onvalidation=add_ecu_validation)
        else:
            db_contents = T('Hello, you have no ecu/vehicles....')
        return db_contents

    # Else it's an OEM; so display database applicable to them
    else:
        #print('\nrequest: {0}'.format(request.vars['ecu_list']))
        list_of_vehicles = db(db.vehicle_db.oem==auth.user.username).select()
        get_supplier_versions(list_of_vehicles)
        get_director_versions(list_of_vehicles)
        get_vehicle_versions(list_of_vehicles)
        get_status(list_of_vehicles)
        get_time_elapsed(list_of_vehicles)
        db.vehicle_db.id.readable=False
        db_contents = SQLFORM.grid(db.vehicle_db.oem==auth.user.username, create=True,
                                   selectable=lambda vehicle_id: selected_vehicle(vehicle_id), csv=False,
                                   searchable=False, details=False, editable=False, oncreate=create_vehicle,
                                   selectable_submit_button='View Vehicle Data',
                                   maxtextlengths={'vehicle_db.supplier_version' : 50,
                                                   'vehicle_db.director_version'  : 50,#,
                                                   'vehicle_db.vehicle_version'  : 50})#,
                                    # HREF link to another page - may be good for 'available updates': links = [lambda row: A('Director Updates', _href=URL("default","show",args=[row.id]))])

        #print('request.args: {0}\n'.format(request.args))

        # If we are adding a new vehicle to the database
        if 'new' in request.args:
            # Regex used to find all ecu 'options' within the db_contents div tag
            #   String we are parsing db_contents for, thus reasoning for specific regex: '<div>[ecu_id]</div>'
            reg_val = re.findall("\>\d{1,3}\<", str(db_contents))
            # If there is a match, pull value from ecu_db
            if reg_val:
                for reg in reg_val:
                    ecu_id= reg[1:-1]
                    ecu = db(db.ecu_db.id==ecu_id).select().first()
                    ecu_name = ecu.ecu_type
                    ecu_ver  = ecu.update_version
                    ecu_str  = '>' + ecu_name + ' - ' + ecu_ver + '<'

                    # Find old 'option' string and replace with newly retrieved ECU Type + Version
                    db_contents = gluon.html.XML(str(db_contents).replace(reg, ecu_str))

        #print('request.args w/ error: {0}'.format(request.args))
        #print('db_contents: {0}'.format(db_contents))

        changed_ecu_list = request.vars['changed_ecu_list']
        edited_vehicle=request.vars['vehicle_id']
        error_message=request.vars['error_message']
        #print('request.vars: {0}\n'.format(request.vars))
        #print('error message: {0}\ntype: {1}'.format(error_message, type(error_message)))
        #print('changed ecu_list: {0}'.format(changed_ecu_list))
        #print('edited_vehicle: {0}'.format(edited_vehicle))
        #print('\nDetermining vehicles w/ available updates')
        available_updates = []
        available_updates = determine_available_updates()

        #db_contents = SQLFORM.smartgrid(db.vehicle_db)
        if changed_ecu_list == None:
            return dict(db_contents=db_contents, available_updates=available_updates, error_message=error_message)
        else:
            return dict(db_contents=db_contents,changed_ecu_list=changed_ecu_list,edited_vehicle=edited_vehicle,
                        available_updates=available_updates, error_message=error_message)

@auth.requires_login()
def selected_vehicle(vehicle_id):
    print('Here I am inside of the selectable...')
    # Ensure that a single vehicle is selected before continuing
    error_message = None
    if len(vehicle_id) == 1:
    #    print('vehicle_id')
    #    print(vehicle_id)
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
        #print('ecu_id_list')
        #print(vehicle_ecu_list)
        #ecu_view = (dict(ecu_list=SQLFORM.grid((db.ecu_db.id==ecu_id_list[0]))))
        #return locals()

        redirect(URL('ecu_list', vars=dict(vehicle_ecu_list=vehicle_ecu_list, ecu_type_list=ecu_type_list, ecu_id_list=ecu_id_list, vehicle_id=vehicle_id)))
        #ecu_list(ecu_id_list)
        #redirect(URL('next', 'list_records', vars=vehicle_id[0]))
    else:
        print('Please select a single vehicle first.')
        error_message = 'Please select a single vehicle before proceeding.'
        redirect(URL('index', vars=dict(error_message=error_message)))

@auth.requires_login()
def ecu_list():
    vehicle_ecu_list =  request.vars['vehicle_ecu_list']
    ecu_id_list =  request.vars['ecu_id_list']
    ecu_type_list = request.vars['ecu_type_list']
    vehicle_id = request.vars['vehicle_id']
    vehicle_vin = db(db.vehicle_db.id==vehicle_id).select().first().vin

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

    #print('query: {0}'.format(query))
    # This line changes our custom query (created above) from a str to a type Query
    # This enables us to send the query as the first argument for SQLFORM.grid()
    mod_query = db(eval(query))
    #print('mod query: {0}'.format(mod_query))
    db.ecu_db.id.readable=False
    return dict(ecu_type_list=ecu_type_list, ecu_id_list=ecu_id_list,
                ecu_list=SQLFORM.grid(mod_query, selectable=lambda ecus: selected_ecus(ecus), csv=False,
                                      orderby=[db.ecu_db.ecu_type, ~db.ecu_db.update_version],
                                      searchable=False, editable=False, deletable=False, create=False,details=False,
                                      selectable_submit_button='Create Bundle',
                                      onupdate=create_bundle_update()),
                vehicle_vin=vehicle_vin)#, selected=ecu_id_list))


@auth.requires_login()
def create_bundle_update():
    print('\n\nUP inside the update')


@auth.requires_login()
def selected_ecus(selected_ecus):
    #print('inside selected ecus')
    ecu_id_list = request.vars['ecu_id_list']
    changed_ecu_list = []
    vehicle_id = request.vars['vehicle_id']

    is_primary = False
    for ecu in selected_ecus:
        if str(ecu) not in ecu_id_list:
            changed_ecu_list.append(ecu)
        else:
            print(str(ecu) + ' is in the list!')

    #print('changed_ecu_list: {0}'.format(changed_ecu_list))
    if changed_ecu_list:
        db.vehicle_db(db.vehicle_db.id == vehicle_id).update_record(ecu_list=selected_ecus)
        #if len(changed_ecu_list) == 1: # <~> Why use this condition?
        print('changed_ecu_list contains ' + repr(len(changed_ecu_list)))

        director = xmlrpc.client.ServerProxy('http://' + str(demo.DIRECTOR_SERVER_HOST) +
                                                ':' + str(demo.DIRECTOR_SERVER_PORT))
        # <~> I'd expect vin to be the same within this call, since this
        # dialog is for an individual vehicle. No?
        vin = db(db.vehicle_db.id==vehicle_id).select().first().vin
        director.clear_vehicle_targets(vin)
        for i in range(len(changed_ecu_list)):


            cur_ecu = db(db.ecu_db.id==changed_ecu_list[i]).select().first()
            #print('\ncur_ecu: {0}'.format(cur_ecu))

            # Do a check to see if it's the Primary (potentially add it after appending to
            #   changed_ecu_list w/ boolean is_primary)
            is_primary = True if cur_ecu.ecu_type == 'INFO' else False

            #print('\ncur_ecu: {0}'.format(cur_ecu))
            #print('\nis_primary: {0}'.format(is_primary))

            # Add the bundle to the vehicle
            cwd = os.getcwd()
            #print('\ncwd now2: {0}'.format(cwd))

            # Retrieve the filename
            filename = return_filename(cur_ecu.update_image)
            # <~> Why are we using test_uploads paths? We can't assume the
            # image files exist in the test_uploads folder.
            filepath = cwd + str('/applications/UPTANE/test_uploads/'+filename)


            vehicle_id = request.vars['vehicle_id']
            #print('vehicle_id: {0}'.format(vehicle_id))
            ecu_serial = cur_ecu.ecu_type+str(vin)

            #print('filepath: {0}\nfilename: {1}\nvin: {2}\necu_serial: {3}'.format(filepath, filename, vin, ecu_serial))

            director.add_target_to_director(filepath, filename, vin, ecu_serial)
            director.write_director_repo(vin)

            pri_ecu_key = demo.import_public_key('primary')
            sec_ecu_key = demo.import_public_key('secondary')
            ecu_pub_key = ''


            # <~> Why would we register the ECU every time we want to update it?
            # (Am I missing something?)
            # # Register the ecu w/ the vehicle
            # is_primary = True if cur_ecu.ecu_type == 'INFO' else False
            # ecu_pub_key = pri_ecu_key if is_primary else sec_ecu_key
            # print('\necu.type+vin: {0}{1}\tform.vars.vin: {2}\tis_primary: {3}'.format(cur_ecu.ecu_type, str(vin), vin, is_primary))
            # director.register_ecu_serial(cur_ecu.ecu_type+str(vin), ecu_pub_key, vin, is_primary)

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


# This function is intended to be used with a Director/OEM resetting their system
@auth.requires_login()
def reset_system():
    ''' This method is invoked when the Reset System button is clicked on the OEM screen.
    The intention of this function is to remove only the latest added ECU update and vehicle.
    :return: Updated ecu_db and vehicle_db
    '''
    try:
        vehicles = db(db.vehicle_db.oem == auth.user.username).select()
        ecus     = db(db.ecu_db.supplier_name == 'supplier1').select()

        # If there are more than one ecu's then continue (don't want to delete the last remaining ecu)
        if ecus and len(ecus) >1:
            # Get the last ecu from the pydal.Objects.Rows -- could iterate through the rows if necessary
            ecu = ecus.last()

            # Uncomment this line below if you want to delete the ecu
            #db(db.ecu_db.id == ecu.id).delete()

        # If there are more than one vehicles then continue (don't want to delete the last remaining vehicle)
        if vehicles and len(vehicles) >1:
            # Setup the director to call the XMLRPC call
            # If the vehicle vin is needed can get it from: vehicle.vin (assuming it's a single vehicle and not the list of vehicles)
            #director = xmlrpc.client.ServerProxy('http://' + str(demo.DIRECTOR_SERVER_HOST) +
            #                            ':' + str(demo.DIRECTOR_SERVER_PORT))
            #director.clear_vehicle_targets()

            # Get the last vehicle from the pydal.Objects.Rows -- could iterate through the rows if necessary
            vehicle = vehicles.last()

            # Uncomment this line below if you want to delete the ecu
            #db(db.vehicle_db.id == vehicle.id).delete()

    except Exception as e:
        print('Unable to reset the system due to this error: {0}'.format(e))



# The calls below are intended to be used with the hacked.html page
# for a hacked Director Repository.
# In each of the attack scripts and recovery scripts below, we'll hard-code the
# vehicle identifier and image filename for the demo.

@auth.requires_login()
def hack1():
    print('\n\nDirector Hack1 - Arbitrary Package Nokeys - CLICKED!')
    director = xmlrpc.client.ServerProxy('http://' + str(demo.DIRECTOR_SERVER_HOST) +
                                        ':' + str(demo.DIRECTOR_SERVER_PORT))
    director.mitm_arbitrary_package_attack('democar', 'TCU1.1.txt')
    print('\n\nDirector Hack1 - Arbitrary Package Nokeys - Done')

@auth.requires_login()
def hack2():
    print('\n\nDirector Hack2 - Prepare for Replay Attack Nokeys - CLICKED!')
    director = xmlrpc.client.ServerProxy('http://' + str(demo.DIRECTOR_SERVER_HOST) +
                                        ':' + str(demo.DIRECTOR_SERVER_PORT))
    director.prepare_replay_attack_nokeys('democar')
    print('\n\nDirector Hack2 - Prepare for Replay Attack Nokeys - Done')

@auth.requires_login()
def hack3():
    print('\n\nDirector Hack3 - Replay Attack Nokeys - CLICKED!')
    director = xmlrpc.client.ServerProxy('http://' + str(demo.DIRECTOR_SERVER_HOST) +
                                        ':' + str(demo.DIRECTOR_SERVER_PORT))
    director.replay_attack_nokeys('democar')
    print('\n\nDirector Hack3 - Replay Attack Nokeys - Done')

@auth.requires_login()
def hack4():
    print('\n\nDirector Repo Hack4 - Arbitrary Package Attack w/ Key CLICKED!')
    director = xmlrpc.client.ServerProxy('http://' + str(demo.DIRECTOR_SERVER_HOST) +
                                        ':' + str(demo.DIRECTOR_SERVER_PORT))
    director.keyed_arbitrary_package_attack(
        'democar', 'TCUdemocar', 'TCU1.1.txt')
    print('\n\nDirector Repo Hack4 - Arbitrary Package Attack w/ Key - Done!')

@auth.requires_login()
def hack5():
    print('\n\nDirector Repo Hack5 - Sign with Compromised Keys - CLICKED!')
    director = xmlrpc.client.ServerProxy('http://' + str(demo.DIRECTOR_SERVER_HOST) +
                                        ':' + str(demo.DIRECTOR_SERVER_PORT))
    director.sign_with_compromised_keys_attack()
    print('\n\nDirector Repo Hack5 - Sign with Compromised Keys - Done')

@auth.requires_login()
def hack6():
    print('\n\nHack6 Clicked - No Action')

@auth.requires_login()
def fix1():
    print('\n\nDirector Fix1 - Undo Arbitrary Package Nokeys - CLICKED!')
    director = xmlrpc.client.ServerProxy('http://' + str(demo.DIRECTOR_SERVER_HOST) +
                                        ':' + str(demo.DIRECTOR_SERVER_PORT))
    director.undo_mitm_arbitrary_package_attack('democar', 'TCU1.1.txt')
    print('\n\nDirector Fix1 - Undo Arbitrary Package Nokeys - Done')

@auth.requires_login()
def fix2():
    print('\n\nFix2 Clicked - No Action')

@auth.requires_login()
def fix3():
    print('\n\Director Fix3 - Undo Replay Attack Nokeys - CLICKED!')
    director = xmlrpc.client.ServerProxy('http://' + str(demo.DIRECTOR_SERVER_HOST) +
                                        ':' + str(demo.DIRECTOR_SERVER_PORT))
    director.undo_replay_attack_nokeys('democar')
    print('\n\Director Fix3 - Undo Replay Attack Nokeys - Done')

@auth.requires_login()
def fix4():
    print('\n\nDirector Fix4 - Undo Arbitrary Package Attack w/ Key - CLICKED!')
    director = xmlrpc.client.ServerProxy('http://' + str(demo.DIRECTOR_SERVER_HOST) +
                                        ':' + str(demo.DIRECTOR_SERVER_PORT))
    director.undo_keyed_arbitrary_package_attack(
        'democar', 'TCUdemocar', 'TCU1.1.txt')
    print('\n\nDirector Fix4 - Undo Arbitrary Package Attack w/ Key - Done')

@auth.requires_login()
def fix5():
    print('\n\nDirector Fix5 - Undo Sign with Compromised Keys - CLICKED!')
    director = xmlrpc.client.ServerProxy('http://' + str(demo.DIRECTOR_SERVER_HOST) +
                                        ':' + str(demo.DIRECTOR_SERVER_PORT))
    director.undo_sign_with_compromised_keys_attack()
    print('\n\nDirector Fix5 - Undo Sign with Compromised Keys - Done')

@auth.requires_login()
def fix6():
    print('\n\nFix6 Clicked - No Action')

# The calls below are intended to be used with the hacked_repo.html page
# for a hacked Image Repository.
@auth.requires_login()
def repo_hack1():
    """Arbitrary Package Attack on the Image Repo without Compromised Keys"""
    print('\n\nImage Repo Hack1 - MITM Arbitrary Package Nokeys - CLICKED!')
    imagerepo = xmlrpc.client.ServerProxy('http://' + str(demo.IMAGE_REPO_SERVICE_HOST) +
                                        ':' + str(demo.IMAGE_REPO_SERVICE_PORT))
    imagerepo.mitm_arbitrary_package_attack('TCU1.1.txt')

@auth.requires_login()
def repo_hack2():
    print('\n\nRepo Hack2 Clicked - No Action')

@auth.requires_login()
def repo_hack3():
    print('\n\nRepo Hack3 Clicked - No Action')

@auth.requires_login()
def repo_hack4():
    print('\n\nImage Repo Hack4 - Arbitrary Package Compromised Key CLICKED!')
    imagerepo = xmlrpc.client.ServerProxy('http://' + str(demo.IMAGE_REPO_SERVICE_HOST) +
                                        ':' + str(demo.IMAGE_REPO_SERVICE_PORT))
    imagerepo.keyed_arbitrary_package_attack('TCU1.1.txt')

@auth.requires_login()
def repo_hack5():
    print('\n\nRepo Hack5 Clicked - No Action')

@auth.requires_login()
def repo_hack6():
    print('\n\nRepo Hack6 Clicked - No Action')

@auth.requires_login()
def repo_fix1():
    """Undo Arbitrary Package attack w/out compromised keys"""
    print('\n\nImage Repo Fix1 - MITM Arbitrary Package Nokeys - CLICKED!')
    imagerepo = xmlrpc.client.ServerProxy('http://' + str(demo.IMAGE_REPO_SERVICE_HOST) +
                                        ':' + str(demo.IMAGE_REPO_SERVICE_PORT))
    imagerepo.undo_mitm_arbitrary_package_attack('TCU1.1.txt')

@auth.requires_login()
def repo_fix2():
    print('\n\nRepo Fix2 Clicked - No Action')

@auth.requires_login()
def repo_fix3():
    print('\n\nRepo Fix3 Clicked - No Action')

@auth.requires_login()
def repo_fix4():
    print('\n\nImage Repo Fix4 - Arbitrary Package Compromised Key Recovery CLICKED!')
    imagerepo = xmlrpc.client.ServerProxy('http://' + str(demo.IMAGE_REPO_SERVICE_HOST) +
                                        ':' + str(demo.IMAGE_REPO_SERVICE_PORT))
    imagerepo.undo_keyed_arbitrary_package_attack('TCU1.1.txt')

@auth.requires_login()
def repo_fix5():
    print('\n\nRepo Fix5 Clicked - No Action')

@auth.requires_login()
def repo_fix6():
    print('\n\nRepo Fix6 Clicked - No Action')
