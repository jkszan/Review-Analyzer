from flask import Flask, request, make_response
from src.glassdoor import GlassdoorSession, getReviewInfo
import sys

# Instantiating our app
app = Flask(__name__)

# Setting route for loading reviews
@app.route('/loadReviews',
    strict_slashes=False,
    methods=['GET'],
    defaults = dict(
        url = None
    ))
def loadReviews(url):

    # Getting input for url
    url = request.args.get('url', url)

    # Throwing error if url is not provided
    if not url:
        return make_response('No url provided', 400)

    # Creating session for scraping data from Glassdoor
    session = GlassdoorSession()

    # Signing into account provided in the secrets.json file
    session.authenticate()

    # Navigating WebDriver to the supplied url
    session.getPage(url)

    reviewList = []
    reviewNum=0

    #Seting a loop to go through the pages of a Glassdoor review page
    while session.paginate():
        print(50*"-")
        print(reviewNum)
        print(50*"-")
        reviews = session.getPageReviews()
        for review in reviews:
            reviewNum += 1
            reviewInfo = getReviewInfo(review)
            reviewList.append(reviewInfo)

    # Printing and returning the dictionary output
    print(reviewList)
    postToDatabase(reviewList)
    return(make_response('Loaded ' + str(reviewNum) + ' reviews', 200))

# Placeholder function to implement inputs into our database
def postToDatabase(reviewList):
    pass
