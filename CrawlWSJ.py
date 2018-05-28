# -*- coding: utf-8 -*-
"""
Created on Mon May 28 15:16:39 2018

@author: zerow
"""

"""" Packages """
import time
import selenium
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import urllib
from urllib.request import Request, urlopen  
import re
from fpdf import FPDF

########################################################################
########################################################################

# Gloabal variables
chromedriver = 'C:/D/Chrome/chromedriver.exe'
option = webdriver.ChromeOptions()
option.add_argument('disable-infobars')

########################################################################
########################################################################

# Functions
def GoogleSearchPage(KeyWords, PageNum):
    """ Get the link of google seach page """
    PageNumStr = str(PageNum)
    LinkPre = "https://www.google.com/search?q="
    LinkMiddle = "&rlz=1C1CHZL_enUS707US707&tbm=nws&ei=e3qUWqfJOu_F_QatybfACQ&start="
    LinkPost = "0&sa=N&biw=1536&bih=734&dpr=1.25"
    LinkSearched = LinkPre + KeyWords + LinkMiddle + PageNumStr + LinkPost
    return LinkSearched

def ExtractAllURLs(GoogleLink):
    """ Fetch all the links from a search page """
    # Store all the URLs of the WSJ website
    req = Request(GoogleLink, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        webpage = urlopen(req).read()
    except urllib.error.URLError as e:
        print(e.reason)
    bs = BeautifulSoup(webpage, 'lxml')
    RawUrls = []
    StartWord = "/url?q="
    EndWord = "&sa="
    for t1 in bs.findAll("h3", {"class": "r"}):
        t2 = t1.find('a', href = True)
        RawUrls.append(t2['href'][len(StartWord):].split(EndWord)[0])
    return RawUrls

def TrimTextContent(TextContent):
    """ Function to trim some bad signs from the text """
    return TextContent.replace('\n', ' ').\
                 replace('\r', '').replace('\xa0', '').replace("’", "").\
                 replace("—", " ").replace('“', '').replace('”', '').\
                 replace('?', '').replace('!', '').replace('<', '').\
                 replace('>', '').replace('–', ' ').replace('––', ' ').\
                 replace('‘', '').replace('’', '').replace('‐', ' ').\
                 replace('―', '').replace("…", '').replace('-', ' ').\
                 replace("\ufeff", "").replace('|', '').replace('/', '')
                 
def ConvertTime(TimeText):
    """ Function to extract the time out of HTML file """
    AllTimeStr = TimeText
    try:
        AllStrDate = AllTimeStr.split(',')[0]
        StrDate = AllStrDate.split(' ')[-2:]         
        StrPost = AllTimeStr.split(',')[1]
        YearStr = StrPost[1:5]
        Time = []
        for i in range(6, len(StrPost)):
            if not StrPost[i].isalpha():
                Time.append(StrPost[i])
            else:
                Time.append(StrPost[i])
                Time.append(StrPost[i + 1])
                Time.append(StrPost[i + 2])
                break
        TimeStr = ''.join(Time)
        tempTime = TimeStr.split(' ')
        tempTime = [tempTime[0], ' ', tempTime[1]]
        TimeStr = ''.join(list(reversed(tempTime)))
        RetTime = ' '.join([YearStr, StrDate[0], StrDate[1], TimeStr])
    except:
        RetTime = TimeText
    return RetTime

def TrimHeadLine(HeadLine):
    """ Function to trim the headline so that it can be pdf title """
    return HeadLine.replace(':', ' ')

def ExtractTextContent(LogInLink, UserName, PassWord, \
                       SignInButton = "snippet-button--secondary", \
                       SignInName = "basic-login-submit",\
                       StopSign = "ad_and_popular", \
                       HeadLineSign = "wsj-article-headline",\
                       TimeClassName = "timestamp"):
    """ Parse all the words in the paragraphs """
    # Open each page 
    driver = webdriver.Chrome(chromedriver, chrome_options = option)
    driver.get(LogInLink)
    time.sleep(1) 
    # Find the submit button using class name and click on it.
    try:
        SubmitButton1 = driver.find_element_by_class_name(SignInButton).click()
        # Type in the username and password
        uname = driver.find_element_by_name("username") 
        uname.send_keys(UserName)  
        passw = driver.find_element_by_name("password")
        passw.send_keys(PassWord)  
        time.sleep(1)
        # Find the submit button using class name and click on it.
        SubmitButton2 = driver.find_element_by_class_name(SignInName).click()
        print ("\nSucceed to login page: " + LogInLink)
        # Decode       
        time.sleep(3)
        # Beautifulsoup decoding
        WebPage = driver.page_source
        time.sleep(3)
        bs = BeautifulSoup(WebPage, 'lxml')
        # Extract the headline
        HeadLine = TrimTextContent(bs.find("h1", {"class": HeadLineSign}).text)
        AllParagraphs = [HeadLine]
        # Time of article
        Time = ConvertTime(bs.find("time", {"class": TimeClassName}).text)
        AllParagraphs.append(Time)
        # String output
        AllDivs = bs.findAll('div')
        try:
            StopItem = bs.findAll("div", id = StopSign)[0]
        except:
            StopItem = bs.findAll("div", id = re.compile("^livefyre-toggle"))[0]
        for x in AllDivs: 
            if (x == StopItem):
                break
            for y in x.findAll('p'):
                AllParagraphs.append(TrimTextContent(y.text))
        # Close the browser                
        driver.quit()
        PrunedParas = list(filter(lambda x : not x.startswith("http"), AllParagraphs))      
        # Return the list of strings to the console
        return PrunedParas
    except:
        print ("\nFail to capture page: " + LogInLink)
        # Close the browser                
        driver.quit()
        return []

def Output2PDF(PrunedParas, PDFFilePre):
    """ Function to convert the list of strings into PDF file """
    Headline = TrimHeadLine(PrunedParas[0])
    Time = PrunedParas[1]
    PDFFile = TrimHeadLine(PDFFilePre + Headline + ".pdf")
    pdf = FPDF()
    # compression is not yet supported in py3k version
    pdf.compress = False
    pdf.add_page()
    # Unicode is not yet supported in the py3k version; use windows-1252 standard font
    pdf.set_font('Arial', '', 12)  
    pdf.ln(10)
    for l in range(len(PrunedParas)):
        pdf.write(5, PrunedParas[l])
        pdf.write(5, "\n\n")
    # To pdf    
    pdf.output(PDFFile, 'F')
    pdf.close()
    return Headline, Time, "Writing to PDF Good"

def GetArtilesFromSearchPage(RawUrls, UserName, PassWord, ArticleDF):
    """ Function to extract all article contents from a single search page """
    FailURLs = []
    # Download into PDF files
    for LinkNum in range(len(RawUrls)):
        # The url you want to login to
        LogInLink = RawUrls[LinkNum]
        # Get the paragraphs we want
        PDFFilePre = ""
        AllParagraphs = ExtractTextContent(LogInLink, UserName, PassWord)
        # If the link fail to log in, try again until it succeeds
        Counter = 1
        while len(AllParagraphs) == 0 and Counter <= 5:
            AllParagraphs = ExtractTextContent(LogInLink, UserName, PassWord)
            Counter += 1
        if Counter > 5:
            print ("\nFail to write to PDF from URL:  " + LogInLink)
            FailURLs.append(LogInLink)
            continue
        # Write to PDF file
        try:
            Headline, TimeString, Status = Output2PDF(AllParagraphs, PDFFilePre)
            print ("\nSucceed to write to PDF. ")
            NewLineDF = pd.DataFrame(np.zeros([1 , 3]), columns = ['HeadLine', 'Time', 'URL'])
            NewLineDF['HeadLine'] = Headline
            NewLineDF['Time'] = TimeString 
            NewLineDF['URL'] = LogInLink
            # Merge into the large DF
            ArticleDF = pd.concat([ArticleDF, NewLineDF], axis = 0)
        except:
            print ("\nFail to write to PDF from URL:  " + LogInLink)
            FailURLs.append(LogInLink)
            continue
    return FailURLs, ArticleDF

def GoogleSearchWSJ(KeyWords, NumPages, ArticleDF, UserName, PassWord):
    """ Function to search key words for WSJ articles on Google """
    for n in range(NumPages):
        print ("Now search page ", str(n + 1))
        PageNum = n
        LinkSearched = GoogleSearchPage(KeyWords, PageNum)  
        # All the URLs of the articles from one search page
        RawUrls = ExtractAllURLs(LinkSearched)     
        # Whole page search
        FailURLs, ArticleDF = GetArtilesFromSearchPage(RawUrls, UserName, \
                                PassWord, ArticleDF)
        # Delete the first row
        ArticleDF = ArticleDF.iloc[1:]
    return ArticleDF, FailURLs

########################################################################
########################################################################
    
# Main
if __name__ == "__main__":
    # Start time
    StartTime = time.clock()
    
    # Key words to be searched
    KeyWords = "wsj+fed+article"
    # How many pages to be searched
    NumPages = 1
    # Excel output
    OutFile = "Articles.xlsx"
    
    # Login parameters
    UserName = 'YourUserName'
    PassWord = 'YourPassWord'
    
    # Establish an empty DF
    ArticleDF = pd.DataFrame(np.zeros([1 , 3]), columns = ['HeadLine', 'Time', 'URL'])
    
    # Start searching
    ArticleDF, FailURLs = GoogleSearchWSJ(KeyWords, NumPages, ArticleDF, UserName, PassWord)
    
    # Write to excel file
    ArticleDF.to_excel(OutFile, index = False)    
    
    # End time
    EndTime = time.clock()
    print ('Time used is: ', EndTime - StartTime, ' seconds\n')
    
    ########################################################################
    ########################################################################