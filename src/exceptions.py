class LocationVerificationError(Exception):
    """Raised when the Amazon location verification fails."""
    pass

class CaptchaDetectedError(Exception):
    """Raised when a captcha is detected on the page."""
    pass
