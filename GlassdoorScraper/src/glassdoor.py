from selenium import webdriver
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains
import datetime
import time
import json


# The locations of certain data elements on a glassdoor review change are subject to change as they develop their platform,
# I have put all of the class information being used in getReviewInfo to pull data out of the HTML in one dict for ease of update.
# Notable exception being that the location data for the pros and cons section are not included here
locationDict = dict(
    review = "empReview",
    id = "id",
    rating = "ratingNumber",
    headline = "reviewLink",
    employeeStatus = "pt-xsm pt-md-0 css-1qxtz39 eg4psks0",
    location = "authorLocation",
    titleAndDate = "authorJobTitle",
    nextButton = "nextButton"
)


class GlassdoorSession():

    # Main webdriver used in execution
    sessionDriver = None

    # WaitDriverWait instance to handle explicit waits for some elements
    waitDriver = None

    def __init__(self):

        # Setting options for our webdriver
        options = webdriver.ChromeOptions()
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--incognito')
        options.add_argument('--headless')
        options.add_argument('--disable-dev-shm-usage')

        # Instantiating our drivers
        self.sessionDriver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
        self.waitDriver = WebDriverWait(self.sessionDriver, 30)

    # Simple function to switch current page of sessionDriver
    def getPage(self, url):
        self.sessionDriver.get(url)

    # Function to automate the sign in process
    def authenticate(self):

        # Trying to read information from the secrets.json file, located in the GlassdoorScraper folder
        try:
            with open('secret.json') as f:
                d = json.loads(f.read())
                userEmail = d['email']
                userPassword = d['password']
        except FileNotFoundError:
            raise Exception('Secret JSON not found')

        # Switching page to the Glassdoor login screen
        self.getPage('https://www.glassdoor.com/profile/login_input.htm')

        # Given that we know that only one email and password input is expected to be on screen,
        # searching by input type is more resiliant than searching by a class name which may change
        emailInput = self.sessionDriver.find_element_by_css_selector('input[type="email"]')
        passwordInput = self.sessionDriver.find_element_by_css_selector('input[type="password"]')
        submitButton = self.sessionDriver.find_element_by_css_selector('button[type="submit"]')


        # Creating, populating, and performing an action chain to sign into Glassdoor
        signIn = ActionChains(self.sessionDriver)
        signIn.move_to_element(emailInput).send_keys(userEmail)
        signIn.move_to_element(passwordInput).send_keys(userPassword)
        signIn.click(on_element = submitButton)
        signIn.perform()

    # Getting an array of all reviews on a page
    def getPageReviews(self):

        html_soup = BeautifulSoup(self.sessionDriver.page_source, 'html.parser')
        reviews = html_soup.find_all(class_=locationDict['review'])
        return reviews

    # Function to automate navigation to the next page
    def paginate(self):

        try:
            nextButton = self.waitDriver.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.' + locationDict['nextButton'])))
        except TimeoutException:
            return False

        if not nextButton.is_enabled():
            return False

        ActionChains(self.sessionDriver).click(on_element = nextButton).perform()

        # While explicit waitDrivers and implicit wait statements on sessionDriver usually handle delays fairly well, there
        # it's never completely consistent. This eliminates the inconsistency of page loads and also paces requests as to not
        # be flagged as malicious by Glassdoor
        time.sleep(3)

        # Here, we wait until all reviews are loaded properly
        self.waitDriver.until(EC.visibility_of_all_elements_located((By.CSS_SELECTOR, 'li.' + locationDict['review'])))

        return True

# Note: In normal execution this may set a required variable to None, filtering used input to only successful results will be
# handled in the Database insertion set with NOT NULL constraints
def getFromHTML(reviewInfo, review, valueName, location):
    try:
        reviewInfo[valueName] = review.find(class_=location).contents[0]
    except AttributeError:
        print(valueName + ' could not be found, setting to None')
        reviewInfo[valueName] = None

def getReviewInfo(review):

    # Dict holding information on the current review
    reviewInfo = {}

    # Internal ID used by Glassdoor for reviews, to be used
    reviewInfo['Review ID'] = review.get(locationDict['id'])

    # Overall star rating (From 1-5) of the review
    getFromHTML(reviewInfo, review, 'rating', locationDict['rating'])

    # Headline of the review
    getFromHTML(reviewInfo, review, 'headline', locationDict['headline'])

    # Reported location of the user's position, can be null
    getFromHTML(reviewInfo, review, 'location', locationDict['location'])

    # Reported Status of the employee
    getFromHTML(reviewInfo, review, 'employeeStatus', locationDict['employeeStatus'])

    # Gets the reported job title of the reviewer and the date the review was posted
    getFromHTML(reviewInfo, review, 'titleAndDate', locationDict['titleAndDate'])

    # Getting the pros and cons sections of the review
    reviewInfo['Pros'] = review.find(attrs={'data-test' : 'pros'}).contents[0]
    reviewInfo['Cons'] = review.find(attrs={'data-test' : 'cons'}).contents[0]

    # Splitting the titleAndDate variable into it's requisite parts
    # Only splitting once to accomidate people using a - in their job title
    titleAndDate = reviewInfo.pop('titleAndDate').split('-', 1)
    reviewInfo["date posted"] = formatDate(titleAndDate[0].strip())
    reviewInfo["job title"] = titleAndDate[1].strip()

    return reviewInfo

# Function to convert Glassdoor datestring to SQL datestring
def formatDate(date):
    '''
    Converting a date string of format MMM DD, YYYY to the SQL standard of
    YYYY-MM-DD
    '''
    # datetime.strptime deals with 3 letter representations, Sept is the only value that Glassdoor uses that isn't compliant
    if date.startswith("Sept"):
        date = date.replace('t', '', 1)

    dateFormatted = datetime.datetime.strptime(date, "%b %d, %Y")
    dateFormatted = dateFormatted.strftime("%Y-%m-%d")
    return dateFormatted

