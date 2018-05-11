#Alex Dobrovansky
#Started: 4th May 2018

#Moves recordings from one location to another, then modifies the database for the new location

#Run from recordings folder
#e.g. if recordings were in C:/randomfolder/recordings/2018/05/etc...
#run from C:/randomfolder/recordings




#Inputs:
#   start date
#   end date
#   destination location
#   or locationID

import firebirdsql
import os
import shutil
import datetime
import calendar

DB = "C:\Program Files (x86)\Oak Telecom\Comms Suite\data\COMMSUITE.FDB"

def getLastDayOfMonth(date):
    lastDay = calendar.monthrange(date.year,date.month)[1]
    return datetime.datetime(date.year,date.month,lastDay,23,59,59)

def strToDateTime(date):
    year = int(date[0])
    month = int(date[1])
    return datetime.datetime(year,month,1,0,0)


def getImmediateSubDirectories(a_dir):
    return [name for name in os.listdir(a_dir)
            if os.path.isdir(os.path.join(a_dir, name))]

def leadingZero(string):
    if len(string) == 1:
        string = "0" + string
    return string

def getInt(msg, default):
    failure = True
    while failure:
        try:
            if default:
                num = input(msg + "(" + default + ") ")

                if num == "":
                    num = default
            else:
                num = int(input(msg))

            failure = False
        except:
            print("That failed, please try again")
            failure = True
    return str(num)
    

def getDate(msg, defaults):
    confirm = "n"
    while confirm not in ['y','Y','']:
        print(msg)
        #Please enter the year
        year = getInt("Enter the year in YYYY format: ", defaults[0])
        if len(year) == 2:
            year = '20' + year
        month = leadingZero(getInt("Enter the month in MM format: ", defaults[1]))   

        #check directory exists
        if os.path.isdir(year+"/"+month):
            confirm = input("You have entered " + month +"/"+ year +". Is this correct? (Y/n) ")
        else:
            print("Cannot find that directory, please try again")
            confirm = "n"

    return [year,month]


def getLocation(msg):
    confirm = 'n'
    archiveID = None
    while confirm not in ['y','Y','']:
        path = input(msg + "(C:\c) ")
        if (path == ""):
            path = "C:\c"
        try:
            archiveID = int(path)
            #get path from DB

            con = firebirdsql.connect(host='localhost',database=DB, user='sysdba', password='masterkey')
            cur = con.cursor()
            cur.execute("SELECT ADDRESS FROM ARCHIVELOCATION WHERE ID = " + path)
            r = cur.fetchone()
            path = r[0]

        except ValueError:
            #must be a file location
            print("")
        finally:
            if os.path.isdir(path):
                confirm = input("You have entered " + path + ". Is this correct? (Y/n) ")
            else:
                print("That directory does not exist! Please try again ")
                confirm = 'n'
    return path,archiveID


#get start date
startDate = getDate("Please enter the starting date (inclusive)",['2018','01'])
#get end date
endDate = getDate("Please enter the ending date (inclusive)",startDate)
#get destination
dest,ID = getLocation("Enter destination directory or archive location ID: ")


#copy files and folders to destination
for year in range(int(startDate[0]),int(endDate[0])+1): #needs to plus 1 to be inclusive
    year = str(year)
    src = os.getcwd() + "/" + year
    print("Moving " + src) #year
    if not os.path.isdir(dest + "/" + year):
        #create directory        
        os.makedirs(dest + "/" + year)

    for month in range(int(startDate[1]),int(endDate[1])+1):
        month = str(month)
        if len(month) == 1:
            month = "0" + month
        if not os.path.isdir(dest + "/" + year + "/" + month):
            #create directory
            os.makedirs(dest + "/" + year + "/" + month)
        
        src = os.getcwd() + "/" + year + "/" + month
        print("Moving " + src)#month
        days = getImmediateSubDirectories(src)
        for day in days:
            print("Moving " + src)
            src = os.getcwd() + "/" + year + "/" + month + "/" + day
            if not os.path.isdir(dest + "/" + year + "/" + month + "/" + day):
                #create directory
                os.makedirs(dest + "/" + year + "/" + month + "/" + day)
            finalDest = dest + "/" + year + "/" + month + "/" + day
            recordings = os.listdir(src)
            for rec in recordings:
                src = os.getcwd() + "/" + year + "/" + month + "/" + day + "/" + rec
                if os.path.isfile(src):
                    shutil.remove(src)
                shutil.move(src,finalDest)

#update database
#get archive ID
if not ID:
    con = firebirdsql.connect(host='localhost',database=DB, user='sysdba', password='masterkey')
    cur = con.cursor()
    cur.execute("SELECT ADDRESS FROM ARCHIVELOCATION WHERE ADDRESS = '?'",dest)
    r = cur.fetchone()
    if r:
        ID = r[0]
        print(r)
    else:
        #create ID
        query = "INSERT INTO ARCHIVELOCATION (SHORTNAME, ADDRESSTYPE,ADDRESS,AVAILABLESIZE,PERCENTAGETOUSE) VALUES ('AutoArchivr',?,?,NULL,?)"
        values = ('1',dest,'95.00')
        print(values)
        cur.execute(query,values)
        con.commit()

#change recording's archive location
#update recordings set archivelocation = 3 where startdatetime >= '2014.01.01 00:00:00' and startdatetime <= '2015.05.31 23:59:59'

#change date format
startDateTime = strToDateTime(startDate)
start = startDateTime.strftime("%Y.%m.%d %H:%M:%S")
endDateTime = getLastDayOfMonth(strToDateTime(endDate))
end = endDateTime.strftime("%Y.%m.%d %H:%M:%S")


con = firebirdsql.connect(host='localhost',database=DB, user='sysdba', password='masterkey')
cur = con.cursor()
query = "UPDATE recordings SET archivelocation = ? WHERE startdatetime >= ? AND startdatetime <= ?"
values = (ID,start,end)
print(values)
cur.execute(query,values)
con.commit()


