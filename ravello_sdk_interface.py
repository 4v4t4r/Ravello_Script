#!/usr/bin/python2.7

## This Script is to Process Ravello Stats and process the records
## The Script utilizes the Ravello SDK for maximum portability and support.
## 
## Author: Ahmed Sammoud
## Date:   June, 2016
##
## Company: Red Hat, Red Hat University , Intern_Team_2016
##
## Description :
##              - This Script's main purpose is to Connect to Ravello Website through the Ravello_SDK API and get these info.
##              - The following is The scope of the project:
##                                    - Get information from Ravello and store it in a local db

from ravello_sdk import *
from ravello_parse import *
import logging
import datetime
import pprint


# Logging level .. Default should be warning.

# logging.basicConfig(level=logging.DEBUG)
# Moved to get from config files
# user="rhu.script@gmail.com"
# Pass="" (password removed for security reasons)


class Rev_Connect:
    ## Initialize
    def __init__(self, username, password):
        # Should Pull login information from a config-file or command-line in the future.
        self.username = username
        self.Password = password
        self.Rev_client = RavelloClient()  # SDK Interface
        self.Rev_Parser = Rev_Parse()

        # Setting name for logger information
        self.logger = logging.getLogger('__RevConnect__')
        self.logger.debug("Rev_Connect Created")

        ## General Login Procedure

    def Rev_Login(self):
        ## This login uses the information provided in the constructor
        ## and Starts the session to be used with the following operations.

        self.logger.debug("  Ravello Login: " + self.username + " .......")
        self.Rev_client.login(self.username, self.Password)

    # Get all Application in a list with all their info.
    # ** Note: This will not get applications that were deleted.
    #          Use Get_Billing method for a full list of Applications.

    def Rev_GetAppList(self):
        self.logger.debug("Retrieving List of APPs List ..")

        appList = []
        records = self.Rev_client.get_applications()

        # Parse and return
        for x in records:
            appList.append(self.Rev_Parser.Parse_AppInfo(x))

        return appList
        # for app in self.Rev_client.get_applications():
        #	self.logger.info('Found Application: {0}'.format(app['id'])

    # Get Application with a certain ID.
    # The Application returned will be in form of dictionary list
    def Rev_GetAppID(self, ID):
        self.logger.debug("Retrieving APP ID: " + str(ID) + " .")

        try:
            list = self.Rev_client.get_application(ID)
            self.logger.debug("APP Found  Id:" + str(ID))
            app = self.Rev_Parser.Parse_AppInfo(list)
            # self.logger.debug("App After Parsing >"+str(app))
            return app
        except Exception as e:
            self.logger.debug("Error While Retrieving App :" + str(ID))
            return None

    # Stop a Specific VM, with certain App_id
    def Rev_StopVm(self, App_id, Vm_id):
        self.logger.debug("Stopping Vm ID: " + Vm_id + "In App ID: " + App_id)
        self.Rev_client.stop_vm(App_id, Vm_id)

    # Common operations between Billing_ToMonth and Billing_Month
    def __bill__(self, billing):

        total = self.Rev_Parser.Parse_Total_BillingMonth(billing)
        applist = []
        for x in billing:
            # Check if this is not a charge entry.
            if "appName" not in x:
                continue
            applist.append(self.Rev_Parser.Parse_AppBillingInfo(x))
        return total, applist

    # Get all applications cost since the beginning of the month
    # Returns charges for month as a dict, and list of apps charges
    def Rev_GetBillingToMonth(self):
        self.logger.debug("Retrieve Billing Since beging of this Month <" + datetime.datetime.now().strftime("%m %Y") + ">")
        billing = self.Rev_client.get_billing()
        total, applist = self.__bill__(billing)
        return {"month": datetime.datetime.now().strftime("%m %Y"), "total": total, "appList": applist}

    # Get all applications cost since the beginning of the month
    # The Format for the month is XX
    # The Format for the Year is XXXX
    # Returns only the total charges for that month(float).
    def Rev_GetBillingMonth(self, month, year):
        self.logger.debug("Retrieve Billing for <" + str(month) + "/" + str(year) + ">")
        billing = self.Rev_client.get_billing_for_month(year, month)
        total, applist = self.__bill__(billing)
        # d = date(int(year),int(month)

        return {"month": str(month) + " " + str(year), "total": total, "appList": applist}

    # Get list of Vms running under a certain application.
    def Rev_Get_VmList(self, App_id):
        self.logger.debug("Vm List: >>>>")
        return self.Rev_client.get_vms(App_id)

    # Exactly what you would think , It performs logout operation.
    def Rev_Logout(self):
        self.logger.debug("Revallo_Loging out....")
        return self.Rev_client.logout()

    # def main():

    # T = Rev_Connect()

    # T.Rev_Login()

    # test = T.Rev_Get_VmList(71993340)



    # test = T.Rev_GetAppID(72253721)
    # test = T.Rev_GetAppList()
    # test = T.Rev_Get_Billing_Month(2016,05)
    # test = T.Rev_Get_Billing_ToMonth()
    # test = T.Rev_Get_VmList(72253721)
    # print("Ravello_sdk")
    # pp = pprint.PrettyPrinter()

    # for app in test:
    #   print(">> Name : "+str(app['appName'])+"  ID:"+str(app['id']))
    #        pp.pprint(app)

    # pp.pprint(test)
    # app1 = test
    # pp.pprint(str(app1))


    #    for d in test:
    #        T.logger.debug("HERE <<>> "+str(d['id']))

    # test = T.Rev_GetAppID(d['id'])

    # pp = pprint.PrettyPrinter()
    # print(">>>>>>>>>>>>>>>>>??>>>>>")
    # pp.pprint((T.Rev_Get_Billing()))


    # print(">>>>>>>>>>>>>>>??>>>>>>>")

    # pp.pprint(T.Rev_Get_VmList(d['id']))
    # print(T.Rev_StopVm(d['id']))

    # T.Rev_Logout()

# main()
