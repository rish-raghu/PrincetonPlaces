#!/usr/bin/env python

"""
app.py
For displaying the UI

## Supported Routes: ##
Public:
  * /
  * /photo
  * /login
  * /error

Logged In:
  * /add_photo
  * /add_pin
  * /logout
  * /edit_photo/<photo_id>
  * /liked_photos

Admin:
  * /admin
  * /admin/pin
  * /adminEditPin/<pinid>
  * /admin/photo/<photo_id>
  * /adminEditPhoto/<photo_id>
  * /adminDeletePhoto/<photo_id>
  * /adminDeletePin
  * /adminDeleteAdmin
  * /adminAddAdmin
  * /adminTogglePinHidden

Hidden:
  * /upload_photo
  * /create_pin
  * /delete/<photo_id>
  * /like
  * /make_edit/<photo_id>
  * /fetch_report_opts

  http requests are redirected to https for geolocation purposes

"""

import cloudinary.api
from cloudinary import Search
from mapdatabase import Database

from flask import Flask, request, make_response, render_template, redirect, json
from flask import url_for, abort, session

from common import get_view_type, validate_user, cloud_upload_photo, get_categories
from common import get_anon, get_dates, send_email, get_descrip, get_map_type

from CASClient import CASClient

import sys
# ----------------------------------------------------------------------------

app = Flask(__name__, template_folder='./templates/')
app.secret_key = ''
cloudinary.config(cloud_name="", api_key="",
                  api_secret="")

# ----------------------------------------------------------------------------

# redirect to https
@app.before_request
def before_request():
    if request.url.startswith('http://princeton'):
        url = request.url.replace('http://', 'https://', 1)
        code = 301
        return redirect(url, code=code)

# the default route -- display a page of pins (and username if logged in)
@app.route('/', methods=['GET'])
def index():
    netid = validate_user(request, session, False)
    status_msg = request.args.get('status_msg')
    warn_msg = request.args.get('warn_msg')
    view_type = get_view_type(request, netid)
    categories = get_categories(request)
    dates = get_dates(request)
    descrip = get_descrip(request)
    map_type = get_map_type(request)

    try:
        database = Database()
        database.connect()
        admin = database.isAdmin(netid)
        database.disconnect()

        html = render_template('index.html',
                               netid=netid, admin=admin, map_type=map_type,
                               view_type=view_type, curr_cat=categories,
                               dates=dates, descrip=descrip,
                               status_msg=status_msg, warn_msg=warn_msg)
        response = make_response(html)

        return response
    except Exception:
        return redirect(url_for('error'))


@app.route('/pin_results', methods=['GET'])
def pin_results():

    netid = validate_user(request, session, False)
    view_type = get_view_type(request, netid)
    descrip = request.args.get('descrip')
    dates = {'start_date': request.args.get('start_date'),
             'end_date': request.args.get('end_date')}
    categories = request.args.getlist('category')
    map_type = request.args.get('map_type')

    try:
        database = Database()
        database.connect()

        if netid and view_type == 'private':
            pins = database.getPinsFiltered(
                netid=netid, categories=categories, dates=dates, descrip=descrip)
        else:
            pins = database.getPinsFiltered(
                categories=categories, dates=dates, descrip=descrip)

        pinJS = []
        photoJS = []
        for pin in pins:
            pinJS.append(pin.getPinid())
            pinJS.append(pin.getX())
            pinJS.append(pin.getY())
            pinJS.append(pin.getDescrip())
            photos = database.getPhotos(pin.getPinid())
            pinJS.append(len(photos))

            # for the photos
            for photo in photos:
                photoJS.append(photo.getThumbnail())
                photoJS.append(photo.getDescription())
        database.disconnect()

        results = {'pins': pinJS, 'photos': photoJS}
        response = make_response(json.dumps(results))

        response.set_cookie('view_type', view_type)
        response.set_cookie('category', json.dumps(categories))
        response.set_cookie('dates', json.dumps(dates))
        response.set_cookie('descrip', descrip)
        response.set_cookie('map_type', map_type)
        return response

    except Exception:
        return redirect(url_for('error'))

# main tour page
@app.route('/tour', methods=['GET'])
def tour():
    netid = validate_user(request, session, False)
    status_msg = request.args.get('status_msg')
    warn_msg = request.args.get('warn_msg')

    # get pins from db
    try:
        database = Database()
        database.connect()

        pins = database.getAllPins()

        # for the map - make JSON pins/photos
        pinJS = []
        for pin in pins:
            pinJS.append(pin.getPinid())
            pinJS.append(pin.getX())
            pinJS.append(pin.getY())
            pinJS.append(pin.getDescrip())
        database.disconnect()

        pinJS = json.dumps(pinJS)

        # make response and return
        html = render_template('tour.html', pins=pins, pinsJS=pinJS,
                               netid=netid, status_msg=status_msg, warn_msg=warn_msg)
        response = make_response(html)
        return response
    except Exception:
        return redirect(url_for('error'))

# hidden page for adding pin to db + photo before redirecting to index
@app.route('/create_tour', methods=['POST'])
def create_tour():
    start = request.form.get('start')
    mid = []
    waypoints = []
    waypoints.append(request.form.getlist('waypoints'))
    for i in waypoints:
        mid.append(i)
    end = request.form.get('end')
    origin_x, origin_y = start.split()
    dest_x, dest_y = end.split()
    descrip = request.form.get('descrip')
    # add to db, go to preset tours and start with the one just added
    return redirect(url_for('preset_tour', mid=mid, origin_x=origin_x, origin_y=origin_y, dest_x=dest_x, dest_y=dest_y, descrip=descrip))

# viewing a preset tour
@app.route('/preset_tour', methods=['GET'])
def preset_tour():
    netid = validate_user(request, session, False)
    status_msg = request.args.get('status_msg')
    warn_msg = request.args.get('warn_msg')
    mid = request.args.get('mid')
    origin_x = request.args.get('origin_x')
    origin_y = request.args.get('origin_y')
    dest_x = request.args.get('dest_x')
    dest_y = request.args.get('dest_y')
    descrip = request.args.get('descrip')

    midJS = []
    if mid != None:
        temp = ""
        for i in mid:
            if i == '[' or i == "'" or i == ']':
                pass
            elif i == ',' or i == ' ':
                midJS.append(temp)
                temp = ""
            else:
                temp += i
        midJS.append(temp)
        i = 2
        while i < len(midJS):
            midJS.remove("")
            i += 3

    # get pins from db
    try:
        database = Database()
        database.connect()

        if origin_x != None:
            if len(midJS) == 2:
                tourid = database.addTour(
                    origin_x, origin_y, dest_x, dest_y, descrip, netid, midJS[0], midJS[1])
            elif len(midJS) == 4:
                tourid = database.addTour(
                    origin_x, origin_y, dest_x, dest_y, descrip, netid, midJS[0], midJS[1], midJS[2], midJS[3])
            elif len(midJS) == 6:
                tourid = database.addTour(origin_x, origin_y, dest_x, dest_y, descrip,
                                          netid, midJS[0], midJS[1], midJS[2], midJS[3], midJS[4], midJS[5])
            elif len(midJS) == 8:
                tourid = database.addTour(origin_x, origin_y, dest_x, dest_y, descrip, netid,
                                          midJS[0], midJS[1], midJS[2], midJS[3], midJS[4], midJS[5], midJS[6], midJS[7])
            elif len(midJS) == 10:
                tourid = database.addTour(origin_x, origin_y, dest_x, dest_y, descrip, netid,
                                          midJS[0], midJS[1], midJS[2], midJS[3], midJS[4], midJS[5], midJS[6], midJS[7], midJS[8], midJS[9])
            elif len(midJS) == 12:
                tourid = database.addTour(origin_x, origin_y, dest_x, dest_y, descrip, netid,
                                          midJS[0], midJS[1], midJS[2], midJS[3], midJS[4], midJS[5], midJS[6], midJS[7], midJS[8], midJS[9], midJS[10], midJS[11])
            else:
                tourid = database.addTour(
                    origin_x, origin_y, dest_x, dest_y, descrip, netid)
            status_msg = "Tour Saved!"
        tours = database.getAllTours()
        pins = database.getAllPins()

        # for the map - make JSON pins/photos
        pinJS = []
        photoJS = []
        tourJS = []
        for tour in tours:
            tourJS.append(tour.getLength())
            tourJS.append(tour.getTourID())
            tourJS.append(tour.getDescription())
            tourJS.append(tour.getOriginX())
            tourJS.append(tour.getOriginY())
            tourJS.append(tour.getDestX())
            tourJS.append(tour.getDestY())
            for i in range(1, int(tour.getLength()) - 1):
                if i == 1:
                    tourJS.append(tour.getX1())
                    tourJS.append(tour.getY1())
                elif i == 2:
                    tourJS.append(tour.getX2())
                    tourJS.append(tour.getY2())
                elif i == 3:
                    tourJS.append(tour.getX3())
                    tourJS.append(tour.getY3())
                elif i == 4:
                    tourJS.append(tour.getX4())
                    tourJS.append(tour.getY4())
                elif i == 5:
                    tourJS.append(tour.getX5())
                    tourJS.append(tour.getY5())
                elif i == 6:
                    tourJS.append(tour.getX6())
                    tourJS.append(tour.getY6())

        for pin in pins:
            pinJS.append(pin.getPinid())
            pinJS.append(pin.getX())
            pinJS.append(pin.getY())
            pinJS.append(pin.getDescrip())
            photos = database.getPhotos(pin.getPinid())
            pinJS.append(len(photos))

            # for the photos
            for photo in photos:
                photoJS.append(photo.getThumbnail())
                photoJS.append(photo.getDescription())
        database.disconnect()

        pinJS = json.dumps(pinJS)
        photoJS = json.dumps(photoJS)
        tourJS = json.dumps(tourJS)
        midJS = json.dumps(midJS)

        # make response and return
        html = render_template('preset_tour.html',
                               netid=netid, midJS=midJS, pinsJS=pinJS, photoJS=photoJS, tours=tours, tourJS=tourJS, status_msg=status_msg, warn_msg=warn_msg)
        response = make_response(html)
        return response
    except Exception:
        return redirect(url_for('error'))

# page for displaying photo of pin
@app.route('/photo', methods=['GET'])
def photo():
    pinid = request.args.get('pinid')
    netid = validate_user(request, session, False)
    view_type = get_view_type(request, netid)
    dates = get_dates(request)
    status_msg = request.args.get('status_msg')
    warn_msg = request.args.get('warn_msg')

    if pinid is None or pinid.strip() == "":
        return redirect(url_for('index', warn_msg="No pin found!"))

    # check view types
    params = {}
    if view_type == 'private' and netid is not None:
        params['netid'] = netid
    if dates:
        params['dates'] = dates

    # get photos for this pin
    try:
        photos = []
        database = Database()
        database.connect()
        photos = database.getPhotos(int(pinid), **params)

        # this pin does not exist
        if (photos is None or len(photos) == 0) and view_type != 'private':
            return redirect(url_for('index',
                                    warn_msg="This pin does not exist or contains no photos."))

        # get extra photo/pin information
        pin_descrip = database.getPin(pinid).getDescrip()
        if netid:
            for photo in photos:
                photo.setLiked(database.checkLike(photo.getPhotoId(), netid))
        database.disconnect()

        # make and return the response
        html = render_template('photo.html', photos=photos,
                               netid=netid, view_type=view_type, pinid=pinid,
                               status_msg=status_msg, warn_msg=warn_msg,
                               pin_descrip=pin_descrip)
        response = make_response(html)
        response.set_cookie('view_type', view_type)
        return response
    except Exception:
        return redirect(url_for('error'))

# page to input photo to upload
@app.route('/add_photo', methods=['GET'])
def add_photo():
    netid = validate_user(request, session)
    pinid = request.args.get('pinid')
    try:
        database = Database()
        database.connect()
        pin_descrip = database.getPin(pinid).getDescrip()
        database.disconnect()
        html = render_template('add_photo.html', pinid=pinid, netid=netid,
                               pin_descrip=pin_descrip)
        response = make_response(html)
        return response
    except Exception as e:
        print(str(e), sys.stderr)
        return redirect(url_for('error'))

# hidden page for uploading a photo
@app.route('/upload_photo', methods=['POST'])
def upload_photo():
    # get upload values
    netid = validate_user(request, session)
    pinid = request.form.get('pinid')
    description = request.form.get('descrip')
    img = request.files.get('img')
    categories = request.form.getlist('category')
    anon = get_anon(request)
    warn_msg = None
    status_msg = None

    # validate arguments
    if pinid is None:
        warn_msg = "Unable to add photo. Pin not found."
    if not img:
        warn_msg = "Unable to add photo. Photo not found."

    file_type = img.filename.split('.')[1]
    accepted_file_types = ['jpg', 'jpeg', 'jpe',
                           'png', 'bmp', 'tif', 'tiff', 'gif']
    if file_type not in accepted_file_types:
        return redirect(url_for('index',
                                warn_msg='Could not create pin. Your chosen file was not an image.'))

    if netid is None:
        warn_msg = "Unable to add photo. Username not found."

    try:
        if warn_msg is None:
            # upload to DB
            url, photo_id = cloud_upload_photo(img)
            database = Database()
            database.connect()
            database.addPhoto(pinid, photo_id, url, description,
                              netid, categories, anon)
            database.disconnect()
            status_msg = "Photo Uploaded!"
        return redirect(url_for('photo', warn_msg=warn_msg,
                                status_msg=status_msg, pinid=pinid))
    except Exception:
        return redirect(url_for('error'))

# hidden page for adding pin to db + photo before redirecting to index
@app.route('/create_pin', methods=['POST'])
def create_pin():
    # get info
    lat, lng = request.form.get('lat'), request.form.get('lng')
    pin_descrip = request.form.get('pin_descrip')
    img = request.files.get('img')
    img_descrip = request.form.get('descrip')
    categories = request.form.getlist('category')
    anon = get_anon(request)

    netid = validate_user(request, session)

    # server-side information checking (to doubly ensure we don't get any input errors)
    if not img:
        return redirect(url_for('index',
                                warn_msg='Could not create pin. No image chosen.'))

    file_type = img.filename.split('.')[1]
    accepted_file_types = ['jpg', 'jpeg', 'jpe',
                           'png', 'bmp', 'tif', 'tiff', 'gif']
    if file_type not in accepted_file_types:
        return redirect(url_for('index',
                                warn_msg='Could not create pin. Your chosen file was not an image.'))

    if len(lat) == 0 or len(lng) == 0:
        return redirect(url_for('index',
                                warn_msg='Could not create pin. Invalid coordinates.'))

    lat = float(lat)
    lng = float(lng)
    if lat > 40.3755 or lng < -74.7219 or lat < 40.32832 or lng > -74.6468:
        return redirect(url_for('index',
                                warn_msg='Could not create pin. Please choose somewhere near Princeton.'))

    if not pin_descrip or pin_descrip.strip() == "":
        return redirect(url_for('index',
                                warn_msg='Could not create pin. Please enter a description.'))

    try:
        # get the pins
        database = Database()
        database.connect()
        pins = database.getAllPins()

        for pin in pins:
            if abs(lat - pin.getX()) < 0.00005 and abs(lng - pin.getY()) < 0.00005:
                return redirect(url_for('add_pin',
                                        warn_msg='Could not create pin. Did you mean ' + pin.getDescrip() + '?'))

        # upload to db
        url, photo_id = cloud_upload_photo(img)
        pinid = database.addPin(lat, lng, pin_descrip, netid,
                                photo_id, url, img_descrip, categories, anon)
        database.disconnect()

        return redirect(url_for("photo", pinid=pinid, status_msg="Pin added!"))
    except Exception:
        return redirect(url_for('error'))

# page to input stuff for pin to upload
@app.route('/add_pin', methods=['GET'])
def add_pin():
    netid = validate_user(request, session)
    warn_msg = request.args.get('warn_msg')

    # get pins from db
    try:
        database = Database()
        database.connect()
        pins = database.getAllPins()

        # for the map - make JSON pins/photos
        pinJS = []
        for pin in pins:
            pinJS.append(pin.getPinid())
            pinJS.append(pin.getX())
            pinJS.append(pin.getY())
            pinJS.append(pin.getDescrip())
            photos = database.getPhotos(pin.getPinid())
            pinJS.append(len(photos))

        pinJS = json.dumps(pinJS)
        html = render_template('add_pin.html', pinsJS=pinJS,
                               netid=netid, warn_msg=warn_msg)
        response = make_response(html)
        return response
    except Exception:
        return redirect(url_for('error'))

# page for logging in
@app.route('/login', methods=['GET'])
def login():
    CASClient().authenticate()
    response = redirect(session.get('requesting_url'))
    session.pop('requesting_url')
    return response

# page to delete a photo
@app.route('/delete/<photo_id>', methods=['GET'])
def delete_photo(photo_id):
    pinid = request.args.get('pinid')
    status_msg = "Deleted!"
    try:
        database = Database()
        database.connect()
        cloudinary.api.delete_resources([photo_id])
        count = database.removePhoto(photo_id)
        database.disconnect()
        if count == 0:
            return redirect(url_for('index', status_msg="Photo and pin deleted!"))

        return redirect(url_for('photo', pinid=pinid, status_msg=status_msg))
    except Exception:
        return redirect(url_for('error'))

# hidden page for logout
@app.route('/logout', methods=['GET'])
def logout():
    casClient = CASClient()
    casClient.authenticate()
    response = casClient.logout()

    response.set_cookie('view_type', expires=0)
    response.set_cookie('category', expires=0)
    response.set_cookie('dates', expires=0)
    response.set_cookie('descrip', expires=0)
    return response

# toggles like on given photo
@app.route('/like', methods=['GET'])
def like():
    netid = validate_user(request, session)
    photo_id = request.args.get('photoid')
    ret_val = "liked"

    try:
        database = Database()
        database.connect()
        liked = database.checkLike(photo_id, netid)
        if liked:
            ret_val = "dislike"
            database.removeLike(photo_id, netid)
        else:
            database.like(photo_id, netid)
        database.disconnect()

        return ret_val
    except Exception:
        return redirect(url_for('error'))

# handles reported post
@app.route('/make_photo_report', methods=['GET'])
def make_photo_report():
    photo_id = request.args.get('photo_id')
    reason = request.args.get('reason')

    try:
        database = Database()
        database.connect()
        database.addPhotoReport(photo_id, reason)
        num_reports = len(database.getPhotoReports(photo_id))
        if num_reports >= 3:
            database.hidePhoto(photo_id)
        database.disconnect()

        # send email to admin
        msg_subject = '[PrincetonPlaces] A Post Has Been Reported'
        msg_body = '''A post has been reported.
                  Please click <a href="{0}admin/photo/{1}">here</a>
                  to view.'''.format(request.url_root, photo_id)
        send_email(msg_subject, msg_body)

        return "Success"
    except Exception:
        return redirect(url_for('error'))

# handles reported pin
@app.route('/make_pin_report', methods=['GET'])
def make_pin_report():
    pin_id = request.args.get('pin_id')
    reason = request.args.get('reason')

    try:
        database = Database()
        database.connect()
        database.addPinReport(pin_id, reason)
        num_reports = len(database.getPinReports(pin_id))
        if num_reports >= 3:
            database.hidePin(pin_id)
        database.disconnect()

        # send email to admin
        msg_subject = '[PrincetonPlaces] A Pin Has Been Reported'
        msg_body = '''A pin has been reported.
                  Please click <a href="{0}admin/pin?pinid={1}">here</a>
                  to view.'''.format(request.url_root, pin_id)
        send_email(msg_subject, msg_body)

        return "Success"
    except Exception:
        return redirect(url_for('error'))

# report-fetching hidden route
@app.route('/fetch_report_opts', methods=['GET'])
def fetch_report_opts():
    report_type = request.args.get('report_type')
    if report_type == 'photo':
        return make_response(render_template('report_photo_opts.html'))
    elif report_type == 'pin':
        return make_response(render_template('report_pin_opts.html'))
    else:
        return ('', 204)  # NO CONTENT

# route for altering photo description, categories, anon
@app.route('/make_edit/<photo_id>', methods=['POST'])
def make_edit(photo_id):
    netid = validate_user(request, session)
    new_descrip = request.form.get('descrip')
    new_categories = request.form.getlist('category')
    anon = get_anon(request)

    try:
        database = Database()
        database.connect()
        photo = database.getPhoto(photo_id)

        if netid != photo.getUser():
            return redirect(url_for('photo', pinid=photo.getPinid(),
                                    warn_msg="You don't have permission to edit this photo!"))

        database.editPhoto(photo_id, new_descrip, new_categories, anon)
        return redirect(url_for('photo', pinid=photo.getPinid(),
                                status_msg="Photo updated!"))
    except Exception:
        return redirect(url_for('error'))

# hidden page for editing the photo
@app.route('/edit_photo/<photo_id>', methods=['GET'])
def edit_form(photo_id):
    netid = validate_user(request, session)

    try:
        database = Database()
        database.connect()
        photo = database.getPhoto(photo_id)
        database.disconnect()

        if netid != photo.getUser():
            return redirect(url_for('photo', pinid=photo.getPinid(),
                                    warn_msg="You don't have permission to edit this photo!"))

        html = render_template('edit_photo.html', photo=photo,
                               curr_cat=photo.getCategories())
        response = make_response(html)
        return response
    except Exception:
        return redirect(url_for('error'))

# base admin page
@app.route('/admin', methods=['GET'])
def admin():
    netid = validate_user(request, session, False)
    status_msg = request.args.get('status_msg')
    warn_msg = request.args.get('warn_msg')

    try:
        database = Database()
        database.connect()

        if database.isAdmin(netid):
                # get pins from db
            pins = database.getAllPins(hidden=True)

            admins = database.getAdmins()

            database.disconnect()

            html = render_template('admin.html', pins=pins,
                                   admins=admins, netid=netid,)
            response = make_response(html)
            return response

        else:
            database.disconnect()
            warn_msg = 'You do not have permission to access the admin panel.'
            return redirect(url_for('index', warn_msg=warn_msg))
    except Exception:
        return redirect(url_for('error'))

# view a pin's information
@app.route('/admin/pin', methods=['GET'])
def admin_pin():
    netid = validate_user(request, session, False)
    pinid = request.args.get('pinid')

    try:
        database = Database()
        database.connect()

        if database.isAdmin(netid):

            pin = database.getPin(pinid)
            photos = database.getPhotos(pinid, hidden=True)
            reports = database.getPinReports(pinid)

            database.disconnect()

            html = render_template('admin_pin.html', pin=pin, pinid=pinid,
                                   photos=photos, netid=netid, reports=reports)
            response = make_response(html)
            return response

        else:
            database.disconnect()
            warn_msg = 'You do not have permission to access the admin panel.'
            return redirect(url_for('index', warn_msg=warn_msg))
    except Exception:
        return redirect(url_for('error'))

# allow the admin to edit a pin
@app.route('/adminEditPin/<pinid>', methods=['GET'])
def adminEditPin(pinid):
    netid = validate_user(request, session, False)

    try:
        database = Database()
        database.connect()

        if database.isAdmin(netid):

            x = request.args.get('x')
            y = request.args.get('y')
            description = request.args.get('description')
            time = request.args.get('time')
            user = request.args.get('user')

            status_msg = "Edited!"

            database.editPinAll(pinid, pinid, x,
                                y, description, time, user)
            database.disconnect()

            return redirect(url_for('admin_pin', pinid=pinid, status_msg=status_msg))

        else:
            database.disconnect()
            warn_msg = 'You do not have permission to access the admin panel.'
            return redirect(url_for('index', warn_msg=warn_msg))
    except Exception:
        return redirect(url_for('error'))

# view a photo
@app.route('/admin/photo/<photo_id>', methods=['GET'])
def admin_photo(photo_id):
    netid = validate_user(request, session, False)
    try:
        database = Database()
        database.connect()

        if database.isAdmin(netid):

            netid = validate_user(request, session, False)
            # pinid = request.args.get('pinid')
            photoid = photo_id

            photo = database.getPhoto(photoid)
            reports = database.getPhotoReports(photoid)

            database.disconnect()

            html = render_template('admin_photo.html',
                                   # pinid=pinid,
                                   photoid=photoid, photo=photo,
                                   netid=netid, curr_cat=photo.getCategories(),
                                   reports=reports)

            response = make_response(html)
            return response

        else:
            database.disconnect()
            warn_msg = 'You do not have permission to access the admin panel.'
            return redirect(url_for('index', warn_msg=warn_msg))
    except Exception:
        return redirect(url_for('error'))

# edit a photo
@app.route('/adminEditPhoto/<photo_id>', methods=['GET'])
def adminEditPhoto(photo_id):
    netid = validate_user(request, session, False)

    try:
        database = Database()
        database.connect()

        if database.isAdmin(netid):

            pinid = request.args.get('pinid')
            photoid = request.args.get('photoid')
            photoLink = request.args.get('photolink')
            description = request.args.get('description')
            time = request.args.get('time')
            user = request.args.get('user')
            anon = request.args.get('anon')
            anon = (anon != None)
            new_categories = request.args.getlist('category')

            status_msg = "Edited!"

            database.editPhotoAll(photo_id, pinid, photoid,
                                  photoLink, description, time, user, anon, new_categories)
            database.disconnect()

            return redirect(url_for('admin_pin', pinid=pinid, status_msg=status_msg))

        else:
            database.disconnect()
            warn_msg = 'You do not have permission to access the admin panel.'
            return redirect(url_for('index', warn_msg=warn_msg))
    except Exception:
        return redirect(url_for('error'))

# delete a photo
@app.route('/adminDeletePhoto/<photo_id>', methods=['GET'])
def admin_delete_photo(photo_id):
    netid = validate_user(request, session, False)
    try:
        database = Database()
        database.connect()

        if database.isAdmin(netid):
            pinid = request.args.get('pinid')
            status_msg = "Deleted!"
            cloudinary.api.delete_resources([photo_id])
            count = database.removePhoto(photo_id)
            database.disconnect()

            if count == 0:
                return redirect(url_for('admin', status_msg=status_msg))

            return redirect(url_for('admin_pin', pinid=pinid, status_msg=status_msg))

        else:
            database.disconnect()
            warn_msg = 'You do not have permission to access the admin panel.'
            return redirect(url_for('index', warn_msg=warn_msg))
    except Exception:
        return redirect(url_for('error'))

# delete a pin
@app.route('/adminDeletePin', methods=['GET'])
def admin_delete_pin():
    netid = validate_user(request, session, False)
    try:
        database = Database()
        database.connect()

        if database.isAdmin(netid):

            pinid = request.args.get('pinid')
            status_msg = "Deleted!"
            photos = database.getPhotos(pinid)

            for photo in photos:
                photo_id = photo.getPhotoId()
                cloudinary.api.delete_resources([photo_id])
                database.removePhoto(photo_id)

            database.removePin(pinid)

            database.disconnect()

            return redirect(url_for('admin', status_msg=status_msg))

        else:
            database.disconnect()
            warn_msg = 'You do not have permission to access the admin panel.'
            return redirect(url_for('index', warn_msg=warn_msg))
    except Exception:
        return redirect(url_for('error'))

# delete an admin
@app.route('/adminDeleteAdmin', methods=['GET'])
def adminDeleteAdmin():
    netid = validate_user(request, session, False)
    try:
        database = Database()
        database.connect()

        if database.isAdmin(netid):

            admin = request.args.get('admin')
            status_msg = "Deleted!"
            database.removeAdmin(admin)

            database.disconnect()

            return redirect(url_for('admin', status_msg=status_msg))

        else:
            database.disconnect()
            warn_msg = 'You do not have permission to access the admin panel.'
            return redirect(url_for('index', warn_msg=warn_msg))
    except Exception:
        return redirect(url_for('error'))

# route for adding a new admin
@app.route('/adminAddAdmin/', methods=['GET'])
def adminAddAdmin():
    netid = validate_user(request, session, False)

    try:
        database = Database()
        database.connect()

        if database.isAdmin(netid):
            newAdmin = request.args.get('newAdmin')

            status_msg = "Created new admin!!"

            database = Database()
            database.connect()
            database.addAdmin(newAdmin)
            database.disconnect()

            return redirect(url_for('admin', status_msg=status_msg))

        else:
            database.disconnect()
            warn_msg = 'You do not have permission to access the admin panel.'
            return redirect(url_for('index', warn_msg=warn_msg))
    except Exception:
        return redirect(url_for('error'))

# delete photo report
@app.route('/adminDeletePhotoReport', methods=['GET'])
def admin_delete_photo_report():
    netid = validate_user(request, session, False)

    try:
        database = Database()
        database.connect()

        if database.isAdmin(netid):

            report_id = request.args.get('reportid')

            database.deletePhotoReport(report_id)
            database.disconnect()

            return "Success"

        else:
            database.disconnect()
            warn_msg = 'You do not have permission to access the admin panel.'
            return redirect(url_for('index', warn_msg=warn_msg))

    except Exception:
        return redirect(url_for('error'))

# delete pin report
@app.route('/adminDeletePinReport', methods=['GET'])
def admin_delete_pin_report():
    netid = validate_user(request, session, False)

    try:
        database = Database()
        database.connect()

        if database.isAdmin(netid):

            report_id = request.args.get('reportid')
            database.deletePinReport(report_id)
            database.disconnect()
            return "Success"

        else:
            database.disconnect()
            warn_msg = 'You do not have permission to access the admin panel.'
            return redirect(url_for('index', warn_msg=warn_msg))

    except Exception:
        return redirect(url_for('error'))

# toggle hidden status of photo
@app.route('/adminTogglePhotoHidden', methods=['GET'])
def admin_toggle_photo_hidden():
    netid = validate_user(request, session, False)

    try:
        database = Database()
        database.connect()

        if database.isAdmin(netid):

            photo_id = request.args.get('photoid')
            action = request.args.get('action')

            if action == 'hide':
                database.hidePhoto(photo_id)
            elif action == 'show':
                database.unhidePhoto(photo_id)

            database.disconnect()
            return "Success"

        else:
            warn_msg = 'You do not have permission to access the admin panel.'
            database.disconnect()
            return redirect(url_for('index', warn_msg=warn_msg))

    except Exception:
        return redirect(url_for('error'))


# toggle hidden status of pin
@app.route('/adminTogglePinHidden', methods=['GET'])
def admin_toggle_pin_hidden():
    netid = validate_user(request, session, False)

    try:
        database = Database()
        database.connect()

        if database.isAdmin(netid):

            pin_id = request.args.get('pinid')
            action = request.args.get('action')

            if action == 'hide':
                database.hidePin(pin_id)
            elif action == 'show':
                database.unhidePin(pin_id)

            database.disconnect()

            return "Success"

        else:
            database.disconnect()
            warn_msg = 'You do not have permission to access the admin panel.'
            return redirect(url_for('index', warn_msg=warn_msg))

    except Exception:
        return redirect(url_for('error'))

# route for liked photos
@app.route('/liked_photos', methods=['GET'])
def liked_photos():
    netid = validate_user(request, session, False)

    if not netid:
        return redirect(url_for('index', warn_msg="You are not logged in. Log in to view liked photos."))

    view_type = get_view_type(request, netid)
    dates = get_dates(request)
    status_msg = request.args.get('status_msg')
    warn_msg = request.args.get('warn_msg')

    # check view types
    params = {}
    if dates:
        params['dates'] = dates

    # get photos for this pin
    try:
        photos = []
        database = Database()
        database.connect()
        photos = database.getUserLikedPhotos(netid)

        # this pin does not exist
        if (photos is None or len(photos) == 0):
            return redirect(url_for('index',
                                    warn_msg="You have not liked any photos yet!"))

        # get extra photo/pin information
        for photo in photos:
            photo.setLiked(database.checkLike(photo.getPhotoId(), netid))
        database.disconnect()

        # make and return the response
        html = render_template('photo_liked.html', photos=photos,
                               netid=netid, view_type=view_type,
                               status_msg=status_msg, warn_msg=warn_msg)
        response = make_response(html)
        response.set_cookie('view_type', view_type)
        return response
    except Exception:
        return redirect(url_for('error'))

# page for general errors
@app.route('/error', methods=['GET'])
def error():
    html = render_template('error_page.html',
                           warn_msg="An error occurred. Please contact a system administrator (evuong, dbooth, jt22, or rraghu @princeton.edu).")
    response = make_response(html)
    return response
