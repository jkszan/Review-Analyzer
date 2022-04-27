# Simple exception for CaptchaErrors, printout behavior is defined in seperate errorhandler
class CaptchaEncounteredException(Exception):

    lastPage = None
    code = 405
    continuationURL = None
    def __init__(self, pageNum=None):
        super()
        self.lastPage = pageNum
        self.message = 'Captcha error encountered, please fix this and restart the application with the supplied url'

