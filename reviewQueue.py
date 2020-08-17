#! /usr/local/bin/python3

from peopleArticleProcessing import PeopleArticleProcessing
from datetime import datetime, timedelta
import pandas as pd
from os.path import dirname, abspath
from time import perf_counter

'''
reviewQueue.py
Author:         Noah Asing
Last updated:   Aug 16, 2020
'''

########## Enter CSV file names ##########

flagArticleCSV = 'flagArticleTriggers_english.csv'
countCSV = 'wordsInArticles_english.csv'
screenedLinksCSV = 'screenedLinks.csv'

urlStem = 'http://en.people.cn/review/' # Program fills in date number and the .html

# Creates datetime objects for the endpoints of the review dates to be scraped
# Enter start and end date with format year, month, day
startDay = datetime(2020, 8, 1)
endDay = datetime(2020, 8, 5)

##########################################

# Ensures that the endDay occurs after the startDay
delta = endDay - startDay
if delta.days < 0:
    switcherVar = endDay
    endDay = startDay
    startDay = switcherVar
elif delta.days == 0:
    print('Invalid window: endDay and startDay are identical. If only 1 day is to be run, use peopleArticleProcessing.py')

day = endDay + timedelta(days=1)      # Increments datetime object forward 1 day for the loop

# Obtains full path to CSV containing words to count/analyze
countCSVfull = dirname(abspath(__file__)) + '/' + countCSV

# Creates a blank dataframe table for the scraped links
# Column headers for the review date that the article was pulled from, article headline and link.
d = {'reviewDate': [], 'Headlines': [], 'scrapedLinks': []}
scrapedTotalDF = pd.DataFrame(d)

# Creates dataframe with first column as the words to analyze.
totalFreqDF = pd.DataFrame([])
totalFreqDF['words_phrases'] = list(pd.read_csv(countCSVfull)['words_phrases'])

while day != startDay:

    day += timedelta(days=-1)       # Increments datetime object 1 day towards the past
    date = day.strftime('%Y%m%d')   # Saves date in string form with YYYYmmdd (Aug 5, 2020 --> 20200805)

    print('Running', urlStem+date+'.html ...')  # Prints the URL about to run to console

    obj = PeopleArticleProcessing(
        flagArticleCSV, countCSV, screenedLinksCSV, urlStem+date+'.html')

    freqFragmentDF = obj.processArticles()

    # Exports list of screened articles to CSV for next run to use as filter
    obj.screened.to_csv(obj.dirName + screenedLinksCSV, index=False)

    # Merges the review's articles' word counts to the total count dataframe
    if freqFragmentDF is not None:
        totalFreqDF = totalFreqDF.merge(freqFragmentDF, on='words_phrases', how='left')

    # Following block generates a dataframe with the same columns as scrapedTotalDF and appends it to the bottom of scrapedTotalDF
    m = []
    for el in obj.flaggedLinks:
        m += [day.strftime('%b %d, %Y')]
    scrapedFragment = {'reviewDate': m, 'Headlines': obj.flaggedHeadlines, 'scrapedLinks': obj.flaggedLinks}
    scrapedFragmentDF = pd.DataFrame(scrapedFragment)
    scrapedTotalDF = scrapedTotalDF.append(scrapedFragmentDF, ignore_index=True)

# Exports scrapedTotalDF to CSV named with datetime of run.
scrapedCSVname = 'linksScraped ' + \
    datetime.now().strftime('%m.%d.%Y %I%M%p') + '.csv'
scrapedTotalDF.to_csv(obj.dirName + scrapedCSVname, index=False, encoding='utf-8-sig')

# Exports word counts to CSV named with datetime of run.
freqCSVname = 'wordFrequencies ' + \
    datetime.now().strftime('%m.%d.%Y %I%M%p') + '.csv'
totalFreqDF.to_csv(obj.dirName + freqCSVname, index=False, encoding='utf-8-sig')

# Logs the time taken to run in console
print('Job took ', perf_counter(), ' seconds')