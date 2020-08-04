#! /usr/local/bin/python3

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

'''
peopleArticleProcessing.py
Author:         Noah Asing
Last updated:   Aug 3, 2020
'''

class peopleArticleProcessing():

    def __init__(self, flagCSV, articleWords, prescreened, frontPageURL):
        '''
        Constructor performs variable initialization and peopleArticleProcessing instantiation

        Parameters
        flagCSV (str):      CSV w/ Chinese characters for identifying relevant articles from headlines
        articleWords (str):     CSV w/ Chinese characters to count/analyze within relevant articles
        prescreened (str):  CSV w/ URLs of previously screened articles
        frontPageURL (str): main page of China People news site (i.e. http://usa.people.com.cn/)
        '''

        self.articleTriggers = pd.read_csv(flagCSV)     # intakes CSV data to DataFrame table of words for identifying relevant articles
        self.markerWords = pd.read_csv(articleWords)    # intakes CSV data to DataFrame table of words to count/analyze within articles

        '''
        The following try-except block intakes article URLs that have been screened in previous runs (to prevent reduncancy/minimize requests)
        If the CSV with "already-screened" article URLs can't be found, an empty list is used
        '''

        try:
            self.screened = pd.read_csv(prescreened)
        except:
            self.screened = pd.DataFrame([], columns=['articleHistory'])
        self.frontPageURL = frontPageURL
        self.flaggedLinks = []
        self.flaggedHeadlines = []
        self.mainPeopleDomain = ['http://www.people.com.cn/', 'www.people.com.cn', 'http://people.com.cn', 'people.com.cn']

    def getArticles(self):

        try:
            siteContent = requests.get(self.frontPageURL).content
        except:
            print('Front Page Link Denied/Broken')
            exit()

        soup = BeautifulSoup(siteContent, 'lxml')                       # parses front page content with lxml

        boring = None                                                   # bool 'boring' will prompt a message if there are no unscreened, relevant articles
        for link in soup.findAll('a'):                                  # loops through anchor tags
            articleURL = str(link.get('href'))                          # extracts URL from hyperlinks and converts to str
            domainBool = self.frontPageURL in self.mainPeopleDomain and '/n1/' in articleURL  # filters for articles on main people domain
            subdomainBool = '/' == articleURL[0] and '/n1/' in articleURL       # filters for articles on people subdomains (usa.people, world.people)
            if domainBool or subdomainBool:
                if domainBool == False:
                    articleURL = self.frontPageURL + articleURL                 # the subdomains news source truncates href vals to post-domain info; this line adds the domain back
                if articleURL in self.screened['articleHistory'].values:        # if article has been screened before, move to next iteration
                    continue
                else:
                    boring = 'not boring!'
                    self.screened = self.screened.append({'articleHistory': articleURL}, ignore_index=True)  # adds to screened article history DF
                    for el in self.articleTriggers['Characters']:           # loops through the Chinese column of article identifying DF
                        if el in link.get_text():                           # filters for article headlines containing a trigger term
                            self.flaggedLinks += [articleURL]               # adds article link to list of articles for analysis
                            self.flaggedHeadlines += [link.get_text()]      # adds article headline to list of articles for analysis
        if boring == None:
            print ('No new pertinent articles  ¯\_(ツ)_/¯')                 # message prevents user confusion if the program does not generate new CSVs
            exit()

        self.screened.to_csv('./screenedLinks.csv', index=False)            # exports screened article DF to csv

        return self.flaggedLinks

    def processArticles(self):

        self.getArticles()

        freq = {}                           # This block generates a dictionary with keys for each of the words/phrases analyzed from the articles
        for el in self.markerWords['words_phrases']:
            freq[el] = 0

        freqDF = pd.DataFrame([])           # This block generates a DF table with 1 column for the words/phrases
        freqDF['words_phrases'] = list(freq.keys())

        for link in self.flaggedLinks:      # loops through flagged article links
            try:                            # tries to retrieve article content; if request fails, loop continues to next link
                rawContent = requests.get(link).content
            except:
                print('Article Link Denied: ' + link)
                continue

            soup = BeautifulSoup(rawContent, 'lxml')        # parses article data with lxml

            articleContent = soup.find_all('p')             # extracts paragraph tags

            fullText = ''
            for el in articleContent:
                fullText += el.text.strip() + ' '           # concatenates paragraphs into one string

            for el in self.markerWords['words_phrases']:    # loops through each analysis word/phrase
                freq[el] = fullText.count(el)               # counts and stores occurrences of word/phrase in freq dictionary

            freqDF[link] = list(freq.values())              # adds column to word frequency DF table named with the URL with number of occurrences as values

        freqDF.to_csv('./wordFrequencies ' + datetime.now().strftime('%m.%d.%Y %I%M%p') + '.csv', index=False, encoding='utf-8-sig')  # exports frequency DF table to CSV named with datetime

        # This block forms a DF table of analyzed articles and exports to CSV, named with datetime. Index column is headlines, 1st col is URLs
        scrapedDF = pd.DataFrame(self.flaggedLinks, columns=['scrapedLinks'])
        scrapedDF.index = self.flaggedHeadlines
        scrapedDF.index.name = 'frontPageHeadlines'
        scrapedDF.to_csv('./linksScraped ' + datetime.now().strftime('%m.%d.%Y %I%M%p') + '.csv', index=True, encoding='utf-8-sig')

        return freqDF


if __name__ == '__main__':
    inputURL = input('Input a People (China) publication main page URL, i.e. http://usa.people.com.cn/ \n')
    yoohoo = peopleArticleProcessing('./flagArticleTriggers.csv', './wordsInArticles.csv', './screenedLinks.csv', inputURL)  # 'http://usa.people.com.cn/')
    yoohoo.processArticles()
