#!/usr/bin/python2.7
## This Script is to clean the info from Ravello system and process the records
##
## Author: Ahmed Sammoud
## Date:   June, 2016
##
## Company: Red Hat, Red Hat University , Intern_Team_2016
##
## Description :
##              - This Script's main purpose is to take :
##                   --  dict element "Usually from the "Ravello site/Rest API interface"
##                   --  Or row "Usually from the .csv file".
##              - Return a dictionary -"Key:value"- with the extract, clean info.
##       


# These Functions will process the data according to the convention in the Ravello csv/REST API.
# So if anything changed in the way the names are stored in the system this function needs to 
# be modified.
##
## Following the Data observations:
## Logic Starts with the Application Name (0): if it starts with: "role:"
##              - Then Course Name, Can be extracted from Blueprint .. Check for "Copy of"
##              - Username,Class,bp from Description -- delimited by space, "user:XXX class:XXX bp:XXX".
##
##  if Application Name(0): Starts with: "k:"
##              - Username can be extracted from K:username__Department/ClassName
##              - This entry is delimited by __ (2 underscores)
##              - Class name can also be extracted from blueprint but sometimes you need to check for "Copy of" at the begining.
##              -- Not using that for now
##              -*** Discard Description if possible. <-- Not Consistent.
## 


import pprint
import logging
import re
import datetime

#logging.basicConfig(level=logging.DEBUG)

pp = pprint.PrettyPrinter()

#T = Rev_Parse()
##print(testb_k)

class Rev_Parse:
    
    def __init__(self):
        self.logger = logging.getLogger('__RevParse__')
        self.logger.debug("Rev_Parser Initialized ....")


    # The Goal of this function is to Clean up the blueprint naming convention and
    # most importantly is gather all the checks "Rules" in one place to avoid madness.
    # Used by : Parse_AppInfo, Parse_AppBillingInfo
        
    def __Get_Bp_class__(self,bp):
        self.logger.debug("Get_Bp_class ....")
        dict = {}
        ##This step is to correctly assign the blueprint name.
        dict["blueprint"]     = bp.strip() if not bp.startswith("Copy of ") else bp.strip()[8:]

        ## Get the class name from the blueprint -- Different cases because of the inconsistency.
        if dict["blueprint"].startswith("GSS") or dict["blueprint"].startswith("gss") :
            dict["class"]        =  (dict["blueprint"][4:]).upper()
        elif re.search('\D\D\d\d\d',dict["blueprint"]) is not None:
            dict["class"]        =  dict["blueprint"][:5].upper()
        elif dict["blueprint"].startswith("k:") or dict["blueprint"].startswith("K:") :
            dict["class"]        =  (dict["blueprint"].split("__"))[1]
        else: dict["class"]       =  (dict["blueprint"]).upper()
        
        return dict["blueprint"],dict["class"]

        
    # Takes in App info record for an App,
    # Returns a dictionary with the following items:
    # username, class, blueprint, class, applicationId, published, owner, department.

    def Parse_AppInfo(self,record):
        try:
            self.logger.debug("Parse_AppInfo Initialize.... id:"+str(record["id"])+"\n")
            dict= {}

            app_name = record['name']
            if app_name.startswith('role:'):
                tmp = re.split('[A-z]+:',record['description'])
                dict["username"]      = tmp[1].strip()
        
            elif app_name.startswith('k:'):
                tmp = app_name.split("__")
                dict["username"] = (tmp[0])[2:]

            if "blueprintName" in record.keys() :
                dict["blueprint"],dict["class"] = self.__Get_Bp_class__(record["blueprintName"].strip())
            else :
                dict["blueprint"] =  "N/A"
                dict["class"]     =  "N/A"
                record["blueprintName"] = "N/A"

            # Not all applications have deployment information
            if "deployment" in record.keys():
                x =record["deployment"]
                dict["Active_vms"] = float(x["totalActiveVms"]) 
            else :
                dict["Active_vms"]  = 0
                
            dict["department"] = "GSS" if record["blueprintName"].startswith("GSS") else "ROLE"
            dict["applicationId"] = record["id"]
            dict["published"]     = record["published"]
            dict["owner"]   = record["owner"]
            self.logger.debug("Parse_AppInfo :"+str(dict)+"\n*Record >>>>>>>:"+str(record))
            return dict
        except Exception as e :
            self.logger.error("Error While Parsing " + str(e))
            self.logger.debug("Parse_AppInfo_>> Current record id:"+str(record["id"])+" .. name:"+str(record["name"]) +" is dropped")
            self.logger.debug("Parse_APPInfo_>> Record :"+ str(record))
            self.logger.debug("Parse APPInfo_>> Result :"+str(dict))
            
    # Only process the charges entry in ravello data,
    # This most probably to be used with total billing for specific months.
    # Returns a float.
    def Parse_Total_BillingMonth(self,records):
        self.logger.debug("Parse Total Billing month ")
        dict = {}
        total =0

        for x in records:
            if("charges" in x.keys()):
                for x in x["charges"]:
                    total += x["summaryPrice"]
        self.logger.debug("Parse Total Billing month "+str(total))
        return total
    
    # Takes in Billing record for an App,
    # Returns a dictionary with the following items:
    # username, class, bp, total, status, owner, region, uptime.
    def Parse_AppBillingInfo(self,record):
        dict = {}
        app_name = record['appName']
        if app_name.startswith('role:'):
            tmp = re.split('[A-z]+:',record['appDescription'])
            dict["username"]      = tmp[1].strip()       

        elif app_name.startswith('k:'):
            tmp = app_name.split("__")
            dict["username"] = (tmp[0])[2:]

        elif app_name.startswith('k:'):
            tmp = app_name.split("__")
            dict["username"] = (tmp[0])[2:]

        if "blueprintName" in record.keys():
            dict["blueprint"], dict["class"] = self.__Get_Bp_class__(record["blueprintName"].strip())
        else:
            dict["blueprint"] = "N/A"
            dict["class"] = "N/A"
            record["blueprintName"] = "N/A"

        total =0
        for x in record["charges"]:
            total += float(x["summaryPrice"])
        dict["department"] = "GSS" if record["blueprintName"].startswith("GSS") else "ROLE"
        dict["charges"] = total
        dict["applicationId"] = record["applicationId"]
        dict["region"]        = record["region"]
        dict["upTime"]        = record["upTime"]
        dict["status"]  =  "deleted" if record["deleted"] else "ACTIVE"
        dict["owner"]   = record["owner"]

        # Ensures nothing went wrong, otherwise report it
        assert(dict != None),self.logger.error("None Dict detected, Record recieved is "+str(record))
        return dict

#pp = pprint.PrettyPrinter()

#T = Rev_Parse()
##print(testb_k)
#pp.pprint(T.Parse_AppInfo(testapp_role))
#pp.pprint(T.Parse_AppBillingInfo(testb_role))
#pp.pprint(T.Parse_AppInfo(testapp_k))
#pp.pprint(T.Parse_AppBillingInfo(testb_k))
