#!/usr/bin/python2.7 -B
## This Script is to Process Ravello Stats and process the records
##
## Author: Ahmed Sammoud
## Date:   June, 2016
##
## Company: Red Hat, Red Hat University , Intern_Team_2016
##
## Description :
##              - This script's main purpose is to be the main module for the Interface with Ravello Data_Stats Project
##              - The following is the scope of the project:
##                                    - Get information from Ravello and store it in a local db.
##                                    - Form a User interface to query the DB.
##                                    - Automate the update procedure.
##
##              - The Script runs in the following phases:        
##              --            1- Main module runs and starts Either: Report_Gen  /OR/ 
##                              (Update recodes with Rev_Interface or CSV_IMP ) /OR/
##                              Both ** Run import then generate report.
##
##              --            2- The stream is used to start entry into Mongodb.
##              --            3- Then Report_Gen Module is called if user choose option 
##
##

import ConfigParser
import argparse
import sys

from csv_ravello import *
from db_store import *
from ravello_sdk_interface import *

## Moved to Config file for the script.
#DB = "mongodb://localhost:27017"
DB = ""

# Setup the Reportng level for the script.
logging.basicConfig(level=logging.DEBUG)

# Name of the Main Program section
logger = logging.getLogger("__Main__")



# Please change the name of the main function to something else,
# This code needs to be divided into different methods. -- Reporting part needs some work

def main():

    ########################################
    #
    #Initiating Command-Line Parsing 
    #q
    
    parser = argparse.ArgumentParser(prog='Rev_Stat',
                                     description='Ravello Stats Storing/Reporting tool:')
    
    parser.add_argument('-import_csv',nargs=2,metavar =('File_Name','"MM YYYY"') ,help="tell script to import from a csv into local db - Provide date 'MM YYYY' ")
    parser.add_argument('-gdb',metavar = '"MM YYYY"',nargs=1,help="Get Data from Ravello, store it in Local DB - Provide date")
    parser.add_argument('-gdbr',metavar = '"MM YYYY"',nargs=1,help = "Get Data from Ravello and Generate a report - Provide date")
    parser.add_argument('-report',metavar = ('"MM YYYY"', '"Report_On"'), nargs=2,
                        help ='''Generate a Report from Local DB. 
                                 Report_On can be one of the following [ALL - Users - Departments - Regions].
                        ''')


    ############################################
    # Config File :
    # Reading values from config file.
    Config = ConfigParser.ConfigParser()
    Config.read("Ravello.conf")
    options = {}
    
    # Main files option
    main_opt = Config.options("Main")
    for opt in main_opt:
        try:
            options[opt.upper()]= Config.get("Main",opt)
        except:
            logger.error("Exception %s",options[opt])
    DB = options["DB"]

    # Ravello Login file informations
    #
    Rav_opt = Config.options("Ravello_Login")
    for opt in Rav_opt:
        try:
            options[opt.upper()]= Config.get("Ravello_Login",opt)
        except:
            logger.error("Exception %s",options[opt])
    username = options["USERNAME"]
    password = options["PASSWORD"]

                                                
     

    ######################################3
    # Actual Processing Initiated
    #
    
    args = parser.parse_args()


    Rev_DB  = None
    Rev_Con =  None
    Rev_csv = None
    pp = None

    
    # Check number of options on the command line and initialize main classes if valid
    if len(sys.argv) > 1:
        Rev_DB  = Rev_Store(DB)
        pp = pprint.PrettyPrinter()


    ###############################################
    #Checking and processing different Options
    
    # Get Data from Ravello, Store it in db
    if args.gdb != None :
        logger.debug("Get Data from Ravello, Store it in db... Arguments Passed: "+str(args.gdb))


        Rev_Con = Rev_Connect(username,password)
        Rev_Con.Rev_Login()
        month = args.gdb[0]
        
        if re.search("\d\d \d\d\d\d",month) is None :
            logger.error("Month format Must be 'XX XXXX'")
            return

        else:
            year  = re.search("\d\d\d\d",month).group(0)
            month = re.search("\d\d",month).group(0)

            
        #Rev_Con.Rev_Login()        
        # Get App List 
        list = Rev_Con.Rev_GetAppList()
        list_app = list
        Rev_DB.Store(list_app,"Apps")
      
        # Get billing for that month.
        list = Rev_Con.Rev_GetBillingMonth(month,year)
        Rev_DB.Store(list,"Billing")
           
             
    # Same as above, plus generate a report
    elif args.gdbr != None:
        logger.debug("Get Data from Ravello, Store it in db, Generate a report .. Arguments Passed:"+str(args.gdbr))
        month = args.gdbr[0]
        if re.search("\d\d \d\d\d\d",month) is None :
            logger.error("Month format Must be 'XX XXXX'")
            return

        else:
            year  = re.search("\d\d\d\d",month).group(0)
            month = re.search("\d\d",month).group(0)


        Rev_Con = Rev_Connect(username,password)
        Rev_Con.Rev_Login()
        
        # Get App List
        logger.debug("Retrieve Apps List >>>")
        list = Rev_Con.Rev_GetAppList()
        list_app = list
        Rev_DB.Store(list_app,"Apps")
      
        # Get billing for that month.
        logger.debug("Retrieve Billing Information for "+str(args.gdbr[0]))
        list = Rev_Con.Rev_GetBillingMonth(month,year)
        Rev_DB.Store(list,"Billing")

        # Report Generation
        Rev_csv = CSV_Rev(filename="result.csv",perm='wb')
        csv.store_Rows(Rev_DB.Report())
        
        
    # Generate a report
    # Options to the report capabilities : "Date, Date range, specific reporting.. etc."
    elif args.report != None:
        
        logger.debug("Generate a Report From DB into csv ....  Arguments Passed: "+str(args.report))

        month = args.report[0]
        report = args.report[1]
        #option = args.report[2]
        
        
        if re.search("\d\d \d\d\d\d",month) is None :
            logger.error("Month format Must be 'XX XXXX'")
            return


        result_user = None
        result_course = None
        result_dept = None
        result_region = None
        list = []
        
        if report == "ALL" :
            ####################################################
            logger.debug("Reporting \"ALL\" Date: "+str(month))
            
            Rev_csv = CSV_Rev(filename="Report_All.csv",perm='wb')
            
            result_user = Rev_DB.Report_Users_Total(month)
            result_course = Rev_DB.Report_Courses_Total(month)
            result_dept = Rev_DB.Report_Dept_Total(month)
            result_region = Rev_DB.Report_Region_Total(month)

            
            list.append(["All Users Information"])
            list.append(["Username","Courses","Department","Total"])
            for l in result_user:
                list.append([l["_id"],l["Courses"],l["Department"],l["total"]])

            list.append(["_"*100]) # Empty line
            list.append(["All Courses Information"])
            list.append(["Course name","# of users","Department","total"])
            for l in result_course:
                list.append([l["_id"],l["# of students"],l["Department"],l["total"]])

            list.append(["_"*100]) # Empty line
            list.append(["All Department Information"])
            list.append(["Department","# of students","Total"])
            for l in result_dept:
                list.append([l["_id"],l["# of students"],l["total"]])

            list.append(["_"*100]) # Empty line
            list.append(["All Region Information"])
            list.append(["Region","# of students","Total"])
            for l in result_region:
                list.append([l["_id"],l["# of students"],l["total"]])
            
            Rev_csv.store_Rows(list)

                
        elif report == "Users":
            logger.debug("Reporting \"User\"")
            csv = CSV_Rev(filename="Report_Users.csv",perm='wb')
            result_user = Rev_DB.Report_Users_Total(month)
            list.append(["All Users Information"])
            list.append(["Username","Courses","Department","Total"])
            for l in result_user:
                list.append([l["_id"],l["Courses"],l["Department"],l["total"]])

            Rev_csv.store_Rows(list)
                                                        
        
        elif report == "Courses":
            logger.debug("Reporting \"Course\"")
            result_course = Rev_DB.Report_Courses_Total(month)
            csv = CSV_Rev(filename="Report_Courses.csv",perm='wb')
            list.append(["All Courses Information"])
            list.append(["Course name","# of users","Department","total"])
            for l in result_course:
                list.append([l["_id"],l["# of students"],l["Department"],l["total"]])
            Rev_csv.store_Rows(list)
                                                        
        elif report == "Departments":
            logger.debug("Reporting \"Department\"")
            result_dept = Rev_DB.Report_Dept_Total(month)
            Rev_csv = CSV_Rev(filename="Report_Department.csv",perm='wb')
            list.append(["All Department Information"])
            list.append(["Department","# of students","Total"])
            for l in result_dept:
                list.append([l["_id"],l["# of students"],l["total"]])
            Rev_csv.store_Rows(list)
                   
            
        elif report == "Regions":
            logger.debug("Reporting \"Region\"")
            Rev_csv = CSV_Rev(filename="Report_Region.csv",perm='wb')
            result_region = Rev_DB.Report_Region_Total(month)
            list.append(["All Region Information"])
            list.append(["Region","# of students","Total"])
            for l in result_region:
                list.append([l["_id"],l["# of students"],l["total"]])
            
            Rev_csv.store_Rows(list)
                                                        

        
    # Import a CSV amd store it in DB
    elif (args.import_csv) != None:
        logger.debug("CSV Import.....  Arguments Passed: "+str(args.import_csv))
        
        record = {}
        file  = args.import_csv[0]
        month = args.import_csv[1]

        if re.search("\d\d \d\d\d\d",month) is None :
            logger.error("Month format Must be 'XX XXXX'")
            return
        
        #get list
        Rev_csv = CSV_Rev(file)
        list =Rev_csv.getlist()
        
        total  =0
        for app in list:
            total += app["charges"]

        record["month"] = month
        record["total"] = total
        record["appList"] = list
        
        #store list
        Rev_DB.Store(record,"Billing")
        
    # When all else fails , Show help message
    else : parser.print_help()
    
    if Rev_Con is not None : Rev_Con.Rev_Logout()
    
main()
       



''' 
#THis Code is just test code that I used for DB .

        for month in range(1,13):
            month = "{:0>2d}".format(month)
            year  = "2015"
            list = Rev_Con.Rev_GetBillingMonth(month,year)
            Rev_DB.Store(list,"Billing")
            print(">> Billing App")
            
        month =0
        
        for month in range(1,7):
            month = "{:0>2d}".format(month)
            year  = "2016"
            list = Rev_Con.Rev_GetBillingMonth(month,year)
            Rev_DB.Store(list,"Billing")
            print(">> **Billing App")

'''

'''
        # Testing Sequence.
        #list = Rev_DB.Get_BillingToDay()
        #list = Rev_DB.Get_BillMonth("05","2015")
        #list = Rev_DB.Get_BillApp(66946219)
        #list = Rev_DB.Get_BillUser("jmann")
        #list  = Rev_DB.Get_BillUsers()
        #list = Rev_DB.Get_BillClasses()
        #list = Rev_DB.Get_BillClass("RH270")
        #list = Rev_DB.Get_BillDepts()
        #list = Rev_DB.Get_BillDept("GSS")

        #list = Rev_DB.Get_BillRegions()
        #list = Rev_DB.Get_BillRegion("Singapore")

        #list = Rev_DB.Get_BillOwners()
        #list = Rev_DB.Get_BillOwner("ravshello rhu")
        
        
        l = {}
        
        for l in list :
            print(">>>> "+ str(l["_id"])+" " +str(l["total"]) )#["month"] + " <<>>"+ str(l["total"] ))
        
        #for l in list :
        #    print(">> "+l)

       
        for x in range(1,13):
            # Get results from DB
            for d in ( (Rev_DB.Get_BillMonth("{:0>2d}".format(x),"2016")) ):
                print(">>>>>>>>> "+ "{:0>2d}".format(x),"2016" )
                pp.pprint(d["total"])
       
        list = Rev_Con.Rev_GetBillingToMonth()
        #list_app = list["appList"]
        print(">> Storing Billing App")
        Rev_DB.Store(list,"Billing_App")
    
'''
