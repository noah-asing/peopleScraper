#! /usr/local/bin/python3

from os import path
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime

'''
peopleArticleProcessing.py
Author:         Noah Asing
Last updated:   Aug 16, 2020
'''

########## Enter CSV file names ##########

flagCSV = 'flagArticleTriggers_english.csv'
articleWordsCSV = 'wordsInArticles_english.csv'
screenedLinksCSV = 'screenedLinks.csv'
inputURL = 'http://en.people.cn/'

##########################################


class PeopleArticleProcessing():

    def __init__(self, flagCSV, articleWordsCSV, screenedLinksCSV, frontPageURL):
        '''
        Constructor performs variable initialization and peopleArticleProcessing instantiation

        Parameters
        flagCSV (str):              CSV w/ Chinese characters for identifying relevant articles from headlines
        articleWordsCSV (str):      CSV w/ Chinese characters to count/analyze within relevant articles
        screenedLinksCSV (str):     CSV w/ URLs of previously screened articles
        frontPageURL (str):         main page of China People news site (i.e. http://usa.people.com.cn/)
        '''

        # Retrieves path to the python file and makes absolute path strings to CSV's
        self.dirName = path.dirname(path.abspath(__file__)) + '/'

        flagCSV = self.dirName + flagCSV
        articleWordsCSV = self.dirName + articleWordsCSV
        screenedLinksCSV = self.dirName + screenedLinksCSV

        # Intakes CSV data to DataFrame table of words for identifying relevant articles
        self.articleTriggers = pd.read_csv(flagCSV)

        # Intakes CSV data to DataFrame table of words to count/analyze within articles
        self.wordsToCount = pd.read_csv(articleWordsCSV)

        # Intakes article URLs that have previously been screened. If CSV is not found, an empty list is used
        try:
            self.screened = pd.read_csv(screenedLinksCSV)
        except:
            self.screened = pd.DataFrame({'articleHistory': []})

        self.frontPageURL = frontPageURL.strip()
        self.domain = self.frontPageURL.split('.cn/', 1)[0] + '.cn'
        self.flaggedLinks = []
        self.flaggedHeadlines = []

    def getArticles(self):

        try:
            siteContent = requests.get(self.frontPageURL).content
        except:
            print('Link Denied/Broken: ', self.frontPageURL)
            return

        # Parses front page content with lxml
        soup = BeautifulSoup(siteContent, 'lxml')

        # Bool 'boring' will prompt a message if there are no unscreened, relevant articles
        boring = True

        # Loops through anchor tags
        for link in soup.findAll('a'):

            # Extracts URL from hyperlinks and converts to str
            articleURL = str(link.get('href')).strip()

            # Filters for links containing url stem ('http://DOMAIN...') that are articles ('DOMAIN.cn/n...')
            domainBool = '://' in articleURL and '/n' in articleURL
            # Filters for articles with truncated URL's (usa.people, world.people)
            truncatedBool = '/' == articleURL[0] and '/n' in articleURL

            if domainBool or truncatedBool:
                if domainBool == False:
                    # Adds domain back to truncated href value
                    articleURL = self.domain + articleURL

                # Executes if the list of screened articles is not empty
                if len(self.screened.values):
                    # If article has been screened before, process continues to next link and the rest of the 'for' loop is skipped
                    if articleURL in self.screened.values:
                        continue

                boring = False

                # Adds to screened article history DF
                self.screened = self.screened.append(
                    {'articleHistory': articleURL}, ignore_index=True)

                # Loops through the Chinese column of article identifying DF
                for el in self.articleTriggers['Characters']:

                    # Filters for article headlines containing a trigger term
                    if el in link.get_text():

                        # Adds article link to list of articles for analysis
                        self.flaggedLinks += [articleURL]

                        # Adds article headline to list of articles for analysis
                        self.flaggedHeadlines += [link.get_text().strip()]

                        break

        return self.flaggedHeadlines, self.flaggedLinks, boring

    def processArticles(self):

        boring = self.getArticles()[2]

        # This block generates a DF table with 1 column for the words/phrases
        self.freqDF = pd.DataFrame([])
        self.freqDF['words_phrases'] = list(self.wordsToCount['words_phrases'])

        if boring == True:
            if __name__ == '__main__':
                # Message prevents user confusion if the program does not generate new CSVs
                print('No new pertinent articles at ',
                      self.frontPageURL, '\n', r'¯\_(ツ)_/¯')
                exit()
            return

        for link in self.flaggedLinks:      # Loops through flagged article links
            try:                            # Tries to retrieve article content; if request fails, loop continues to next link
                rawContent = requests.get(link).content
            except:
                print('Article Link Denied: ' + link)
                continue

            # Parses article data with lxml
            soup = BeautifulSoup(rawContent, 'lxml')

            # Extracts paragraph tags
            articleContent = soup.find_all('p')

            fullText = ''
            for el in articleContent:
                # Concatenates paragraphs into one string
                fullText += el.text.strip() + ' '

            # Counts occurrences of each word being analyzed
            wordCount = []
            for el in self.wordsToCount['words_phrases']:
                wordCount += [fullText.count(el)]

            # Adds column to word frequency DF table named with the URL with number of occurrences as values
            self.freqDF[link] = wordCount
            
        # Excludes occurrences of 'unfriendly' from count of 'friend'
        try:
            self.freqDF = self.freqDF.set_index('words_phrases')
            self.freqDF.loc['friend'] = self.freqDF.loc['friend'] - self.freqDF.loc['unfriendly']
        except:
            pass

        self.freqDF = self.freqDF.reset_index()
        
        return self.freqDF

    def exportToCSV(self):

        # Exports screened article DF to csv
        self.screened.to_csv(self.dirName+screenedLinksCSV, index=False)

        # Exports word frequency DF to CSV named with datetime
        freqCSVname = 'wordFrequencies ' + \
            datetime.now().strftime('%m.%d.%Y %I%M%p') + '.csv'
        self.freqDF.to_csv(self.dirName + freqCSVname,
                           index=True, encoding='utf-8-sig')

        # This block forms a DF table of analyzed articles and exports to CSV, named with datetime.
        scrapedDict = {'frontPageHeadlines': self.flaggedHeadlines, 'scrapedLinks': self.flaggedLinks}
        scrapedDF = pd.DataFrame(scrapedDict)
        scrapedCSVname = 'linksScraped ' + \
            datetime.now().strftime('%m.%d.%Y %I%M%p') + '.csv'
        scrapedDF.to_csv(self.dirName + scrapedCSVname,
                         index=True, encoding='utf-8-sig')


if __name__ == '__main__':
    
    yoohoo = PeopleArticleProcessing(
        flagCSV, articleWordsCSV, screenedLinksCSV, inputURL)
    yoohoo.processArticles()
    yoohoo.exportToCSV()
