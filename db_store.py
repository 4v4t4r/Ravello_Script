#!/usr/bin/python2.7

## This Script is to Process Ravello data and store the records into a DB
## The main DB will be Mongodb since the data is in the form of JSON.
##
## The Script is an interface to simplify the storing and retrieving process.
## 
## Author: Ahmed Sammoud
## Date:   June, 2016
##
## Company: Red Hat, Red Hat University , Intern_Team_2016
##
## Description :
##              - This Script's main purpose is to provide an interface to the DB
##
##

import logging
import datetime
import re
from pymongo import *


# Enumration for values.
# For python 2.7
def enum(**name):
    return type("Enum", (), name)


# This class is an interface for the DB operations on the Rev_DB
# Mainly the DB should be on Mongodb, but in case different DB was used, this should provide the isolation needed.

# Rev_Store : Main methods are
#  - Store : Takes in the name of collection to store the record in .. This name should be selected from the 
#             DB_Table item. "See Table Overview below ".
#
#     An intial overview on the collections on mongo
#      - Apps     :Collection of information about apps
#    
#      - Billing_App: Collection containing all billing info
#          - This will contain redundant data with the App_Id
#             collection.
#
#      - Billing : Total for each month for all Apps.
# 
#  - Get_<attribute> * : Thers are two types of get methods
#       - Either Get all info for <attribute>
#       - Get Specific info for a Specfic <attribute>
#     - List of <attribute>s : BillMonth, BillinToDay, BillApp, BillUser, BillUsers,
#                              BillClass,BillClasses,BillDepts,BillDept,BillOwner,BillOwners,BillRegion,BillRegions.


# See Documentation below for more specific information,.
class Rev_Store:
    DB_Table = enum(App_Id="App", Billing_App="Billing_App", Total_Billing="Billing")

    def __init__(self, DB_URI):

        # Mongo Connection
        self.DB_Connection = MongoClient(DB_URI)

        # Mongo db
        self.DB = self.DB_Connection['Rev_Stat']

        # Setting name for logger information
        self.logger = logging.getLogger('__Rev_Store__')
        self.logger.debug("Rev_Store intiailized")

    # Store information on the corresponding collection,
    # db: Must be one of the DB_Table values
    # returns an object of type

    def Store(self, record, db):
        Coll = None
        result = None

        if db == "Apps":
            Coll = self.DB['Apps']
        elif db == "Billing":
            Coll = self.DB['Billing']  # Redundant ....
        else:
            Coll = None

        if (db == "Apps"):
            if Coll != None:
                for r in record:
                    self.logger.debug("###APPS: Record : \n" + str(r))
                    # This will Upserts
                    self.logger.debug("Apps: Updatting > Id: " + str(r["applicationId"]))
                    result = Coll.update_many({"applicationId": r["applicationId"]}, {"$set": r}, upsert=True)
                    self.logger.debug("Apps: # of updated records :" + str(
                        result.modified_count) + " In Collection:" + Coll.full_name)

        elif (db.startswith("Billing")):

            if Coll != None:
                # This will Upserts
                self.logger.debug("Billing: Updating Billing Month : " + record["month"])
                result = Coll.update_many({"month": record["month"]}, {
                    "$set": {"month": record["month"], "total": record["total"],
                             "Lib_Store_Charge": record["Lib_Store_Charge"], "appList": record["appList"]}},
                                          upsert=True)
                self.logger.debug(
                    "Billing: # of updated records :" + str(result.modified_count) + " In Collection:" + Coll.full_name)

        else:
            if Coll != None:
                # This will Upserts
                result = Coll.update_one({"applicationId": record["applicationId"]}, {"$set": record}, upsert=True)
                self.logger.debug(
                    "else: # of updated records :" + str(result.modified_count) + " In Collection:" + Coll.full_name)

        return result

    # Get_BillingMonth : Returns Billing Totals for that month year
    # month : in the format of XX
    # Year : Format XXXX
    # Returns Totals .
    def Get_BillMonth(self, month, year):
        Coll = self.DB['Billing']
        result = Coll.find({"month": "{:>02d} {:s}".format(int(month), year)})
        self.logger.debug(
            "# of found records :" + str(result.count()) + " In Collection:" + Coll.full_name + " For Month " + str(
                month) + " " + str(year))
        return result

    # Get_BillingToday : Return all Billing Totals for Current Month up to this day.
    # This assumes that the db is updated daily.
    # Returns Totals 
    def Get_BillingToDay(self):
        Coll = self.DB['Billing']
        result = Coll.find({"month": datetime.datetime.now().strftime("%m %Y")})
        self.logger.debug("# of found records :" + str(result.count()) + " In Collection:" + Coll.full_name)
        return result

    # Get_BillApp : Return billing information about specific app
    # Id : App Id to get billing info for.
    # Returns Totals for this app .
    def Get_BillApp(self, Id):
        Coll = self.DB['Billing']
        # result = Coll.find({"appList.applicationId":Id})

        result = Coll.aggregate([{"$unwind": "$appList"}, {"$match": {"appList.applicationId": Id}},
                                 {"$group": {"_id": "$month", "total": {"$sum": "$appList.charges"}}}
                                 ])

        self.logger.debug("# of found records :" + str(result.alive) + " In Collection:" + Coll.full_name)
        return result

    # Get_BillUser : Return Bill information for specfic username
    # username: username
    # Returns total sum
    def Get_BillUser(self, username):
        Coll = self.DB['Billing']
        # result = Coll.aggregate({"$group":{"_id":"$appList.username","Total":{"$sum":"$appList.charges"}}})

        result = Coll.aggregate([{"$unwind": "$appList"}, {"$match": {"appList.username": username}},
                                 {"$group": {"_id": "$appList.class", "total": {"$sum": "$appList.charges"}}}])

        self.logger.debug("# of found records :" + str(result.alive) + " In Collection:" + Coll.full_name)
        return result

    # Get_BillUsers : Returns all info for all users
    # Returns list of usernames and their totals
    def Get_BillUsers(self):
        Coll = self.DB['Billing']
        result = Coll.aggregate([
            {"$unwind": "$appList"}, {"$group": {"_id": "$appList.username", "total": {"$sum": "$appList.charges"}}}
        ])

        self.logger.debug("# of found records :" + str(result.alive) + " In Collection:" + Coll.full_name)
        return result

    # Get_BillClasses : Returns all info for all classes
    # Returns list of Classes and their totals
    def Get_BillClasses(self):
        Coll = self.DB['Billing']

        result = Coll.aggregate([
            {"$unwind": "$appList"}, {"$group": {"_id": "$appList.class", "total": {"$sum": "$appList.charges"}}}
        ])

        self.logger.debug("# of found records :" + str(result.alive) + " In Collection:" + Coll.full_name)
        return result

    # Get_BillClass : Return Bill information for specfic class
    # course: class
    # Returns total sum

    def Get_BillClass(self, course):
        Coll = self.DB['Billing']

        result = Coll.aggregate([{"$unwind": "$appList"}, {"$match": {"appList.class": course}},
                                 {"$group": {"_id": "$month", "total": {"$sum": "$appList.charges"}}}])

        self.logger.debug("# of found records :" + str(result.alive) + " In Collection:" + Coll.full_name)
        return result

    # Get_BillDepts : Returns all info for all users
    # Returns list of Depts and their totals
    def Get_BillDepts(self):
        Coll = self.DB['Billing']

        result = Coll.aggregate([
            {"$unwind": "$appList"}, {"$group": {"_id": "$appList.department", "total": {"$sum": "$appList.charges"}}}
        ])

        self.logger.debug("# of found records :" + str(result.alive) + " In Collection:" + Coll.full_name)
        return result

    # Get_BillDept : Return Bill information for specific Dept
    # Dept : Department
    # Returns total sum

    def Get_BillDept(self, dept):
        Coll = self.DB['Billing']

        result = Coll.aggregate([{"$unwind": "$appList"}, {"$match": {"appList.department": dept}},
                                 {"$group": {"_id": "$month", "total": {"$sum": "$appList.charges"}}}])

        self.logger.debug("# of found records :" + str(result.alive) + " In Collection:" + Coll.full_name)
        return result

    # Get_BillRegions : Returns all info for all Regions
    # Returns list of Regions and their totals
    def Get_BillRegions(self):
        Coll = self.DB['Billing']

        result = Coll.aggregate([
            {"$unwind": "$appList"}, {"$group": {"_id": "$appList.region", "total": {"$sum": "$appList.charges"}}}
        ])

        self.logger.debug("# of found records :" + str(result.alive) + " In Collection:" + Coll.full_name)
        return result

    # Get_BillRegion : Return Bill information for specfic Region
    # region : Region
    # Returns total sum
    def Get_BillRegion(self, region):
        Coll = self.DB['Billing']

        result = Coll.aggregate([{"$unwind": "$appList"}, {"$match": {"appList.region": region}},
                                 {"$group": {"_id": "$month", "total": {"$sum": "$appList.charges"}}}])

        self.logger.debug("# of found records :" + str(result.alive) + " In Collection:" + Coll.full_name)
        return result

    # Get_BillOwners : Returns all info for all Owners
    # Returns list of Owners and their totals
    def Get_BillOwners(self):
        Coll = self.DB['Billing']

        result = Coll.aggregate([
            {"$unwind": "$appList"}, {"$group": {"_id": "$appList.owner", "total": {"$sum": "$appList.charges"}}}
        ])

        self.logger.debug("# of found records :" + str(result.alive) + " In Collection:" + Coll.full_name)
        return result

    # Get_BillOwner : Return Bill information for specfic Owner
    # Owner:Owner
    # Returns total sum
    def Get_BillOwner(self, Owner):
        Coll = self.DB['Billing']

        result = Coll.aggregate([{"$unwind": "$appList"}, {"$match": {"appList.owner": Owner}},
                                 {"$group": {"_id": "$month", "total": {"$sum": "$appList.charges"}}}])

        self.logger.debug("# of found records :" + str(result.alive) + " In Collection:" + Coll.full_name)
        return result

    # ToDo: Add more selections for reporting capabilities.
    #      For example : Add options to select different reports outputs .
    # All of these needs to be done on Monthly level as well on period of time 'From Jan to May for example'.
    #          - Report for all
    #          - Usage of each user, for each course. "in terms of Total and Vm time ?"
    #          - Usage of each department for each month.
    #          - Usage of each class for each month.
    #          - Usage for courses, in terms of Total
    #          - Top 10 Courses, Users. ( In terms of Total)
    #          - Sorted list for departments, Regions,Owners
    #

    # Report : Will return a report on all information currently in DB.
    # Returns a list of strings 
    def Report(self):

        # User/Dept/Courses stats for 3,6,9, 1 year
        # - Usage: time, Total, courses.
        # Use separate reports 

        list = []

        # Reporting Sequence.

        cur = self.Get_BillingToDay()
        list.append([" Billing up to Today for this month"])
        list.append(["Month", "Total", "Library Cost"])
        for l in cur:
            list.append([l["month"], l["total"], l["Lib_Store_Charge"]])

        list.append(["_" * 100])  # Empty line

        cur = self.Get_BillUsers()
        list.append(["Billing for Users"])
        list.append(["Username", "Total"])
        for l in cur:
            list.append([l["_id"], l["total"]])

        list.append(["_" * 100])  # Empty line

        cur = self.Get_BillClasses()
        list.append(["Billing for Classes"])
        for l in cur:
            list.append([l["_id"], l["total"]])

        list.append(["_" * 100])  # Empty line

        cur = self.Get_BillDepts()
        list.append(["Billing for Departments"])
        for l in cur:
            list.append([l["_id"], l["total"]])

        list.append(["_" * 100])  # Empty line

        cur = self.Get_BillRegions()
        list.append(["Billing for Regions"])
        for l in cur:
            list.append([l["_id"], l["total"]])

        list.append(["_" * 100])  # Empty line

        cur = self.Get_BillOwners()
        list.append(["Billing for Owners"])
        for l in cur:
            list.append([l["_id"], l["total"]])

        return list

    def Report_ALL(self,month):
        self.logger.debug("Report_ALL : month"+month)
        list = []


        list.append(["_" * 100])  # Empty line
        list = list + self.Report_Cost_Total(month)

        list.append(["_" * 100])  # Empty line
        list = list + self.Report_Dept_Total(month)

        list.append(["_" * 100]) # Empty line
        list = list + self.Report_Courses_Total(month)

        list.append(["_" * 100])  # Empty line
        list = list + self.Report_Regions_Total(month)

        list.append(["_" * 100])  # Empty line
        list= list + self.Report_Users_Total(month)

        return list

    def Report_Cost_Total(self,month):
        list=[]
        self.logger.debug("Report_Cost_Total : month " + month)
        result_total = self.Query_Billing_Total(month)

        list.append(["Billing Information"])
        list.append(["Month", "Total", "Library Charge", "Application Charge"])

        App_Charge = 0
        for l in result_total:
            for i in l["appList"]:
                App_Charge+= i["charges"]

        list.append( [l["month"], l["total"], l["Lib_Store_Charge"], App_Charge])
        return list

    def Report_Users_Total(self,month):
        self.logger.debug("Report_Users_Total : month " + month)
        list = []
        result_user = self.Query_Users_Total(month)
        list.append(["All Users Information"])
        list.append( ["Username", "Courses", "Department", "Applications Total"])

        for l in result_user:
            list.append( [l["_id"], l["Courses"] , l["Department"], l["total"]])

        return list

    def Report_Courses_Total(self,month):
        self.logger.debug("Report_Courses_Total : month " + month)
        list = []
        result_course = self.Query_Courses_Total(month)
        list.append( ["All Courses Information"])
        list.append( ["Course name", "# of users", "Department", "Application total"])
        for l in result_course:
            list.append( [l["_id"], l["# of students"], l["Department"], l["total"]])

        return list

    def Report_Dept_Total(self,month):
        self.logger.debug("Report_Dept_Total : month " + month)
        list = []
        result_dept = self.Query_Dept_Total(month)
        result_total = self.Query_Billing_Total(month)
        list.append( ["All Department Information"])
        list.append( ["Department", "# of students", "Total"])

        for l in result_dept:
            list.append( [l["_id"], l["# of students"], l["total"]])

        return list

    def Report_Regions_Total(self,month):
        self.logger.debug("Report_Regions_Total : month " + month)
        list = []
        result_region = self.Query_Region_Total(month)
        list.append( ["All Region Information"])
        list.append( ["Region", "# of students", "Applications Total"])
        for l in result_region:
            list.append( [l["_id"], l["# of students"], l["total"]])

        return list

    # Users: Start, end_Date, Fields.
    # for each user generate the following:
    # - Total charges per Month.
    # - Courses included in that Charge.
    # - Department

    def Query_Billing_Total(self, month_in):
        self.logger.debug("Query_Billing_Total: month " + month_in)
        year = re.search("\d\d\d\d", month_in).group(0)
        month = int(re.search("\d\d", month_in).group(0))

        # Users Total/month -- "Display: Dept, Courses"
        # -----------
        Coll = self.DB['Billing']

        if re.search("\d\d \d\d\d\d", month_in) is None:
            self.logger.error("Month format Must be 'XX XXXX'")
            return None

        result = Coll.find({"month": str("{:>02}".format(month) + " " + "{:4}".format(year))})

        return result

    # Users: Start, end_Date, Fields.
    # for each user generate the following:
    # - Total charges per Month.
    # - Courses included in that Charge.
    # - Department

    def Query_Users_Total(self, month_in, Num_Month=1):
        self.logger.debug("Query_Users_Total: month " + month_in)
        year = re.search("\d\d\d\d", month_in).group(0)
        month = int(re.search("\d\d", month_in).group(0))

        # Users Total/month -- "Display: Dept, Courses"
        # -----------
        Coll = self.DB['Billing']

        if re.search("\d\d \d\d\d\d", month_in) is None:
            self.logger.error("Month format Must be 'XX XXXX'")
            return None

        for M in range(month, month + Num_Month):
            result = Coll.aggregate(
                [
                    {"$match":
                         {"month": str("{:>02}".format(month) + " " + "{:4}".format(year))}},
                    {"$unwind": "$appList"},
                    {"$group":
                         {"_id": "$appList.username",
                          "Department": {"$first": "$appList.department"},
                          "Courses": {"$addToSet": "$appList.class"},
                          "total": {"$sum": "$appList.charges"}
                          }
                     }
                ])

        return result

    # Query Each User, Total per Course for each month
    # for each user generate the following:
    # - Courses per Month total
    # - Departments

    def Query_User_Courses(self, username, month_in, Num_Month=1):

        self.logger.debug("Query_User_Courses: month " + month_in)

        year = re.search("\d\d\d\d", month_in).group(0)
        month = int(re.search("\d\d", month_in).group(0))

        # Users Total/month -- "Display: Dept, Courses"
        # -----------
        Coll = self.DB['Billing']

        if re.search("\d\d \d\d\d\d", month_in) is None:
            self.logger.error("Month format Must be 'XX XXXX'")
            return None

        for M in range(month, month + Num_Month):
            result = Coll.aggregate(
                [
                    {"$match":
                         {"month": str("{:>02}".format(month) + " " + "{:4}".format(year))}},
                    {"$unwind": "$appList"},
                    {"$match": {"appList.username": username}},
                    {"$group":
                         {"_id": "$appList.class",
                          "Month": {"$first": "$month"},
                          "Department": {"$first": "$appList.department"},
                          "total": {"$sum": "$appList.charges"}
                          }
                     }
                ])

        return result

    # Query Total for Each Course, Per Month.
    # For each course generate the follwoing
    # - Total per Course
    # - # of users per month
    # - Department of that course

    def Query_Courses_Total(self, month_in, Num_Month=1):

        self.logger.debug("Query_Courses_Total: month " + month_in)

        year = re.search("\d\d\d\d", month_in).group(0)
        month = int(re.search("\d\d", month_in).group(0))

        # Users Total/month -- "Display: Dept, Courses"
        # -----------
        Coll = self.DB['Billing']

        if re.search("\d\d \d\d\d\d", month_in) is None:
            self.logger.error("Month format Must be 'XX XXXX'")
            return None

        for M in range(month, month + Num_Month):
            result = Coll.aggregate(
                [
                    {"$match":
                         {"month": str("{:>02}".format(month) + " " + "{:4}".format(year))}},
                    {"$unwind": "$appList"},
                    {"$group":
                         {"_id": "$appList.class",
                          "Department": {"$first": "$appList.department"},
                          "# of students": {"$sum": 1},
                          "total": {"$sum": "$appList.charges"}
                          }
                     },
                ])

        return result

    # Query for course, Total
    # for each user generate the following:
    # - Courses per Month total
    # - # of students
    # - Total

    def Query_Course(self, course, month_in, Num_Month=1):

        self.logger.debug("Query_Course: month " + month_in)

        year = re.search("\d\d\d\d", month_in).group(0)
        month = int(re.search("\d\d", month_in).group(0))

        # course Total/month -- "Display: Dept, Courses"
        # -----------
        Coll = self.DB['Billing']

        if re.search("\d\d \d\d\d\d", month_in) is None:
            self.logger.error("Month format Must be 'XX XXXX'")
            return None

        for M in range(month, month + Num_Month):
            result = Coll.aggregate(
                [
                    {"$match":
                         {"month": str("{:>02}".format(month) + " " + "{:4}".format(year))}},
                    {"$unwind": "$appList"},
                    {"$match": {"appList.class": course}},
                    {"$group":
                         {"_id": "$appList.class",
                          "Month": {"$first": "$month"},
                          "Department": {"$first": "$appList.department"},
                          "# of students": {"$sum": 1},
                          "total": {"$sum": "$appList.charges"}
                          }
                     }
                ])

        return result

    # Query Total for Each Department, Per Month.
    # For each course generate the follwoing
    # - Total per Department
    # - # of users per month

    def Query_Dept_Total(self, month_in, Num_Month=1):

        self.logger.debug("Query_Dept_Total: month " + month_in)
        year = re.search("\d\d\d\d", month_in).group(0)
        month = int(re.search("\d\d", month_in).group(0))

        # Users Total/month -- "Display: Dept, Courses"
        # -----------
        Coll = self.DB['Billing']

        if re.search("\d\d \d\d\d\d", month_in) is None:
            self.logger.error("Month format Must be 'XX XXXX'")
            return None

        for M in range(month, month + Num_Month):
            result = Coll.aggregate(
                [
                    {"$match":
                         {"month": str("{:>02}".format(month) + " " + "{:4}".format(year))}},
                    {"$unwind": "$appList"},
                    {"$group":
                         {"_id": "$appList.department",
                          "# of students": {"$sum": 1},
                          "total": {"$sum": "$appList.charges"}
                          }
                     },
                ])

        return result

    # Query for Department, Total
    # for each user generate the following:
    # - Courses per Month total
    # - # of Studnets

    def Query_Department(self, dept, month_in, Num_Month=1):

        self.logger.debug("Query_Department: month " + month_in)
        year = re.search("\d\d\d\d", month_in).group(0)
        month = int(re.search("\d\d", month_in).group(0))

        # course Total/month -- "Display: Dept, Courses"
        # -----------
        Coll = self.DB['Billing']

        if re.search("\d\d \d\d\d\d", month_in) is None:
            self.logger.error("Month format Must be 'XX XXXX'")
            return None

        for M in range(month, month + Num_Month):
            result = Coll.aggregate(
                [
                    {"$match":
                         {"month": str("{:>02}".format(month) + " " + "{:4}".format(year))}},
                    {"$unwind": "$appList"},
                    {"$match": {"appList.department": dept}},
                    {"$group":
                         {"_id": "$appList.department",
                          "Month": {"$first": "$month"},
                          "# of students": {"$sum": 1},
                          "total": {"$sum": "$appList.charges"}
                          }
                     }
                ])

        return result

    # Query Total for Each Region, Per Month.
    # For each course generate the following
    # - Total 
    # - # of users

    def Query_Region_Total(self, month_in, Num_Month=1):

        self.logger.debug("Query_Region_Total: month " + month_in)

        year = re.search("\d\d\d\d", month_in).group(0)
        month = int(re.search("\d\d", month_in).group(0))

        # Users Total/month -- "Display: Dept, Courses"
        # -----------
        Coll = self.DB['Billing']

        if re.search("\d\d \d\d\d\d", month_in) is None:
            self.logger.error("Month format Must be 'XX XXXX'")
            return None

        for M in range(month, month + Num_Month):
            result = Coll.aggregate(
                [
                    {"$match":
                         {"month": str("{:>02}".format(month) + " " + "{:4}".format(year))}},
                    {"$unwind": "$appList"},
                    {"$group":
                         {"_id": "$appList.region",
                          "# of students": {"$sum": 1},
                          "total": {"$sum": "$appList.charges"}
                          }
                     },
                ])

        return result

    # Query for Region, Total
    # for each Region generate the following:
    # - Month , # of Students,total

    def Query_Region(self, Region, month_in, Num_Month=1):

        self.logger.debug("Query_Region: month " + month_in)
        year = re.search("\d\d\d\d", month_in).group(0)
        month = int(re.search("\d\d", month_in).group(0))

        # Region Total/month -- "Display: Dept, Courses"
        # -----------
        Coll = self.DB['Billing']

        if re.search("\d\d \d\d\d\d", month_in) is None:
            self.logger.error("Month format Must be 'XX XXXX'")
            return None

        for M in range(month, month + Num_Month):
            result = Coll.aggregate(
                [
                    {"$match":
                         {"month": str("{:>02}".format(month) + " " + "{:4}".format(year))}},
                    {"$unwind": "$appList"},
                    {"$match": {"appList.region": Region}},
                    {"$group":
                         {"_id": "$appList.region",
                          "Month": {"$first": "$month"},
                          "# of students": {"$sum": 1},
                          "total": {"$sum": "$appList.charges"}
                          }
                     }
                ])

        return result
