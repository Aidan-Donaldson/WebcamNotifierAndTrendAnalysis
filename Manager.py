import smtplib as smtp
import ssl
import sqlite3
import datetime
import bcrypt
from email.message import EmailMessage
from email.utils import make_msgid
import mimetypes

dbFile = "" # Your sqlite db file

def Hash(string):
    SALT = b'$2b$12$2haDY23wT0S4yStDTBU49u'
    hashedString = str(bcrypt.hashpw(string.encode("utf-8"), SALT))[len(SALT)+2:]
    return hashedString

def Login(email, passwordAttempt): #Needs to use user password not app password
    userId = None
    passwordAttempt = Hash(passwordAttempt)
    try:
        connection = sqlite3.connect(dbFile)
        cursor = connection.cursor()
            
        cmmd = f"""SELECT password, id
        FROM User
        WHERE Email = "{email}"
        """
        cursor.execute(cmmd)
        password, userId = cursor.fetchall()[0]
        connection.close()
        if passwordAttempt == password:                    
            return userId
        
        else:
            raise Exception
        
    except Exception as exception:
        print(exception, "\nEmail or password invalid")
        if userId is None:
            return None
        else:
            return False

def UpdatePrefs(user, notify, freq, critical, evntId):
    connection = sqlite3.connect(dbFile)
    cursor = connection.cursor()
        
    cmmd = f"""UPDATE Preferences
    SET SummaryFreq = {freq}, Notify = {notify}, Critical = {critical}
    WHERE UserId = {user} AND EvntID = {evntId}
    """
    cursor.execute(cmmd)
    connection.commit()
    connection.close()

def AddUser(email, password):
    password = Hash(password)
    connection = sqlite3.connect(dbFile)
    cursor = connection.cursor()
         
    cmmd = f"""INSERT INTO User (Email, Password)
VALUES ("{email}", "{password}");

CREATE TEMP TABLE LastUser (UserId INTEGER);
INSERT INTO LastUser
SELECT last_insert_rowid();

INSERT INTO Preferences (UserId, EvntId)
SELECT LastUser.UserId, EventType.EvntId
FROM lastUser, EventType;

INSERT INTO EventSummary (UserId, EvntId)
SELECT lastUser.UserId, EventType.EvntId
FROM lastUser, EventType;

DROP TABLE LastUser
    """
    cursor.executescript(cmmd)
    connection.close()

def GetPrefs(user):
    connection = sqlite3.connect(dbFile)
    cursor = connection.cursor()
        
    cmmd = f"""SELECT Type, SummaryFreq, Notify, Critical, EventType.EvntId
FROM Preferences, EventType
WHERE Preferences.UserId = {user}
AND Preferences.EvntId = EventType.EvntId
ORDER BY Type ASC
    """
    cursor.execute(cmmd)
    data = cursor.fetchall()
    connection.close()
    return data

def AddEvent(user, evntId, time, fileName):
    dayName = {0: "Mon", 1: "Tue", 2: "Wed", 3: "Thu", 4: "Fri", 5: "Sat", 6: "Sun"}
    day = dayName[datetime.datetime.today().weekday()]
    connection = sqlite3.connect(dbFile)
    cursor = connection.cursor()
    cmmd = f"""SELECT Critical
FROM Preferences
WHERE UserId = {user} AND EvntId = {evntId}
    """
    cursor.execute(cmmd)
    critical = cursor.fetchall()[0][0]
    
    cmmd = f"""INSERT INTO EventLog (UserId, EvntId, Time, Day, ImagePath)
VALUES ({user}, {evntId}, "{time}", "{day}", "{fileName}");

UPDATE EventSummary
SET EvntFreq = EvntFreq + 1
WHERE UserId = {user} AND EvntId = {evntId}
    """
    cursor.executescript(cmmd)
    connection.commit()
    connection.close()
    if critical == 1:
        SendCriticalUpdate(user, evntId, fileName)

def SendCriticalUpdate(user, evntId, fileName):
    email = GetUserInfo(user)
    evnt, evntDesc = GetEventInfo(evntId)
    messageDefaultContent = f"""\
Something Has Been Detected
Good afternoon. {evnt} ({evntDesc}) has recently been detected"""
    
    message = CreateEmailMessage("Event of Importance Detected", email, messageDefaultContent)
        
    imageCId = make_msgid()

    htmlText = """\
<html>
    <head></head>
    <body>
        <h2>Something Has Been Detected</h2>
        <p>Good afternoon. {eventType} ({eventDesc}) has recently been detected<br>
        Below is the captured image:<br>
        <img src="cid:{imageCId}" alt="Predicted Event">
        </p>
    </body>
</html>""".format(eventType=evnt, eventDesc=evntDesc, imageCId=imageCId[1:-1])
    
    message.add_alternative(htmlText, subtype="html")    
    with open(f"Images/{fileName}", "rb") as img:
        maintype, subtype = mimetypes.guess_type(img.name)[0].split("/")
        #print(maintype, subtype)
        message.get_payload()[1].add_related(img.read(),
                                             maintype=maintype,
                                             subtype=subtype,
                                             cid=imageCId)
    
    SendMessage(email, message)

def GetEventInfo(evntId):
    connection = sqlite3.connect(dbFile)
    cursor = connection.cursor()
    cmmd = f"""SELECT Type, Desc
FROM EventType
WHERE EvntId = {evntId}
    """
    cursor.execute(cmmd)
    info = cursor.fetchall()[0]
    return info

def GetUserInfo(user):
    connection = sqlite3.connect(dbFile)
    cursor = connection.cursor()
    cmmd = f"""SELECT Email
FROM User
WHERE Id = {user}
    """
    cursor.execute(cmmd)
    info = cursor.fetchall()[0]
    return info

def CreateEmailMessage(subject, recipient, messageContent):
    try:
        message = EmailMessage()
        message["From"] = "" # Your Email Server
        message["Subject"] = subject
        message["To"] = recipient
        message.set_content(messageContent)
    
        return message
    except:
        return False

def SendMessage(recipient, message):
    SSLport = 465
    context = ssl.create_default_context()
    sender = "" # Your Email server
    appPassword = "" # Your Email app password
    
    try:
        with smtp.SMTP_SSL("smtp.gmail.com", SSLport, context = context) as server:
            server.login(sender, appPassword)
            server.send_message(message)
            server.quit()
    except Exception as exception:
        print("Exception:", exception)


def SendUpdate(updateInfo, currentTime, user):
    connection = sqlite3.connect(dbFile)
    cursor = connection.cursor()
    for record in updateInfo:
        cursor = connection.cursor()
        lastSent, notifType, notifDesc, notifFreq, eventId, eventFreq, notify = record
        #print(lastSent, notifType, notifDesc, notifFreq)
        dateFormat = "%Y-%m-%d"
        lastSent = datetime.datetime.strptime(lastSent, dateFormat)
        updateTime = lastSent + datetime.timedelta(days=notifFreq)
        
        if currentTime >= updateTime:
            newDate = currentTime.strftime(dateFormat)
            cmmd = f"""UPDATE EventSummary
SET GeneratedDate = "{newDate}", EvntFreq = 0
WHERE UserId = {user} AND EvntId = {eventId}
            """
            cursor.execute(cmmd)
            
            if notify:
                email = GetUserInfo(user)
                messageContent=f"""\
In the past {notifFreq} day(s): A {notifType.lower()} has been detected {eventFreq} time(s)
{notifType} - {notifDesc}."""
                message = CreateEmailMessage("Event Summary", email, messageContent)
                SendMessage(email, message)
            
    connection.commit()
    connection.close()

def GetUpdateInfo(user):
    connection = sqlite3.connect(dbFile) 
    cursor = connection.cursor()
        
    cmmd = f"""SELECT GeneratedDate, Type, Desc, SummaryFreq, EventSummary.EvntId, EvntFreq, Notify
FROM EventSummary, EventType, User, Preferences
WHERE User.Id = {user}
AND User.Id = EventSummary.UserId
AND EventSummary.EvntId = EventType.EvntId
AND Preferences.EvntId = EventType.EvntId
AND Preferences.UserId = User.Id
    """
    cursor.execute(cmmd)
    data = cursor.fetchall()
    connection.close()
    return data

def GetEvents(user):
    connection = sqlite3.connect(dbFile)
    cursor = connection.cursor()
        
    cmmd = f"""SELECT EvntId, Date, Time, Day
    FROM EventLog
    WHERE UserId = {user}
    """

    cursor.execute(cmmd)
    data = cursor.fetchall()
    connection.close()
    
    return data

def ConvertEventId(antecendents, consequents):
    connection = sqlite3.connect(dbFile)
    cursor = connection.cursor()
    cmmd = f"""SELECT EvntId, Type
FROM EventType
    """
    
    cursor.execute(cmmd)
    data = cursor.fetchall()
    connection.close()
    
    eventKey = dict(data)
    for i in range(len(antecendents)):
        length = len(antecendents[i])
        for x in range(length):
            value = antecendents[i][x]
            if type(value) is int:
                antecendents[i][x] = eventKey[value]
    
    for i in range(len(consequents)):
        length = len(consequents[i])
        for x in range(length):
            value = consequents[i][x]
            if type(value) is int:
                consequents[i][x] = eventKey[value]
         
    return (antecendents, consequents)

def Update(user):
    updateInfo = GetUpdateInfo(user)
    currentTime = datetime.datetime.now()
    SendUpdate(updateInfo, currentTime, user)