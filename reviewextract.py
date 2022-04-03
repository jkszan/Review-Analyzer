from bs4 import BeautifulSoup
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
import datetime


# quote_page = 'https://www.glassdoor.ca/Reviews/{Name}-Reviews-E{placeID}.htm'
# We must find way to translate company name to URL / placeID

class GlassdoorSession():

    # Declaring some session variable values 
    sessionDriver = None

    # Class identifiers for some Glassdoor webpage elements, these are subject to change over time when Glassdoor
    # is updated
    nextPageButtonClass = 'nextButton css-1hq9k8 e13qs2071'
    reviewClass = 'gdReview'


    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--incognito')
        options.add_argument('--headless')
        
        self.sessionDriver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
        self.sessionDriver.implicitly_wait(15)
    
    def getPage(self, url):
        self.sessionDriver.get(url)

    def getPageReviews(self):
        html_soup = BeautifulSoup(self.sessionDriver.page_source, 'html.parser')
        reviews = html_soup.find_all(class_="empReview")
        return reviews

    def paginate(self):
        self.sessionDriver.getElementsByClassName(nextPageButtonClass)[0].click()

# Note: In normal execution this may set a required variable to None, filtering used input to only successful results will be
# handled in the Database insertion set with NOT NULL constraints
def getFromHTML(reviewInfo, valueName, location):
    try:
        reviewInfo[valueName] = review.find(class_=location).contents[0]
    except AttributeError:
        print(valueName + ' could not be found, setting to None')
        reviewInfo[valueName] = None


# The locations of certain data elements on a glassdoor review change are subject to change as they develop their platform,
# I have put all of the class information being used in getReviewInfo to pull data out of the HTML in one dict for ease of update.
# Notable exception being that the location data for the pros and cons section are not included here
locationDict = dict(
    id = "id",
    rating = "ratingNumber",
    headline = "reviewLink",
    employeeStatus = "pt-xsm pt-md-0 css-1qxtz39 eg4psks0",
    location = "authorLocation",
    titleAndDate = "authorJobTitle"
)

def getReviewInfo(review):


    # REQUIRED VALUES IN A REVIEW:
    # Overall Rating (1-5 stars, integer)
    # Employee Status (Current or Former)
    # Review Headline (String, any length)
    # Pros Section (String, min 5 words)
    # Cons Section (String, min 5 words)
    # Job Function (String, very general dropdown selection of functional area)
    # Date Posted, in a user friendly format of (MMM DD, YYYY) where MMM is a shortform of the month name
    # Review ID, internal value stored by Glassdoor to identify reviews

    # OPTIONAL VALUES IN A REVIEW:
    # Job Title (String), if not provided this defaults to Anonymous Employee
    # Ratings for different extra categories (Compensation & Benefits, Career Opprotunities, etc) (1-5 stars, integer) - Not done yet
    # CEO Performance, Recommend to Friend, 6 month outlook (Boolean yes/no or Neutral). Recommend can be abstained from but not selected as neutral
    # Length of Employment
    # Location

    # Preferably, queryable: Job Title, Location, Rating** and Date Posted

    # All have 5 stars, we need to differntiate off of a css gradient
    #for extraCategory in review.find_all('li'):
    #    categoryName = extraCategory.find('div').contents[0]
    #    print(categoryName)
    #    categoryStars = len(extraCategory.find_all('span'))
    #    reviewInfo[categoryName] = categoryStars

    # This seems to be the id used internally by Glassdoor for reviews, we can be reasonably certain that we are denying
    # duplicates using a combination of this and the company place ID as a primary key for our database entries

    # For the most part we can generalize our data gathering to be ran in a single helper function, but there are a few special
    # cases we need to take care of manually
    reviewInfo = {}
    reviewInfo["Review ID"] = review.get(locationDict['id'])
    getFromHTML(reviewInfo, 'rating', locationDict['rating'])
    getFromHTML(reviewInfo, 'headline', locationDict['headline'])
    getFromHTML(reviewInfo, 'location', locationDict['location'])
    getFromHTML(reviewInfo, 'employeeStatus', locationDict['employeeStatus'])
    getFromHTML(reviewInfo, 'titleAndDate', locationDict['titleAndDate'])
    reviewInfo['Pros'] = review.find(attrs={'data-test' : 'pros'}).contents[0]
    reviewInfo['Cons'] = review.find(attrs={'data-test' : 'cons'}).contents[0]

    # Only splitting once here to accomidate people using a - in their job title 
    titleAndDate = reviewInfo.pop('titleAndDate').split('-', 1)
    reviewInfo["date posted"] = formatDate(titleAndDate[0].strip())
    reviewInfo["job title"] = titleAndDate[1].strip()




    return reviewInfo

def formatDate(date):
    '''
    Converting a date string of format MMM DD, YYYY to the SQL standard of
    YYYY-MM-DD
    '''
    dateFormatted = datetime.datetime.strptime(date, "%b %d, %Y")
    dateFormatted = dateFormatted.strftime("%Y-%m-%d")
    return dateFormatted


# Desired URL
url = 'https://www.glassdoor.ca/Reviews/Electronic-Arts-Reviews-E1628.htm'

session = GlassdoorSession()
session.getPage(url)
reviews = session.getPageReviews()

for review in reviews:
    reviewInfo = getReviewInfo(review)
    print(reviewInfo)
