#!/usr/bin/python2.7
## This Script is to read CSV File and process the records to be imported into db.
##
## Author: Ahmed Sammoud
## Date:   June, 2016
##
## Company: Red Hat, Red Hat University , Intern_Team_2016
##
## Description :
##              - This Script's main purpose is to read in ".csv" file and extract the needed information for data analysis.
##              - Also Writes results into an csv output file.
##              - The Script runs in three phases:        
##              --            1- It uses the csv package and start reading Rows from the file in the Starter module.
##              --            2- It uses the Extract_Info function to extract the needed info from columns in each row.
##              --            3- The Process_Data function is used to :
##                                1- clean up the data from each columns
##                                2- populate the needed data structures.
##              --            
##              --    Starter --> Extract_Info --> Process_Data  
##



import csv
from ravello_parse import Rev_Parse
import pprint

class CSV_Rev:

# A function that selects only the needed Columns and puts it in a new list.

        def __init__(self,filename="csv_output.csv",perm = 'r+'):
                self.Parser = Rev_Parse() #initializing parser
                # Open CSV File 

                if perm == 'r+':

                        # Open file Read binary
                        CSV_F = open(filename, perm)

                        # Starting the reader, One Row at a time. Puts it into a list.
                        self.Reader = csv.reader(CSV_F)
                        self.Reader.next() #skip header row
                else :

                        # Open file Write mode
                        CSV_F = open(filename, perm)
                        # Starting the Writer
                        self.Writer = csv.writer(CSV_F)
        
        
                
        def __Extract_Data__(self,Row):
	        Info = {}       # list of values from csv
                #_________________________________
                # The names of the keys match the names from Ravello Rest API, That to ensure consistency among modules.
                #__________________________________
                #TIP for Self: Be smart and make this a global unified dictionary.
                
                Info["applicationId"] = Row[0]
                Info["appName"] = Row[1] # Applicaiton Name
                Info["deleted"] = Row[2] # App Status
                Info["blueprintName"] = Row[3] # BluePrint 

                #Info.(Row[4]) # Cloud Type
                
                Info["appDescription"] = Row[7] # Description
                Info["owner"]  =  Row[21] # Owner
                Info["region"] =  Row[28] # Region
                Info["charges"]  = [ {"summaryPrice" : float(Row[29])}]
                #Info["charges"]  = ({{'summaryPrice': float(Row[29])},{'null':0}} # Total Cost
                Info["upTime"] = Row[30]  # UpTime
                return Info


        def __Process_Data__(self,Info):
                # Process The Data
                # use ravello_parse functions for cleanning up and returnning valid info.
                
                list = self.Parser.Parse_AppBillingInfo(Info)
                
                return list

        
        def getlist(self):

                list = []

                for Row in self.Reader:
                        Info = self.__Extract_Data__(Row)
                        list.append(self.__Process_Data__(Info))
                
                return list

        
        def store_Rows(self,Rows):
                for Row in Rows:
                        self.Writer.writerow(Row)

                
        def store_Row(self,Row):
                self.Writer.writerow(Row)
                

                

#T = CSV_Import()
#list = T.getlist("csv_test.csv")
#P = pprint.PrettyPrinter()
#P.pprint(list)
