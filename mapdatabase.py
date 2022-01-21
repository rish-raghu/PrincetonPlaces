#!/usr/bin/env python
"""
db_methods.py

This class provides functionality used for altering the database. We opted to
not use SQL Alchemy, although this class operates similarly.

API:
* Database              ()

* connect               (db_name: string = "mapdb")

* disconnect            ()

* getPhotos             (pinid: int,                      -> photos: Photo[]
                         netid: string = None, 
                         dates: dict = None
                         hidden: boolean = False)  

* getPhoto              (photo_id: string)                -> photo: Photo

* getAllPhotos          (hidden: boolean = False)         -> photos: Photo[]

* addPhoto              (pinid: int,
                         photo_id: string,
                         photo: string,
                         description: string,
                         netid: string,
                         categories: string[],
                         anon: boolean)

* addPin                (x: float, y: float,              -> pinid: int
                         description: string,
                         netid: string,
                         photo_id: string,
                         photo: string,
                         photo_descrip: string,
                         categories: string[],
                         anon: boolean)

* editPhoto             (photo_id: string,
                         new_descrip: string,
                         new_categories: string[],
                         anon: bool = False)

* removePhoto           (photo_id: string)                -> count: int

* removePhotosFromPin   (pinid: int)

* getAllPins            (hidden: boolean = False)         -> pins: Pin[]

* getPinsFiltered       (netid: string = None,            -> pins: Pin[]
                         categories: string[] = None,
                         dates: dict = None,
                         descrip: string = "",
                         hidden: boolean = False)

* getPin                (pinid: int)                      -> pin: Pin

* removePin             (pinid: int)

* checkLike             (photo_id: string,                -> liked: boolean
                        netid: string)

* like                  (photo_id: string,
                         netid: string)

* removeLike            (photo_id: string,
                         netid: string)

* addPhotoReport        (photo_id: string,                -> report_id: int
                         reason: string)

* getPhotoReports       (photo_id: string)                -> reports: PhotoReport[]

* deletePhotoReport     (report_id: int)

* hidePhoto             (photo_id: string)

* unhidePhoto           (photo_id: string)

* addPinReport          (pinid: int,                     -> report_id: int
                         reason: string)

* getPinReports         (pinid: int)                     -> reports: PinReport[]

* deletePinReport       (report_id: int)

* hidePin               (pinid: int)

* unhidePin             (pinid: int)
"""
from os import path, environ
from objects import Photo, Pin, Tour
from psycopg2 import connect
from objects import Photo, Pin, PhotoReport, PinReport, Tour


DATABASE_URL = environ.get('DATABASE_URL')

# class for connecting to database, editing


class Database(object):
    def __init__(self):
        self._connection = None

    # connect
    def connect(self, db_name=""):
        # runs locally
        if DATABASE_URL is None or DATABASE_URL is '127.0.0.1':
            self._connection = connect(
                database=db_name, user="", password="",
                host='', port="")

        # for heroku
        else:
            self._connection = connect(DATABASE_URL, sslmode='require')

    # disconnect
    def disconnect(self):
        self._connection.close()

    # get photos from a pin with pinid and optional netid
    def getPhotos(self, pinid, netid=None, dates=None, hidden=False):
        try:
            cursor = self._connection.cursor()
            QUERY_STRING = "SELECT * FROM photos WHERE pinid=%s"
            VALUES = [pinid]

            # filtering options for photos
            if netid is not None:
                QUERY_STRING += " AND netid=%s"
                VALUES.append(netid)

            if dates and dates['start_date']:
                QUERY_STRING += " AND photos.time >= %s"
                VALUES.append(dates['start_date'])

            if dates and dates['end_date']:
                QUERY_STRING += " AND photos.time <= %s"
                VALUES.append(dates['end_date'])

            if not hidden:
                QUERY_STRING += " AND photos.hidden=false"

            QUERY_STRING += " ORDER BY likes DESC"
            cursor.execute(QUERY_STRING, tuple(VALUES))

        except Exception as e:
            print(str(e))
            exit(1)

        # create the photos list
        photos = []
        all_rows = cursor.fetchall()
        for row in all_rows:
            photo_id = row[1]
            QUERY_STRING = "SELECT category FROM categories WHERE photo_id=%s"
            cursor.execute(QUERY_STRING, (photo_id,))
            categories = cursor.fetchall()
            categories = [category[0] for category in categories]
            photo = Photo(*row, categories=categories)
            photos.append(photo)
        cursor.close()
        return photos

    # get photos from a photoid
    def getPhoto(self, photo_id):
        try:
            # get photo
            cursor = self._connection.cursor()
            QUERY_STRING = "SELECT * FROM photos WHERE photo_id=%s"
            cursor.execute(QUERY_STRING, (photo_id,))
            photoArgs = cursor.fetchone()

            # get categories
            QUERY_STRING = "SELECT category FROM categories WHERE photo_id=%s"
            cursor.execute(QUERY_STRING, (photo_id,))
            categories = [category[0] for category in cursor.fetchall()]
            photo = Photo(*photoArgs, categories=categories)
            cursor.close()

        except Exception as e:
            print(str(e))
            exit(1)

        return photo

    # get all photos
    def getAllPhotos(self, hidden=False):
        try:
            cursor = self._connection.cursor()
            QUERY_STRING = "SELECT * FROM photos"

            if not hidden:
                QUERY_STRING += " WHERE hidden=false"

            QUERY_STRING += " ORDER BY likes DESC"
            cursor.execute(QUERY_STRING)

        except Exception as e:
            print(str(e))
            exit(1)

        # create the photos list
        photos = []
        all_rows = cursor.fetchall()
        for row in cursor:
            photo_id = row[1]
            QUERY_STRING = "SELECT category FROM categories WHERE photo_id=%s"
            cursor.execute(QUERY_STRING, (photo_id,))
            categories = cursor.fetchall()
            categories = [category[0] for category in categories]
            photo = Photo(*row, categories=categories)
            photos.append(photo)
        cursor.close()
        return photos

    # get all tours
    def getAllTours(self, hidden=False):
        try:
            cursor = self._connection.cursor()
            QUERY_STRING = "SELECT * FROM tours"
            cursor.execute(QUERY_STRING)

        except Exception as e:
            print(str(e))
            exit(1)

        # create the tours list
        tours = []
        for row in cursor:
            tour = Tour(*row)
            tours.append(tour)
        cursor.close()
        return tours

    # adds a photo to the db
    def addPhoto(self, pinid, photo_id, photo, description, netid, categories, anon):

        try:
            QUERY_STRING_PHOTO = ("INSERT INTO photos (pinid, photo_id, photo, description, time, "
                                  "netid, anon) VALUES (%s, %s, %s, %s, CURRENT_DATE, %s, %s)")

            cursor = self._connection.cursor()
            cursor.execute(QUERY_STRING_PHOTO, (pinid, photo_id,
                                                photo, description, netid, anon))

            # adding categories
            if categories is not None and len(categories) != 0:
                QUERY_STRING_CAT = (
                    "INSERT INTO categories (photo_id, category) VALUES (%s, %s)")
                val = []
                for category in categories:
                    val.append((photo_id, category))
                cursor.executemany(QUERY_STRING_CAT, val)

        except Exception as e:
            print(str(e))
            exit(1)
        self._connection.commit()
        cursor.close()

    # add a pin with defaulted pinid, add photo, returns the pinid
    def addPin(self, x, y, description, netid, photo_id, photo, photo_descrip, categories, anon):

        try:
            # create the pin
            QUERY_STRING = ("INSERT INTO pins (x, y, description, time, netid ) " +
                            "VALUES (%s, %s, %s, CURRENT_DATE, %s) RETURNING pinid")
            cursor = self._connection.cursor()
            cursor.execute(QUERY_STRING, (x, y, description, netid))
            pinid = cursor.fetchone()

        except Exception as e:
            print(str(e))
            exit(1)

        self._connection.commit()
        cursor.close()

        # add the photo
        self.addPhoto(pinid, photo_id, photo, photo_descrip,
                      netid, categories, anon)

        return pinid
    
    # add a tour
    def addTour(self, origin_x, origin_y, dest_x, dest_y, descript, netid, x1 = 0, y1 = 0, x2 = 0, y2 = 0, x3 = 0, y3 = 0, x4 = 0, y4 = 0, x5 = 0, y5 = 0, x6 = 0, y6 = 0):
        try:
            # create the pin
            QUERY_STRING = ("INSERT INTO tours (origin_x, origin_y, dest_x, dest_y, descript, netid, x1, y1, x2, y2, x3, y3, x4, y4, x5, y5, x6, y6) " +
                            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING tourid")
            cursor = self._connection.cursor()
            cursor.execute(QUERY_STRING, (origin_x, origin_y, dest_x, dest_y, descript, netid, x1, y1, x2, y2, x3, y3, x4, y4, x5, y5, x6, y6))
            tourid = cursor.fetchone()

        except Exception as e:
            print(str(e))
            exit(1)

        self._connection.commit()
        cursor.close()

        return tourid

    # edit photo by photo id
    def editPhoto(self, photo_id, new_descrip, new_categories, anon=False):
        try:
            QUERY_STRING = ("UPDATE photos "
                            "SET "
                            "description=%s, "
                            "anon=%s "
                            "WHERE photo_id=%s ")
            cursor = self._connection.cursor()
            cursor.execute(QUERY_STRING, (new_descrip, anon, photo_id))

            # remove existing categories
            QUERY_STRING = ("DELETE FROM categories WHERE photo_id=%s")
            cursor.execute(QUERY_STRING, (photo_id,))

            # add categories back
            if new_categories is not None and len(new_categories) != 0:
                QUERY_STRING_CAT = (
                    "INSERT INTO categories (photo_id, category) VALUES (%s, %s)")
                val = []
                for category in new_categories:
                    val.append((photo_id, category))
                cursor.executemany(QUERY_STRING_CAT, val)

        except Exception as e:
            print(str(e))
            exit(1)

        self._connection.commit()
        cursor.close()

    # remove photo by photo id
    def removePhoto(self, photo_id):
        try:
            QUERY_STRING = (
                "DELETE FROM photos WHERE photo_id=%s RETURNING pinid")
            cursor = self._connection.cursor()
            cursor.execute(QUERY_STRING, (photo_id,))
            pinid = cursor.fetchone()
            QUERY_STRING = ("DELETE FROM categories WHERE photo_id=%s")
            cursor.execute(QUERY_STRING, (photo_id,))
            QUERY_STRING = ("DELETE FROM photo_reports WHERE photo_id=%s")
            cursor.execute(QUERY_STRING, (photo_id,))
            QUERY_STRING = ("DELETE FROM likes WHERE photo_id=%s")
            cursor.execute(QUERY_STRING, (photo_id,))
            self._connection.commit()

            # delete pin if no more photos
            QUERY_STRING = ("SELECT COUNT(*) FROM photos WHERE pinid=%s")
            cursor.execute(QUERY_STRING, (pinid,))
            count, = cursor.fetchone()
            cursor.close()

            # if the pin is now empty delete it
            if count == 0:
                self.removePin(pinid)
            return count
        except Exception as e:
            print(str(e))
            exit(1)

    # remove photos from a pin by pinid
    def removePhotosFromPin(self, pinid):
        try:
            QUERY_STRING = ("DELETE FROM photos WHERE pinid=%s")
            cursor = self._connection.cursor()
            cursor.execute(QUERY_STRING, [pinid])
        except Exception as e:
            print(str(e))
            exit(1)
        self._connection.commit()
        cursor.close()

    # get all pins
    def getAllPins(self, hidden=False):
        try:
            cursor = self._connection.cursor()
            QUERY_STRING = "SELECT * FROM pins"
            if not hidden:
                QUERY_STRING += " WHERE hidden=false"
            cursor.execute(QUERY_STRING)
        except Exception as e:
            print(str(e))
            exit(1)

        # create pins list
        pins = []
        for row in cursor:
            pin = Pin(*row)
            pins.append(pin)
        cursor.close()
        return pins

    # get pins with filtering options
    def getPinsFiltered(self, netid=None, categories=None, dates=None, descrip="", hidden=False):
        try:
            cursor = self._connection.cursor()
            QUERY_STRING = "SELECT * FROM pins"

            filterStrings = []
            values = []

            # user-specific
            if netid is not None:
                filterStrings.append("photos.netid=%s")
                values.append(netid)

            # category filtering
            if categories is not None and len(categories) > 0:
                TEMP_QUERY = "CREATE TEMP TABLE lookup (category TEXT)"
                cursor.execute(TEMP_QUERY)
                TEMP_QUERY = "INSERT INTO lookup (category) VALUES (%s)"
                cursor.executemany(TEMP_QUERY, [(cat,) for cat in categories])
                filterStrings.append("EXISTS (SELECT * FROM ((SELECT category FROM \
                categories WHERE categories.photo_id=photos.photo_id) INTERSECT (SELECT * FROM lookup)) AS deriv)")

            # date filtering
            if dates:
                if dates['start_date']:
                    filterStrings.append("photos.time >= %s")
                    values.append(dates['start_date'])
                if dates['end_date']:
                    filterStrings.append("photos.time <= %s")
                    values.append(dates['end_date'])

            # at least one visible photo
            filterStrings.append("photos.hidden=false")

            if len(filterStrings) > 0:
                QUERY_STRING += " WHERE pins.pinid IN \
                (SELECT photos.pinid FROM photos WHERE "
                QUERY_STRING += (" AND ".join(filterStrings) + ")")

            # pin visibility
            if not hidden:
                QUERY_STRING += " AND pins.hidden=false"

            # pin description filtering
            if descrip:
                QUERY_STRING += " AND pins.description ILIKE %s"
                values.append('%' + str(descrip).lower().replace('%','\%').replace('_', '\_') + '%')
           
            cursor.execute(QUERY_STRING, tuple(values))
        except Exception as e:
            print(str(e))
            exit(1)

        # create the list of pins
        pins = []
        for row in cursor:
            pin = Pin(*row)
            pins.append(pin)
        self._connection.commit()
        cursor.close()
        return pins

    # get single pin
    def getPin(self, pinid):
        try:
            cursor = self._connection.cursor()
            QUERY_STRING = "SELECT * FROM pins WHERE pinid=%s"
            cursor.execute(QUERY_STRING, [pinid])
            args = cursor.fetchone()
            if args is None or len(args) is 0:
                return None
            pin = Pin(*args)

        except Exception as e:
            print(str(e))
            exit(1)

        cursor.close()
        return pin

    # delete pin -- does not delete associated photos!
    def removePin(self, pinid):
        try:
            QUERY_STRING = ("DELETE FROM pins WHERE pinid=%s")
            cursor = self._connection.cursor()
            cursor.execute(QUERY_STRING, [pinid])
            QUERY_STRING = ("DELETE FROM pin_reports WHERE pinid=%s")
            cursor.execute(QUERY_STRING, [pinid])
            self._connection.commit()
            cursor.close()
        except Exception as e:
            print(str(e))
            exit(1)

    # check if a photo has been liked by a person (return true if is, false
    # otherwise)
    def checkLike(self, photo_id, netid):
        try:
            QUERY_STRING = ("SELECT COUNT(*) FROM likes WHERE photo_id=%s " +
                            "AND netid=%s")
            cursor = self._connection.cursor()
            cursor.execute(QUERY_STRING, (photo_id, netid))
            val = cursor.fetchone()[0]
            cursor.close()
            return val
        except Exception as e:
            print(str(e))
            exit(1)

    # like a photo (like a photo if not already liked)

    def like(self, photo_id, netid):
        try:
            # check if already liked, return
            liked = self.checkLike(photo_id, netid)
            if liked:
                return

            QUERY_STRING = (
                "INSERT INTO likes (photo_id, netid) VALUES (%s, %s)")
            cursor = self._connection.cursor()
            cursor.execute(QUERY_STRING, (photo_id, netid))

            QUERY_STRING = ("UPDATE photos SET likes=" +
                            "(SELECT likes FROM photos WHERE photo_id=%s) + 1 " +
                            "WHERE photo_id=%s")
            cursor.execute(QUERY_STRING, (photo_id, photo_id))
            self._connection.commit()
            cursor.close()
        except Exception as e:
            print(str(e))
            exit(1)

    # unlike a photo (if currently liked otherwise do nothing)
    def removeLike(self, photo_id, netid):
        try:
            # check if liked, if not return
            liked = self.checkLike(photo_id, netid)
            if not liked:
                return

            QUERY_STRING = ("DELETE FROM likes WHERE photo_id=%s AND netid=%s")
            cursor = self._connection.cursor()
            cursor.execute(QUERY_STRING, (photo_id, netid))

            QUERY_STRING = ("UPDATE photos SET likes=" +
                            "(SELECT likes FROM photos WHERE photo_id=%s) - 1 " +
                            "WHERE photo_id=%s")
            cursor.execute(QUERY_STRING, (photo_id, photo_id))
            self._connection.commit()
            cursor.close()
        except Exception as e:
            print(str(e))
            exit(1)

    # Get all photos a given user has liked
    def getUserLikedPhotos(self, netid):
        try:
            QUERY_STRING = ("SELECT photo_id FROM likes WHERE netid=%s")

            cursor = self._connection.cursor()
            cursor.execute(QUERY_STRING, (netid,))
            photoIDs = []
            for row in cursor:
                photoIDs.append(row[0])

            photos = []
            for photoID in photoIDs:
                QUERY_STRING = ("SELECT * FROM photos WHERE photo_id=%s")
                cursor.execute(QUERY_STRING, (photoID,))
                row = cursor.fetchone()

                QUERY_STRING = (
                    "SELECT category FROM categories WHERE photo_id=%s")
                cursor.execute(QUERY_STRING, (photoID,))
                categories = cursor.fetchall()
                categories = [category[0] for category in categories]
                photo = Photo(*row, categories=categories)
                photos.append(photo)

            cursor.close()
            return photos


        except Exception as e:
            print(str(e))
            exit(1)
            
            
    # add photo report for provided photo ID and reason, returning report ID
    def addPhotoReport(self, photo_id, reason):
        try:
            QUERY_STRING = ("INSERT INTO photo_reports (photo_id, reason, time_filed) " +
                            "VALUES (%s, %s, CURRENT_TIMESTAMP) RETURNING report_id")
            cursor = self._connection.cursor()
            cursor.execute(QUERY_STRING, (photo_id, reason))
            report_id = cursor.fetchone()

            self._connection.commit()
            cursor.close()
            return report_id
                      
        except Exception as e:
            print(str(e))
            exit(1)


    # get photo reports by photo ID
    def getPhotoReports(self, photo_id):
        try:
            QUERY_STRING = "SELECT * FROM photo_reports WHERE photo_id=%s \
                ORDER BY time_filed DESC"
            cursor = self._connection.cursor()
            cursor.execute(QUERY_STRING, (photo_id,))
            rows = cursor.fetchall()
        
        except Exception as e:
            print(str(e))
            exit(1)
        
        self._connection.commit()
        cursor.close()

        reports = []
        for row in rows:
            reports.append(PhotoReport(*row))

        return reports

    # delete photo report by report ID
    def deletePhotoReport(self, report_id):
        try:
            QUERY_STRING = "DELETE FROM photo_reports WHERE report_id=%s"
            cursor = self._connection.cursor()
            cursor.execute(QUERY_STRING, (report_id,))
            self._connection.commit()

        except Exception as e:
            print(str(e))
            exit(1)

    # hide photo by photo ID
    def hidePhoto(self, photo_id):
        try:
            QUERY_STRING = "UPDATE photos SET hidden=true WHERE photo_id=%s"
            cursor = self._connection.cursor()
            cursor.execute(QUERY_STRING, (photo_id,))
            self._connection.commit()
            
        except Exception as e:
            print(str(e))
            exit(1)
            
    # unhide photo by photo ID
    def unhidePhoto(self, photo_id):
        try:
            QUERY_STRING = "UPDATE photos SET hidden=false WHERE photo_id=%s"
            cursor = self._connection.cursor()
            cursor.execute(QUERY_STRING, (photo_id,))
            self._connection.commit()
            
        except Exception as e:
            print(str(e))
            exit(1)

    # add pin report for provided pin ID and reason, returning report ID
    def addPinReport(self, pinid, reason):
        try:
            QUERY_STRING = ("INSERT INTO pin_reports (pinid, reason, time_filed) " +
                            "VALUES (%s, %s, CURRENT_TIMESTAMP) RETURNING report_id")
            cursor = self._connection.cursor()
            cursor.execute(QUERY_STRING, (pinid, reason))
            report_id = cursor.fetchone()

            self._connection.commit()
            cursor.close()
            return report_id
            
        except Exception as e:
            print(str(e))
            exit(1)

    # get pin reports by pin ID
    def getPinReports(self, pinid):
        try:
            QUERY_STRING = "SELECT * FROM pin_reports WHERE pinid=%s \
                ORDER BY time_filed DESC"
            cursor = self._connection.cursor()
            cursor.execute(QUERY_STRING, (pinid,))
            rows = cursor.fetchall()
        
        except Exception as e:
            print(str(e))
            exit(1)
        
        self._connection.commit()
        cursor.close()

        reports = []
        for row in rows:
            reports.append(PinReport(*row))

        return reports

    # delete pin report by report ID
    def deletePinReport(self, report_id):
        try:
            QUERY_STRING = "DELETE FROM pin_reports WHERE report_id=%s"
            cursor = self._connection.cursor()
            cursor.execute(QUERY_STRING, (report_id,))
            self._connection.commit()

        except Exception as e:
            print(str(e))
            exit(1)

    # hide pin by pin ID
    def hidePin(self, pinid):
        try:
            QUERY_STRING = "UPDATE pins SET hidden=true WHERE pinid=%s"
            cursor = self._connection.cursor()
            cursor.execute(QUERY_STRING, (pinid,))
            self._connection.commit()
            
        except Exception as e:
            print(str(e))
            exit(1)
            
    # unhide pin by pin ID
    def unhidePin(self, pinid):
        try:
            QUERY_STRING = "UPDATE pins SET hidden=false WHERE pinid=%s"
            cursor = self._connection.cursor()
            cursor.execute(QUERY_STRING, (pinid,))
            self._connection.commit()
            
        except Exception as e:
            print(str(e))
            exit(1)

    
    def addAdmin(self, netid):
        try:
            QUERY_STRING = (
                "INSERT INTO admins VALUES (%s)")

            cursor = self._connection.cursor()
            cursor.execute(QUERY_STRING, (netid,))

        except Exception as e:
            print(str(e))
            exit(1)

        self._connection.commit()
        cursor.close()

        return

    def removeAdmin(self, netid):

        try:
            QUERY_STRING = ("DELETE FROM admins WHERE netid=%s")
            cursor = self._connection.cursor()
            cursor.execute(QUERY_STRING, [netid])
            self._connection.commit()
            cursor.close()
        except Exception as e:
            print(str(e))
            exit(1)
        return

    def isAdmin(self, netid):

        isAdmin = False

        try:
            QUERY_STRING = ("SELECT * FROM admins WHERE netid=%s")
            cursor = self._connection.cursor()
            cursor.execute(QUERY_STRING, [netid])
            row = cursor.fetchone()

            if row is not None:
                isAdmin = True

            cursor.close()

        except Exception as e:
            print(str(e))
            exit(1)

        return isAdmin

    def getAdmins(self):

        try:
            cursor = self._connection.cursor()
            QUERY_STRING = "SELECT * FROM admins"
            cursor.execute(QUERY_STRING)
        except Exception as e:
            print(str(e))
            exit(1)

        admins = []
        for row in cursor:
            admins.append(row[0])

        cursor.close()
        return admins

    def editPinAll(self, pinid, newPinid, newX, newY, newDescription, newTime, newNetid):
        try:
            QUERY_STRING = (
                "UPDATE pins SET pinid=%s, X=%s, Y=%s, description=%s, time=%s, netid=%s WHERE pinid=%s")
            cursor = self._connection.cursor()
            cursor.execute(QUERY_STRING, (newPinid, newX,
                                          newY, newDescription, newTime, newNetid, pinid))

        except Exception as e:
            print(str(e))
            exit(1)

        self._connection.commit()
        cursor.close()

    def editPhotoAll(self, photo_id, newPinid, newPhotoid, newPhotoLink, newDescription, newTime, newNetid, newAnon, newCategories):
        try:
            QUERY_STRING = (
                "UPDATE photos SET pinid=%s, photo_id=%s, photo=%s, description=%s, time=%s, netid=%s, anon=%s WHERE photo_id=%s")
            cursor = self._connection.cursor()
            cursor.execute(QUERY_STRING, (newPinid, newPhotoid,
                                          newPhotoLink, newDescription, newTime, newNetid, newAnon, photo_id))

            # remove existing categories
            QUERY_STRING = ("DELETE FROM categories WHERE photo_id=%s")
            cursor.execute(QUERY_STRING, (photo_id,))

            # add categories back
            if newCategories is not None and len(newCategories) != 0:
                QUERY_STRING_CAT = (
                    "INSERT INTO categories (photo_id, category) VALUES (%s, %s)")
                val = []
                for category in newCategories:
                    val.append((newPhotoid, category))
                cursor.executemany(QUERY_STRING_CAT, val)

        except Exception as e:
            print(str(e))
            exit(1)
        self._connection.commit()
        cursor.close()

