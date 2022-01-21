"""
File of objects that will make displaying info easier (hopefully)
"""
import re


class Pin(object):

    def __init__(self, pinid, x, y, description, time, netid, hidden=False):
        self._pinid = int(pinid)
        self._x = float(x)
        self._y = float(y)
        self._description = description
        self._time = time
        self._netid = netid
        self._hidden = hidden

    def getPinid(self):
        return self._pinid

    def getX(self):
        return self._x

    def getY(self):
        return self._y

    def getDescrip(self):
        return self._description

    def getTime(self):
        return self._time

    def getNetid(self):
        return self._netid

    def getHidden(self):
        return self._hidden

    def toString(self):
        return(self._pinid + ', ' + self._x + ', ' + self._y + ', ' + self._time + ', ' + self._netid)


class Photo(object):

    def __init__(self, pinid, photo_id, photo, description, time, userid,
                 likes, anon=False, hidden=False, liked=False, categories=set()):
        self._pinid = pinid
        self._photo_id = photo_id
        self._photo = photo
        self._description = description
        self._time = time
        self._userid = userid
        self._likes = likes
        self._liked = liked
        self._categories = {category for category in categories}
        self._thumbnail = self._format_thumbnail(photo)
        self._anon = anon
        self._hidden = hidden

    def _format_thumbnail(self, photo):
        return re.sub(r'(.*/image/upload/)(.*)', r'\1w_650,h_350,c_fill/\2', photo)

    def getThumbnail(self):
        return self._thumbnail

    def getPinid(self):
        return self._pinid

    def getPhotoId(self):
        return self._photo_id

    def getPhoto(self):
        return self._photo

    def getDescription(self):
        return self._description

    def getTime(self):
        return self._time

    def getUser(self):
        return self._userid

    def getLikes(self):
        return self._likes

    def getLiked(self):
        return self._liked

    def setLiked(self, liked):
        self._liked = liked

    def getCategories(self):
        return self._categories

    def getAnon(self):
        return self._anon

    def getHidden(self):
        return self._hidden

    def toString(self):
        return(str(self._pinid) + ', ' + str(self._photo) + ', ' + str(self._description) +
                  ', ' + str(self._time) + ', ' + str(self._userid))

class PhotoReport(object):
    def __init__(self, report_id, photo_id, reason, time_filed):
        self._report_id = report_id
        self._photo_id = photo_id
        self._reason = reason
        self._time_filed = time_filed

    def getReportId(self):
        return self._report_id

    def getPhotoId(self):
        return self._photo_id

    def getReason(self):
        return self._reason

    def getTimeFiled(self):
        return self._time_filed

    def toString(self):
        return(str(self._report_id) + ', ' + str(self._photo_id) + ', '  + 
            str(self._reason) + ', ' + str(self._time_filed))

class PinReport(object):
    def __init__(self, report_id, pin_id, reason, time_filed):
        self._report_id = report_id
        self._pin_id = pin_id
        self._reason = reason
        self._time_filed = time_filed

    def getReportId(self):
        return self._report_id

    def getPinId(self):
        return self._pin_id

    def getReason(self):
        return self._reason

    def getTimeFiled(self):
        return self._time_filed

    def toString(self):
        return(str(self._report_id) + ', ' + str(self._pin_id) + ', '  + 
            str(self._reason) + ', ' + str(self._time_filed))

class Tour(object):
    def __init__(self, tour_id, origin_x, origin_y, dest_x, dest_y, description, netid, x1 = 0, y1 = 0, x2 = 0, y2 = 0, x3 = 0, y3 = 0, x4 = 0, y4 = 0, x5 = 0, y5 = 0, x6 = 0, y6 = 0):
        self._tour_id = tour_id
        self._description = description
        self._origin_x = origin_x
        self._origin_y = origin_y
        self._dest_x = dest_x
        self._dest_y = dest_y
        self._netid = netid
        self._x1 = x1
        self._y1 = y1
        self._x2 = x2
        self._y2 = y2
        self._x3 = x3
        self._y3 = y3
        self._x4 = x4
        self._y4 = y4
        self._x5 = x5
        self._y5 = y5
        self._x6 = x6
        self._y6 = y6
    
    def getDescription(self):
        return self._description
    
    def getOriginX(self):
        return self._origin_x
    
    def getOriginY(self):
        return self._origin_y
    
    def getDestX(self):
        return self._dest_x
    
    def getDestY(self):
        return self._dest_y
    
    def getX1(self):
        return self._x1
    
    def getY1(self):
        return self._y1
    
    def getX2(self):
        return self._x2
    
    def getY2(self):
        return self._y2
    
    def getX3(self):
        return self._x3
    
    def getY3(self):
        return self._y3
    
    def getX4(self):
        return self._x4
    
    def getY4(self):
        return self._y4
    
    def getX5(self):
        return self._x5
    
    def getY5(self):
        return self._y5
    
    def getX6(self):
        return self._x6
    
    def getY6(self):
        return self._y6
    
    def getTourID(self):
        return self._tour_id
    
    def getLength(self):
        if self._x1 == 0:
            return 2
        elif self._x2 == 0:
            return 3
        elif self._x3 == 0:
            return 4
        elif self._x4 == 0:
            return 5
        elif self._x5 == 0:
            return 6
        elif self._x6 == 0:
            return 7
        return 8
