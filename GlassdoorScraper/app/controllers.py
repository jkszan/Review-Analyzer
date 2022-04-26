from flask import Blueprint, g, request, make_response
from app.glassdoor import GlassdoorSession, getReviewInfo
from app.common import CaptchaEncounteredException
import logging

controller = Blueprint('', __name__)


# Setting route for loading reviews
@controller.route('/loadReviews',
    strict_slashes=False,
    methods=['GET'],
    defaults = dict(
        url = None,
        startingPage = 1
    ))
def loadReviews(url, startingPage):

    # Getting input for url
    baseurl = request.args.get('url', url)
    page = request.args.get('page', startingPage)

    # Throwing error if url is not provided
    if not baseurl:
        return make_response('No url provided', 400)

    # Creating session for scraping data from Glassdoor, passing forward our logger
    session = GlassdoorSession()
    g.appLogger.info('Successfully authenticated with Glassdoor')

    if startingPage > 1:
        url = alterURLPage(baseurl, startingPage)
    else:
        url = baseurl
    
    try:
        # Navigating WebDriver to the supplied url
        session.getPage(url)
    
        # Getting the company name
        company = session.getCompany()
        g.appLogger.info('Retrieved Company Name: ' + company)

    except CaptchaEncounteredException:
        g.appLogger.info('Captcha encountered before scraping began, resolve this issue before retrying')
        raise CaptchaEncounteredException(baseurl)

    reviewList = []
    reviewNum = 0
    pageNumber = 1
    nextPageExists = True

    try:

        #Seting a loop to go through the pages of a Glassdoor review page
        while nextPageExists:
            g.appLogger.info('Current Page: ' + str(pageNumber))
            g.appLogger.info('Reviews Processed: ' + str(reviewNum))
            reviews = session.getPageReviews()
            g.appLogger.info(str(len(reviews)) + ' reviews found on this page')

            for review in reviews:
                reviewNum += 1

                try:
                    reviewInfo = getReviewInfo(review)
                except TimeoutException as e:
                    g.appLogger.info("Timed out when querying for review info, skipping")

                except Exception as e:
                    g.appLogger.info('Unexpected error when querying for review info, skipping')
                    g.appLogger.debug(str(e))

                else:
                    reviewList.append(reviewInfo)

                nextPageExists = session.paginate()

            pageNumber += 1

    except CaptchaEncounteredException as e:
        g.appLogger.debug(str(e))
        continuationURL = alterURLPage(baseurl, pageNumber)
        g.appLogger.info('Captcha encountered, fix this on Glassdoor and retry starting at page ' + str(pageNumber) + '. Fix this and use url: ' + continuationURL)
        
        # Handling insertion of queried reviews before ending the process
        postToDatabase(reviewList, url, company)
        return(make_response(pageNumber))
    
    # Printing and returning the dictionary output
    postToDatabase(reviewList, url, company)

    return(make_response('Loaded ' + str(reviewNum) + ' reviews', 200))

# Simple function to alter the URL page, currently has a simple implementation that may grow in a future
# update to support pagination via URL as opposed to button press
def alterURLPage(url, page):
    url = url[:-4] + '_P' + str(page) + '.htm'
    return url

@controller.app_errorhandler(CaptchaEncounteredException)
def captchaError(exception):

    if exception.lastPage:
        continuationURL = alterURLPage(baseurl, exception.lastPage)
    else:
        continuationURL = baseurl
    
    responseDict = {"Message" : exception.message, "Continuation URL" : continuationURL}

    return make_response(responseDict, exception.code)

# Placeholder function to implement inputs into our database
def postToDatabase(reviewList, url, company):


    formattedReviews = []
    for review in reviewList:
        formattedVersion = (review['Review ID'], company, review['rating'], review['headline'], review['location'],
        review['employeeStatus'], review['Date Posted'], review['Job Title'], review['Pros'], review['Cons'])
        formattedReviews.append(formattedVersion)

    employerQuery = 'INSERT IGNORE INTO employer(companyName, url) VALUES (%s, %s)'
    g.dbcursor.execute(employerQuery, [company, url])

    reviewQuery = '''INSERT IGNORE INTO review(review_id, company, rating, headline, location,
                employeestatus, dateposted, jobtitle, pros, cons)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'''
    f = open("demofile2.txt", "a")
    f.write(str(formattedReviews))
    f.close()
    g.dbcursor.executemany(reviewQuery, formattedReviews)
    g.dbcon.connection.commit()
