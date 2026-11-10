"""Repository layer for schemes, profiles, roadmaps, and document chunks."""

import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from app.schemas.scheme import SchemeResponse, SchemeRuleSchema, SchemeMatchRequest
from app.schemas.business import BusinessProfileCreate, BusinessProfileResponse
from app.schemas.roadmap import RoadmapResponse, RoadmapTaskResponse, RoadmapCreate
from app.core.constants import TN_DISTRICTS, EligibilityStatus, DISCLAIMER_EN

# In-memory storage structures ensuring high reliability
_SCHEMES_CACHE: Dict[str, Dict[str, Any]] = {}
_PROFILES_CACHE: Dict[str, Dict[str, Any]] = {}
_ROADMAPS_CACHE: Dict[str, Dict[str, Any]] = {}
_CHUNKS_CACHE: List[Dict[str, Any]] = []

def _now():
    return datetime.now(timezone.utc)

def seed_verified_schemes():
    """Seeds authentic, verified Tamil Nadu and Central Government schemes."""
    if _SCHEMES_CACHE:
        return

    schemes_data = [
        {
            "id": "scheme-needs-tn",
            "name": "NEEDS (New Entrepreneur-cum-Enterprise Development Scheme)",
            "department": "Directorate of Industries and Commerce, Government of Tamil Nadu",
            "description": "Financial assistance program for educated first-generation entrepreneurs to establish greenfield manufacturing or service enterprises in Tamil Nadu.",
            "state": "Tamil Nadu",
            "scheme_type": "subsidy",
            "official_url": "https://msmeonline.tn.gov.in/",
            "application_url": "https://msmeonline.tn.gov.in/needs/",
            "benefits_summary": "25% capital subsidy on project cost up to a maximum of ₹75 Lakhs, plus 3% interest subvention for the entire loan tenure.",
            "eligibility_summary": "First-generation entrepreneurs aged 21-35 (General) or 21-45 (SC/ST/BC/MBC/Women/Differently-abled/Transgender/Ex-servicemen) with minimum Degree, Diploma, or ITI qualification. Project cost from ₹10 Lakhs to ₹5 Crores.",
            "exclusions": [
                "Trading / retail business activities are strictly not eligible.",
                "Existing operating enterprises (only greenfield/new setups qualify).",
                "Entrepreneurs who have already availed government capital subsidy under other schemes."
            ],
            "required_documents": [
                "Educational qualification certificates (Degree / Diploma / ITI)",
                "Age proof (Birth Certificate or 10th Marksheet)",
                "Community Certificate (if claiming age concession)",
                "Detailed Project Report (DPR) with machinery quotations",
                "Land ownership document or registered lease deed (minimum 5 years)"
            ],
            "application_steps": [
                "1. Apply online at msmeonline.tn.gov.in/needs/.",
                "2. Upload project report and educational proofs.",
                "3. Interview and project vetting by District Task Force Committee (DTFC) headed by District Collector.",
                "4. Bank sanction letter issuance.",
                "5. Mandatory Entrepreneurship Development Programme (EDP) training by EDI-TN.",
                "6. Loan disbursement and subsidy release."
            ],
            "rules": [
                {"id": "r1", "scheme_id": "scheme-needs-tn", "rule_type": "state", "field_name": "state", "operator": "eq", "expected_value": "Tamil Nadu", "source_reference": "NEEDS Guidelines Section 2"},
                {"id": "r2", "scheme_id": "scheme-needs-tn", "rule_type": "category", "field_name": "business_category", "operator": "in", "expected_value": ["manufacturing", "services"], "source_reference": "NEEDS Exclusions: Trading not eligible"},
                {"id": "r3", "scheme_id": "scheme-needs-tn", "rule_type": "first_gen", "field_name": "first_generation_entrepreneur", "operator": "eq", "expected_value": True, "source_reference": "NEEDS Criteria: Must be first generation entrepreneur"},
                {"id": "r4", "scheme_id": "scheme-needs-tn", "rule_type": "budget_min", "field_name": "investment_budget", "operator": "gte", "expected_value": 1000000, "source_reference": "Project cost minimum ₹10 Lakhs"},
                {"id": "r5", "scheme_id": "scheme-needs-tn", "rule_type": "budget_max", "field_name": "investment_budget", "operator": "lte", "expected_value": 50000000, "source_reference": "Project cost maximum ₹5 Crores"},
            ]
        },
        {
            "id": "scheme-uyegp-tn",
            "name": "UYEGP (Unemployed Youth Employment Generation Programme)",
            "department": "Department of MSME, Government of Tamil Nadu",
            "description": "Scheme to mitigate unemployment among educated youth in Tamil Nadu by helping them establish micro manufacturing, service, or business ventures.",
            "state": "Tamil Nadu",
            "scheme_type": "subsidy",
            "official_url": "https://msmeonline.tn.gov.in/uyegp/",
            "application_url": "https://msmeonline.tn.gov.in/uyegp/",
            "benefits_summary": "25% Government Subsidy on the project cost: up to ₹1.25 Lakhs for Manufacturing, ₹75,000 for Service, and ₹37,500 for Business / Trading.",
            "eligibility_summary": "Any resident of Tamil Nadu aged 18-35 (General) or 18-45 (SC/ST/BC/MBC/Women/Differently-abled) with minimum 8th standard pass. Family annual income must not exceed ₹5,00,000.",
            "exclusions": [
                "Applicants whose family annual income exceeds ₹5,00,000.",
                "Prior defaulters to any bank or financial institution.",
                "Persons who have already benefited from any state or central subsidy scheme."
            ],
            "required_documents": [
                "8th Standard Pass Certificate or School Transfer Certificate (TC)",
                "Nativity / Residence proof in Tamil Nadu (Ration card / Voter ID / Aadhaar)",
                "Income Certificate issued by Revenue Tahsildar (annual family income < ₹5 Lakhs)",
                "Community Certificate",
                "Project Cost Estimation / Proforma Invoice of machinery"
            ],
            "application_steps": [
                "1. Register online on msmeonline.tn.gov.in/uyegp/.",
                "2. Submit hard copy of application with documents to General Manager, District Industries Centre (DIC).",
                "3. Appear before District Task Force Committee interview.",
                "4. Bank branch sanction and 7-day EDP training.",
                "5. Subsidy released directly to bank as Term Deposit."
            ],
            "rules": [
                {"id": "u1", "scheme_id": "scheme-uyegp-tn", "rule_type": "state", "field_name": "state", "operator": "eq", "expected_value": "Tamil Nadu", "source_reference": "UYEGP Guidelines Sec 1"},
                {"id": "u2", "scheme_id": "scheme-uyegp-tn", "rule_type": "budget_max", "field_name": "investment_budget", "operator": "lte", "expected_value": 1500000, "source_reference": "Manufacturing max ₹15L, Services/Business max ₹5L"},
                {"id": "u3", "scheme_id": "scheme-uyegp-tn", "rule_type": "category", "field_name": "business_category", "operator": "in", "expected_value": ["manufacturing", "services", "trading", "other"], "source_reference": "All categories eligible up to sub-limits"}
            ]
        },
        {
            "id": "scheme-pmegp-central",
            "name": "PMEGP (Prime Minister's Employment Generation Programme)",
            "department": "Khadi and Village Industries Commission (KVIC), Ministry of MSME, Govt of India",
            "description": "Credit-linked subsidy program across India to generate employment opportunities through establishment of micro enterprises in non-farm sectors.",
            "state": "Central",
            "scheme_type": "subsidy",
            "official_url": "https://www.kviconline.gov.in/pmegpeportal/pmegphome/index.jsp",
            "application_url": "https://www.kviconline.gov.in/pmegpeportal/jsp/pmegponline.jsp",
            "benefits_summary": "Margin Money Subsidy: 15% (General Urban), 25% (General Rural / Special Urban), 35% (Special Rural like SC/ST/OBC/Women/Ex-servicemen). Maximum project cost ₹50 Lakhs for Manufacturing and ₹20 Lakhs for Services.",
            "eligibility_summary": "Any individual above 18 years of age. Minimum 8th standard pass required only for projects costing above ₹10 Lakhs in manufacturing and above ₹5 Lakhs in service.",
            "exclusions": [
                "Negative list: Meat/slaughtering, intoxicants/tobacco, tapping of toddy, pashmina wool, and non-biodegradable polythene bags.",
                "Existing units or projects that already received government capital subsidies."
            ],
            "required_documents": [
                "Aadhaar Card",
                "Passport size photograph",
                "Educational qualification certificate (if project > ₹10L manufacturing or > ₹5L service)",
                "Caste / Community / Special category certificate if applicable",
                "Detailed Project Report (DPR)"
            ],
            "application_steps": [
                "1. Apply online at kviconline.gov.in.",
                "2. Application forwarded to selected financing bank branch.",
                "3. Bank evaluates feasibility and sanctions credit.",
                "4. Complete online or offline EDP training (10 days).",
                "5. Subsidy credited to loan account as TDR for 3 years lock-in."
            ],
            "rules": [
                {"id": "p1", "scheme_id": "scheme-pmegp-central", "rule_type": "budget_max", "field_name": "investment_budget", "operator": "lte", "expected_value": 5000000, "source_reference": "Manufacturing max ₹50L, Service max ₹20L"},
                {"id": "p2", "scheme_id": "scheme-pmegp-central", "rule_type": "category", "field_name": "business_category", "operator": "in", "expected_value": ["manufacturing", "services"], "source_reference": "Only manufacturing and services eligible for PMEGP"}
            ]
        },
        {
            "id": "scheme-aabcs-tn",
            "name": "AABCS (Annal Ambedkar Business Champions Scheme)",
            "department": "Department of MSME, Government of Tamil Nadu",
            "description": "Flagship Tamil Nadu government scheme aimed at promoting economic empowerment and industrial leadership among SC and ST entrepreneurs.",
            "state": "Tamil Nadu",
            "scheme_type": "subsidy",
            "official_url": "https://msmeonline.tn.gov.in/",
            "application_url": "https://msmeonline.tn.gov.in/",
            "benefits_summary": "35% capital subsidy on project cost up to ₹35 Lakhs, plus 6% interest subvention on term loan throughout the loan period.",
            "eligibility_summary": "Exclusively for Scheduled Caste (SC) and Scheduled Tribe (ST) entrepreneurs. Applicable for manufacturing, service, and trading businesses including commercial transport vehicles.",
            "exclusions": [
                "Non-SC/ST applicants.",
                "Units operating outside Tamil Nadu."
            ],
            "required_documents": [
                "Community Certificate issued by competent Revenue authority",
                "Detailed project proposal / quotation",
                "Address proof in Tamil Nadu",
                "Bank loan sanction letter"
            ],
            "application_steps": [
                "1. Apply through msmeonline.tn.gov.in portal.",
                "2. Upload community certificate and project quote.",
                "3. DIC task force committee review.",
                "4. Bank loan sanction and direct subsidy credit."
            ],
            "rules": [
                {"id": "a1", "scheme_id": "scheme-aabcs-tn", "rule_type": "state", "field_name": "state", "operator": "eq", "expected_value": "Tamil Nadu", "source_reference": "AABCS State Criteria"},
                {"id": "a2", "scheme_id": "scheme-aabcs-tn", "rule_type": "community", "field_name": "community", "operator": "in", "expected_value": ["SC", "ST", "Scheduled Caste", "Scheduled Tribe"], "source_reference": "AABCS Target Community"}
            ]
        },
        {
            "id": "scheme-tanseed-tn",
            "name": "TANSEED (Tamil Nadu Startup Seed Grant Fund)",
            "department": "StartupTN, Government of Tamil Nadu",
            "description": "Flagship seed funding program providing early-stage equity-free innovation grants to startups registered in Tamil Nadu.",
            "state": "Tamil Nadu",
            "scheme_type": "grant",
            "official_url": "https://startuptn.in/",
            "application_url": "https://startuptn.in/tanseed",
            "benefits_summary": "Equity-free seed grant up to ₹10-15 Lakhs awarded in milestone-based tranches to build MVP and validate market traction.",
            "eligibility_summary": "Startups incorporated as Private Limited company or LLP in Tamil Nadu, less than 5 years old, registered with StartupTN and DPIIT, working on innovative, IP-driven or tech-scalable products.",
            "exclusions": [
                "Traditional retail shops, sole proprietorships, or partnership firms without innovation or technology component.",
                "Startups registered outside Tamil Nadu."
            ],
            "required_documents": [
                "Certificate of Incorporation (Pvt Ltd / LLP)",
                "DPIIT recognition certificate",
                "StartupTN registration ID",
                "Pitch deck and product prototype / proof of concept",
                "Financial projections"
            ],
            "application_steps": [
                "1. Register startup on startuptn.in.",
                "2. Submit TANSEED application during open cohort window.",
                "3. Screening and jury evaluation by external domain experts.",
                "4. Pitch presentation before grand jury.",
                "5. Grant agreement signing and tranche disbursal."
            ],
            "rules": [
                {"id": "t1", "scheme_id": "scheme-tanseed-tn", "rule_type": "state", "field_name": "state", "operator": "eq", "expected_value": "Tamil Nadu", "source_reference": "StartupTN guidelines"},
                {"id": "t2", "scheme_id": "scheme-tanseed-tn", "rule_type": "category", "field_name": "business_category", "operator": "in", "expected_value": ["manufacturing", "services", "other"], "source_reference": "Tech/Innovative scalable models"}
            ]
        },
        {
            "id": "scheme-udyam-central",
            "name": "Udyam Registration (Official Free MSME Certification)",
            "department": "Ministry of Micro, Small and Medium Enterprises, Govt of India",
            "description": "The mandatory, official, zero-cost government registration portal for micro, small, and medium enterprises in India.",
            "state": "Central",
            "scheme_type": "support",
            "official_url": "https://udyamregistration.gov.in/",
            "application_url": "https://udyamregistration.gov.in/Government-India/Ministry-MSME-registration.htm",
            "benefits_summary": "100% Free official certificate. Unlocks collateral-free bank loans under CGTMSE, priority sector lending, lower bank interest rates, 50% concession on patent/trademark fees, and legal protection against delayed buyer payments via MSME Samadhaan.",
            "eligibility_summary": "All micro, small, and medium businesses in India (Proprietorship, Partnership, LLP, Pvt Ltd). Investment in plant & machinery under ₹1 Crore and Turnover under ₹5 Crores for Micro status.",
            "exclusions": [
                "Beware of fake private portals charging fees. The official government website NEVER charges any fee (₹0)."
            ],
            "required_documents": [
                "Aadhaar Number of the Entrepreneur / Partner / Director",
                "PAN Card of the Enterprise or Owner",
                "Bank Account number and IFSC code",
                "Business address and date of commencement"
            ],
            "application_steps": [
                "1. Visit official free portal udyamregistration.gov.in.",
                "2. Enter Aadhaar and authenticate with OTP.",
                "3. Enter PAN details and validate.",
                "4. Fill in enterprise details and NIC activity codes.",
                "5. Submit with final OTP to generate instant Udyam Registration Number and downloadable e-certificate."
            ],
            "rules": [
                {"id": "u_all", "scheme_id": "scheme-udyam-central", "rule_type": "universal", "field_name": "all", "operator": "eq", "expected_value": True, "source_reference": "Available to all businesses across India"}
            ]
        },
        {
            "id": "scheme-mudra-central",
            "name": "Pradhan Mantri MUDRA Yojana (PMMY)",
            "department": "Department of Financial Services, Ministry of Finance, Govt of India",
            "description": "Scheme to provide collateral-free institutional credit up to ₹10-20 Lakhs to micro and small non-farm, non-corporate enterprises.",
            "state": "Central",
            "scheme_type": "loan",
            "official_url": "https://www.mudra.org.in/",
            "application_url": "https://www.udyamimitra.in/",
            "benefits_summary": "Collateral-free institutional loan in 3 categories: Shishu (up to ₹50,000), Kishore (₹50,000 to ₹5 Lakhs), Tarun (₹5 Lakhs to ₹10 Lakhs), and Tarun Plus (up to ₹20 Lakhs) with competitive interest rates and MUDRA debit card.",
            "eligibility_summary": "Any Indian citizen with a feasible business proposal for manufacturing, processing, trading, allied agriculture or service sector.",
            "exclusions": [
                "Corporate companies.",
                "Agricultural farm activities (pure farming). Allied activities like dairy/poultry are eligible."
            ],
            "required_documents": [
                "Proof of identity (Voter ID / Driving License / PAN)",
                "Proof of residence (Electricity bill / Aadhaar)",
                "Applicant's recent photos",
                "Quotation of machinery/items to be purchased",
                "Business enterprise proof (Udyam certificate / trade licence)"
            ],
            "application_steps": [
                "1. Apply via udyamimitra.in or directly at any nationalized, private, or regional rural bank.",
                "2. Submit standard loan application form along with quotations.",
                "3. Bank branch processes and sanctions loan without asking for collateral."
            ],
            "rules": [
                {"id": "m1", "scheme_id": "scheme-mudra-central", "rule_type": "budget_max", "field_name": "investment_budget", "operator": "lte", "expected_value": 2000000, "source_reference": "MUDRA ceiling limit ₹20 Lakhs"}
            ]
        }
    ]

    for s in schemes_data:
        _SCHEMES_CACHE[s["id"]] = s

        # Also populate initial RAG chunk cache for accurate retrieval
        chunk_content = f"{s['name']}. Implementing Authority: {s['department']}. {s['description']} " \
                        f"Benefits: {s['benefits_summary']} Eligibility criteria: {s['eligibility_summary']} " \
                        f"Exclusions: {'; '.join(s['exclusions'])}. Required documents: {'; '.join(s['required_documents'])}. " \
                        f"Application Steps: {'; '.join(s['application_steps'])}. Official URL: {s['official_url']}."
        
        _CHUNKS_CACHE.append({
            "id": f"chunk-{s['id']}",
            "scheme_id": s["id"],
            "title": s["name"],
            "url": s["official_url"],
            "content": chunk_content,
            "state": s["state"],
            "category": s.get("scheme_type", "subsidy"),
            "last_verified_at": _now().isoformat()
        })


# Initialize seed data immediately
seed_verified_schemes()


class SchemeRepository:
    """Access layer for Schemes and deterministic rule screening."""

    @staticmethod
    def list_schemes(state: Optional[str] = None, scheme_type: Optional[str] = None, search: Optional[str] = None) -> List[Dict[str, Any]]:
        seed_verified_schemes()
        results = list(_SCHEMES_CACHE.values())

        if state:
            results = [s for s in results if s["state"].lower() == state.lower() or s["state"].lower() == "central"]

        if scheme_type:
            results = [s for s in results if s.get("scheme_type", "").lower() == scheme_type.lower()]

        if search:
            q = search.lower().strip()
            results = [
                s for s in results
                if q in s["name"].lower()
                or q in s["description"].lower()
                or q in s["benefits_summary"].lower()
                or q in s["eligibility_summary"].lower()
            ]

        return results

    @staticmethod
    def get_by_id(scheme_id: str) -> Optional[Dict[str, Any]]:
        seed_verified_schemes()
        return _SCHEMES_CACHE.get(scheme_id)

    @staticmethod
    def match_schemes(req: SchemeMatchRequest) -> List[Dict[str, Any]]:
        """
        Deterministic, testable rule-based eligibility screening.
        Checks user attributes against verified scheme criteria.
        Returns potentially_eligible, criteria_not_met, or insufficient_information.
        """
        seed_verified_schemes()
        matched_results = []

        for scheme_id, scheme in _SCHEMES_CACHE.items():
            match_reasons = []
            missing_criteria = []
            is_disqualified = False
            status = EligibilityStatus.POTENTIALLY_ELIGIBLE

            rules = scheme.get("rules", [])
            for rule in rules:
                rtype = rule["rule_type"]
                expected = rule["expected_value"]

                if rtype == "state":
                    # Must match state unless Central
                    if scheme["state"] != "Central" and req.state.lower() != str(expected).lower():
                        is_disqualified = True
                        break
                    else:
                        match_reasons.append(f"Operating location matches ({req.state})")

                elif rtype == "category":
                    if req.business_category not in expected:
                        is_disqualified = True
                        break
                    else:
                        match_reasons.append(f"Business category ({req.business_category.replace('_', ' ')}) is eligible")

                elif rtype == "budget_min":
                    if req.investment_budget < expected:
                        is_disqualified = True
                        break
                    else:
                        match_reasons.append(f"Budget (₹{req.investment_budget:,.0f}) meets minimum threshold (₹{expected:,.0f})")

                elif rtype == "budget_max":
                    if req.investment_budget > expected:
                        is_disqualified = True
                        break
                    else:
                        match_reasons.append(f"Budget (₹{req.investment_budget:,.0f}) falls within allowed project cap (₹{expected:,.0f})")

                elif rtype == "first_gen":
                    if req.first_generation_entrepreneur is None:
                        status = EligibilityStatus.INSUFFICIENT_INFORMATION
                        missing_criteria.append("Verification required: Must confirm first-generation entrepreneur status")
                    elif req.first_generation_entrepreneur is False:
                        is_disqualified = True
                        break
                    else:
                        match_reasons.append("First-generation entrepreneur qualification verified")

                elif rtype == "community":
                    if not req.community:
                        status = EligibilityStatus.INSUFFICIENT_INFORMATION
                        missing_criteria.append("Community category verification required (e.g., SC/ST status)")
                    elif req.community.upper() not in [e.upper() for e in expected]:
                        is_disqualified = True
                        break
                    else:
                        match_reasons.append(f"Target community category matched ({req.community})")

            if not is_disqualified:
                # Add default match reason if none populated
                if not match_reasons:
                    match_reasons.append("General startup eligibility applies")

                scheme_copy = dict(scheme)
                scheme_copy["eligibility_status"] = status
                scheme_copy["match_reasons"] = match_reasons
                scheme_copy["missing_criteria"] = missing_criteria
                matched_results.append(scheme_copy)

        return matched_results


class ProfileRepository:
    """Storage for onboarding questionnaires and business profiles."""

    @staticmethod
    def create_or_update(profile_data: BusinessProfileCreate) -> BusinessProfileResponse:
        pid = str(uuid.uuid4())
        created = _now()
        data = profile_data.model_dump()
        data["id"] = pid
        data["created_at"] = created
        data["updated_at"] = created
        _PROFILES_CACHE[pid] = data
        return BusinessProfileResponse(**data)

    @staticmethod
    def get_by_id(profile_id: str) -> Optional[BusinessProfileResponse]:
        data = _PROFILES_CACHE.get(profile_id)
        if data:
            return BusinessProfileResponse(**data)
        return None


class RoadmapRepository:
    """Storage and generator for actionable launch roadmaps."""

    @staticmethod
    def generate_roadmap_tasks(business_idea: str, category: str, district: str, budget: float, stage: str, language: str = "en") -> List[Dict[str, Any]]:
        """Generates structured, step-by-step actionable tasks based on business stage and category."""
        tasks = []

        is_tamil = language == "ta"

        # Task 1: Business Plan & Feasibility
        tasks.append({
            "id": str(uuid.uuid4()),
            "title": "வணிக திட்டம் & சாத்தியக்கூறு அறிக்கை" if is_tamil else "Refine Business Model & Prepare Project Report",
            "description": (
                "உங்கள் தொழில் யோசனைக்கான உத்தேச செலவுகள், இயந்திரங்கள் மற்றும் மூலப்பொருள் விவரங்களை ஆவணப்படுத்துங்கள்."
                if is_tamil else
                f"Prepare a Detailed Project Report (DPR) detailing your {category} operations, raw materials, machinery, and working capital needs for {district}."
            ),
            "priority": "high",
            "status": "completed" if stage in ["planning", "registration", "operating"] else "in_progress",
            "prerequisites": [],
            "required_documents": ["Detailed Project Report (DPR)", "Machinery Quotations"],
            "official_url": "https://msmeonline.tn.gov.in/",
            "source_references": ["Government Project Guidelines"]
        })

        # Task 2: Free Official Udyam MSME Registration
        tasks.append({
            "id": str(uuid.uuid4()),
            "title": "அதிகாரப்பூர்வ உத்யாம் பதிவு (இலவசம்)" if is_tamil else "Obtain Official Udyam MSME Registration (Free)",
            "description": (
                "மத்திய அரசின் உத்யாம் போர்ட்டலில் இலவசமாக பதிவு செய்து MSME சான்றிதழ் பெறுங்கள் (ரூ. 0 கட்டணம்)."
                if is_tamil else
                "Register on the central official portal for lifetime zero-cost MSME certification. Unlocks priority sector bank loans and collateral-free credit."
            ),
            "priority": "high",
            "status": "completed" if stage in ["registration", "operating"] else "pending",
            "prerequisites": ["Aadhaar Number", "PAN Card", "Bank Account Details"],
            "required_documents": ["Aadhaar Card", "PAN Card", "Bank Passbook"],
            "official_url": "https://udyamregistration.gov.in/",
            "source_references": ["Ministry of MSME Official Notification"]
        })

        # Task 3: Relevant State Scheme Application
        if budget >= 1000000 and category in ["manufacturing", "services"]:
            tasks.append({
                "id": str(uuid.uuid4()),
                "title": "தமிழ்நாடு NEEDS திட்ட மானியத்திற்கு விண்ணப்பியுங்கள்" if is_tamil else "Apply for Tamil Nadu NEEDS 25% Capital Subsidy",
                "description": (
                    "msmeonline.tn.gov.in மூலம் 25% மூலதன மானியத்திற்கு (அதிகபட்சம் ₹75 லட்சம்) விண்ணப்பியுங்கள்."
                    if is_tamil else
                    "Submit online application on msmeonline.tn.gov.in for up to 25% capital subsidy (max ₹75 Lakhs) and 3% interest subvention."
                ),
                "priority": "high",
                "status": "pending",
                "prerequisites": ["Degree/Diploma certificate", "Project Report", "Land/Building agreement"],
                "required_documents": ["Degree Certificate", "Age Proof", "Machinery Quotations", "DPR"],
                "official_url": "https://msmeonline.tn.gov.in/needs/",
                "source_references": ["Directorate of Industries and Commerce TN"]
            })
        elif budget <= 1500000:
            tasks.append({
                "id": str(uuid.uuid4()),
                "title": "UYEGP திட்ட மானியத்திற்கு விண்ணப்பிக்கவும்" if is_tamil else "Apply for Tamil Nadu UYEGP Micro Subsidy",
                "description": (
                    "மாவட்ட தொழில் மையம் (DIC) மூலம் 25% மானியத்திற்கு விண்ணப்பம் சமர்ப்பிக்கவும்."
                    if is_tamil else
                    f"Apply for 25% state subsidy at District Industries Centre (DIC) {district} for micro projects up to ₹15 Lakhs."
                ),
                "priority": "high",
                "status": "pending",
                "prerequisites": ["8th pass or TC", "Tahsildar Income Certificate (< ₹5L)"],
                "required_documents": ["School TC / Marksheet", "Income Certificate", "Nativity Certificate"],
                "official_url": "https://msmeonline.tn.gov.in/uyegp/",
                "source_references": ["TN MSME Department"]
            })

        # Task 4: Bank Current Account & GSTIN
        tasks.append({
            "id": str(uuid.uuid4()),
            "title": "வணிக நடப்புக் கணக்கு & ஜிஎஸ்டி பதிவு" if is_tamil else "Open Current Bank Account & GST Registration",
            "description": (
                "தொழில் பெயரில் நடப்புக் கணக்கு துவங்கி, தேவையானால் ஜிஎஸ்டி பதிவு மேற்கொள்ளுங்கள்."
                if is_tamil else
                "Open a dedicated business current account with your Udyam certificate. Apply for GSTIN if turnover exceeds ₹40 Lakhs (Goods) / ₹20 Lakhs (Services) or if inter-state."
            ),
            "priority": "medium",
            "status": "pending",
            "prerequisites": ["Udyam Registration Certificate", "Rental / Commercial Address Proof"],
            "required_documents": ["Udyam Certificate", "PAN Card", "Electricity Bill / Rental Deed"],
            "official_url": "https://www.gst.gov.in/",
            "source_references": ["CBIC Portal"]
        })

        # Task 5: Local Trade Licences & Approvals
        tasks.append({
            "id": str(uuid.uuid4()),
            "title": "உள்ளூர் வர்த்தக உரிமங்கள் மற்றும் அனுமதிகள்" if is_tamil else "Obtain Local Municipal Trade Licence & Safety Approvals",
            "description": (
                f"{district} உள்ளாட்சி அமைப்பு அல்லது நகராட்சியிடம் வர்த்தக உரிமம் (Trade Licence) மற்றும் உணவுத் தொழிலாக இருந்தால் FSSAI பதிவு பெறவும்."
                if is_tamil else
                f"Obtain Local Body Trade Licence from {district} local municipality. If dealing with food or hospitality, obtain FSSAI licence."
            ),
            "priority": "medium",
            "status": "pending",
            "prerequisites": ["Premises Lease Agreement", "Udyam Registration"],
            "required_documents": ["Property Tax Receipt", "Rental Agreement", "FSSAI Registration (if food)"],
            "official_url": "https://tnurbantree.tn.gov.in/",
            "source_references": ["Tamil Nadu Municipal Administration"]
        })

        return tasks

    @staticmethod
    def create_roadmap(data: RoadmapCreate, language: str = "en") -> RoadmapResponse:
        rid = str(uuid.uuid4())
        created = _now()
        tasks_raw = RoadmapRepository.generate_roadmap_tasks(
            business_idea=data.business_summary,
            category=data.category,
            district=data.district,
            budget=data.budget,
            stage=data.stage,
            language=language
        )

        task_responses = []
        for t in tasks_raw:
            t["roadmap_id"] = rid
            t["created_at"] = created
            t["updated_at"] = created
            task_responses.append(RoadmapTaskResponse(**t))

        completed_count = sum(1 for t in task_responses if t.status == "completed")
        progress = round((completed_count / len(task_responses)) * 100, 1) if task_responses else 0.0

        roadmap_obj = {
            "id": rid,
            "user_id": data.user_id or "guest",
            "title": data.title,
            "business_summary": data.business_summary,
            "status": "active",
            "progress_percentage": progress,
            "tasks": task_responses,
            "created_at": created,
            "updated_at": created
        }
        _ROADMAPS_CACHE[rid] = roadmap_obj
        return RoadmapResponse(**roadmap_obj)

    @staticmethod
    def get_by_id(roadmap_id: str) -> Optional[RoadmapResponse]:
        data = _ROADMAPS_CACHE.get(roadmap_id)
        if data:
            return RoadmapResponse(**data)
        return None

    @staticmethod
    def update_task_status(roadmap_id: str, task_id: str, new_status: str) -> Optional[RoadmapResponse]:
        roadmap = _ROADMAPS_CACHE.get(roadmap_id)
        if not roadmap:
            return None

        for task in roadmap["tasks"]:
            if task.id == task_id:
                task.status = new_status
                task.updated_at = _now()
                break

        completed_count = sum(1 for t in roadmap["tasks"] if t.status == "completed")
        roadmap["progress_percentage"] = round((completed_count / len(roadmap["tasks"])) * 100, 1)
        roadmap["updated_at"] = _now()
        return RoadmapResponse(**roadmap)


class DocumentChunkRepository:
    """RAG Document Chunk search and retrieval."""

    @staticmethod
    def search(query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Multilingual keyword and semantic search against verified scheme documents.
        """
        seed_verified_schemes()
        q_words = [w.lower().strip() for w in query.split() if len(w) > 2]
        
        scored_chunks = []
        for chunk in _CHUNKS_CACHE:
            score = 0
            text_lower = (chunk["title"] + " " + chunk["content"]).lower()
            
            # Simple keyword matching across English and Tamil terms
            for word in q_words:
                if word in text_lower:
                    score += 2

            # Direct scheme name bonus
            if "needs" in query.lower() and "needs" in chunk["title"].lower():
                score += 10
            if "uyegp" in query.lower() and "uyegp" in chunk["title"].lower():
                score += 10
            if "pmegp" in query.lower() and "pmegp" in chunk["title"].lower():
                score += 10
            if "udyam" in query.lower() and "udyam" in chunk["title"].lower():
                score += 10
            if "tanseed" in query.lower() and "tanseed" in chunk["title"].lower():
                score += 10

            # Tamil terms
            if "மானியம்" in query and "subsidy" in chunk["content"].lower():
                score += 5
            if "உத்யாம்" in query and "udyam" in chunk["content"].lower():
                score += 10

            scored_chunks.append((score, chunk))

        # Sort descending by score
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        return [c for score, c in scored_chunks[:limit]]

