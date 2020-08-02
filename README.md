# peopleScraper
Python-based webscraper for the Chinese publication "People"

Program scrapes front page / main page for headlines that include words/characters in "flagArticleTriggers.csv", then scrapes each flagged article and counts frequency of occurence of each of the terms in "wordsInArticle.csv".

Outputs

screenedLinks.csv             —     Running list of previously scraped articles (prevents double-counting articles)
linksScraped DATE time.csv    —     List of article headlines and URLs scraped in one session
wordFrequencies DATE time.csv —     count of occurence frequency for each word/character in "wordsInArticle.csv", with column headers as article URLs

For now, the script takes input for front page URL; once a front page (http: // usa.people.com.cn/ vs. http: // world.people.com.cn/ is decided/finalized, URL will be hardcoded.

Update "flagArticleTriggers.csv" to adjust which article headlines are flagged from the main page.
Update "wordsInArticle.csv" to adjust the words counted from each article
