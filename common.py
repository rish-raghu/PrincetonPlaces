#!/usr/bin/env python

"""
common.py
Shared methods for app.py
"""

import cloudinary.uploader
from flask import request, session, json
from CASClient import CASClient
import smtplib
from email.message import EmailMessage
from email.mime.text import MIMEText

# gets the view type
def get_view_type(request, netid):
  # determine whether all pins or user's pins should be shown
  if 'view_type' in request.args and netid is not None:
      view_type = request.args.get('view_type')
  elif 'view_type' in request.cookies and netid is not None:
      view_type = request.cookies.get('view_type')
  else:
      view_type = 'all'

  return view_type

# gets category list
def get_categories(request):
  if 'category' in request.args:
      categories = request.args.getlist('category')
      # remove final 'NA' element, leaving empty list if no categories selected
      categories.pop() 
  elif 'category' in request.cookies:
      categories = json.loads(request.cookies.get('category'))
  else:
      categories = []

  return categories

# gets dates and returns as dictionary
def get_dates(request):
  dates={}
  if 'start_date' in request.args:
    dates['start_date'] = request.args.get('start_date')
    dates['end_date'] = request.args.get('end_date')
  elif 'dates' in request.cookies:
    dates = json.loads(request.cookies.get('dates'))
  return dates

# gets searched pin description
def get_descrip(request):
  if 'descrip' in request.args:
      descrip = request.args.get('descrip')
  elif 'descrip' in request.cookies:
      descrip = request.cookies.get('descrip')
  else:
      descrip = ''

  return descrip

# get map type: gmaps or arcmap
def get_map_type(request):
  if 'map_type' in request.args:
      descrip = request.args.get('map_type')
  elif 'map_type' in request.cookies:
      descrip = request.cookies.get('map_type')
  else:
      descrip = 'gmap'

  return descrip

# gets the user's username & authenticates
def validate_user(request, session, auth=True):
  # get user info
  if auth:
    CASClient().authenticate()
  netid = session.get('netid')
  return netid.strip() if netid else netid

# upload photo to cloudinary and return url, photo_id
def cloud_upload_photo(img):
  result = cloudinary.uploader.upload(img)
  url = result["url"]
  photo_id = result["public_id"]
  return url, photo_id

# returns true/false depending on anon value
def get_anon(request):
  anon = request.form.get('anon')
  return anon != None

# send email to admins
def send_email(msg_subject, msg_body):
  msg = MIMEText(msg_body, 'html')
  msg['To'] = ''
  msg['From'] = ''
  msg['Subject'] = msg_subject
  s = smtplib.SMTP('smtp.gmail.com', 587)
  s.starttls()
  s.login('', '')
  s.send_message(msg) 
  s.quit()
