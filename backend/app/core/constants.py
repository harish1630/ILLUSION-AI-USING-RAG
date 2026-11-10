"""Constants for ILLUSION AI platform."""

from typing import Final, List, Dict

# Supported languages
SUPPORTED_LANGUAGES: Final[List[str]] = ["en", "ta"]
DEFAULT_LANGUAGE: Final[str] = "en"

# Business categories
BUSINESS_CATEGORIES: Final[List[str]] = [
    "manufacturing",
    "services",
    "trading",
    "agriculture_allied",
    "other",
]

# Business stages
BUSINESS_STAGES: Final[List[str]] = [
    "idea",
    "planning",
    "registration",
    "operating",
]

# Eligibility screening statuses
class EligibilityStatus:
    POTENTIALLY_ELIGIBLE = "potentially_eligible"
    CRITERIA_NOT_MET = "criteria_not_met"
    INSUFFICIENT_INFORMATION = "insufficient_information"
    VERIFICATION_REQUIRED = "verification_required"

# Official scheme and financial disclaimers
DISCLAIMER_EN: Final[str] = (
    "Disclaimer: illusion AI provides provisional, informational guidance based on available official documentation. "
    "Eligibility determination, loan sanctions, and subsidy approvals are solely at the discretion of the respective "
    "government authorities and financial institutions. Always verify current guidelines on official portals."
)

DISCLAIMER_TA: Final[str] = (
    "பொறுப்புத்துறப்பு: illusion AI கிடைக்கக்கூடிய அதிகாரப்பூர்வ ஆவணங்களின் அடிப்படையில் தற்காலிக தகவல்களை மட்டுமே வழங்குகிறது. "
    "திட்ட தகுதி, கடன் மற்றும் மானிய அனுமதிகள் சம்பந்தப்பட்ட அரசு துறைகள் மற்றும் வங்கிகளின் இறுதி முடிவுக்கு உட்பட்டது. "
    "அதிகாரப்பூர்வ போர்ட்டல்களில் நடப்பு வழிகாட்டுதல்களை உறுதிப்படுத்திக் கொள்ளவும்."
)

# Common Tamil Nadu Districts
TN_DISTRICTS: Final[List[str]] = [
    "Ariyalur", "Chengalpattu", "Chennai", "Coimbatore", "Cuddalore", "Dharmapuri",
    "Dindigul", "Erode", "Kallakurichi", "Kanchipuram", "Kanyakumari", "Karur",
    "Krishnagiri", "Madurai", "Mayiladuthurai", "Nagapattinam", "Namakkal",
    "Nilgiris", "Perambalur", "Pudukkottai", "Ramanathapuram", "Ranipet",
    "Salem", "Sivaganga", "Tenkasi", "Thanjavur", "Theni", "Thoothukudi",
    "Tiruchirappalli", "Tirunelveli", "Tirupathur", "Tiruppur", "Tiruvallur",
    "Tiruvannamalai", "Tiruvarur", "Vellore", "Viluppuram", "Virudhunagar"
]

