export type Language = "en" | "ta";

export interface Translations {
  brandName: string;
  tagline: string;
  nav: {
    home: string;
    onboarding: string;
    schemes: string;
    chat: string;
    roadmap: string;
    language: string;
  };
  hero: {
    badge: string;
    titleLine1: string;
    titleLine2: string;
    description: string;
    primaryCta: string;
    secondaryCta: string;
    trustText: string;
  };
  features: {
    title: string;
    subtitle: string;
    f1Title: string;
    f1Desc: string;
    f2Title: string;
    f2Desc: string;
    f3Title: string;
    f3Desc: string;
    f4Title: string;
    f4Desc: string;
  };
  howItWorks: {
    title: string;
    subtitle: string;
    step1Title: string;
    step1Desc: string;
    step2Title: string;
    step2Desc: string;
    step3Title: string;
    step3Desc: string;
    step4Title: string;
    step4Desc: string;
  };
  trust: {
    title: string;
    description: string;
    source1: string;
    source2: string;
    source3: string;
    source4: string;
    source5: string;
  };
  disclaimer: string;
  footer: {
    rights: string;
    privacy: string;
    terms: string;
    officialPortals: string;
  };
}

export const translations: Record<Language, Translations> = {
  en: {
    brandName: "illusion AI",
    tagline: "Empowering First-Time Entrepreneurs",
    nav: {
      home: "Home",
      onboarding: "Start Journey",
      schemes: "Govt Schemes",
      chat: "AI Advisor",
      roadmap: "My Roadmap",
      language: "தமிழ்",
    },
    hero: {
      badge: "Tamil Nadu & Central Govt Startup Intelligence",
      titleLine1: "Your Business Journey",
      titleLine2: "Starts Here.",
      description:
        "Turn complicated business procedures, subsidies, and government schemes into a simple, personalized, step-by-step launch roadmap. Built for aspiring founders in Tamil Nadu.",
      primaryCta: "Start My Business Journey",
      secondaryCta: "Explore Government Schemes",
      trustText: "Grounded exclusively in official Tamil Nadu & Government of India portals",
    },
    features: {
      title: "Everything You Need to Launch with Confidence",
      subtitle: "Tailored specifically for first-time entrepreneurs and small business owners.",
      f1Title: "Beginner-Friendly Onboarding",
      f1Desc: "A straightforward questionnaire that captures your business idea, district, and budget without jargon or sensitive credentials.",
      f2Title: "AI Business Startup Guide",
      f2Desc: "Evaluate startup costs, working capital, Udyam registration, and specific trade licences required for your activity.",
      f3Title: "Govt Scheme & Subsidy Matcher",
      f3Desc: "Instantly discover potentially relevant schemes (NEEDS, UYEGP, PMEGP, Startup TN) with verified criteria and exclusions.",
      f4Title: "Personalized Action Roadmap",
      f4Desc: "Get a clear checklist of actionable tasks, required documents, and direct links to official application portals.",
    },
    howItWorks: {
      title: "How It Works",
      subtitle: "Four simple steps from business idea to official registration and scheme discovery.",
      step1Title: "1. Share Your Vision",
      step1Desc: "Tell us what you want to start, your investment budget, and your district in Tamil Nadu.",
      step2Title: "2. Verified Scheme Discovery",
      step2Desc: "Our deterministic engine checks verified rules to match central and state schemes you may qualify for.",
      step3Title: "3. Ask the Bilingual AI Advisor",
      step3Desc: "Chat in Tamil, English, or Tanglish with answers grounded strictly in retrieved official gazettes and documents.",
      step4Title: "4. Follow Your Roadmap",
      step4Desc: "Execute step-by-step tasks, prepare required documents, and apply through verified official portals.",
    },
    trust: {
      title: "Grounded in Authentic Official Data",
      description: "We never invent subsidy amounts, deadlines, or eligibility rules. Every scheme card and recommendation cites authentic sources.",
      source1: "Tamil Nadu MSME Portal (msmeonline.tn.gov.in)",
      source2: "MyScheme National Platform (myscheme.gov.in)",
      source3: "Startup India (startupindia.gov.in)",
      source4: "Udyam Registration Portal (udyamregistration.gov.in)",
      source5: "StartupTN Official Hub (startuptn.in)",
    },
    disclaimer:
      "Important Legal Notice: illusion AI is an educational and guidance platform providing provisional information based on public government guidelines. We do not guarantee scheme eligibility, loan sanctions, or subsidy approvals. Final determinations are made solely by the respective government departments and authorized financial institutions.",
    footer: {
      rights: "All rights reserved. Designed for Indian and Tamil Nadu Entrepreneurs.",
      privacy: "Privacy Policy",
      terms: "Terms of Service",
      officialPortals: "Official Portals",
    },
  },
  ta: {
    brandName: "illusion AI",
    tagline: "தொழில்முனைவோருக்கான வழிகாட்டி",
    nav: {
      home: "முகப்பு",
      onboarding: "பயணத்தை தொடங்கு",
      schemes: "அரசு திட்டங்கள்",
      chat: "AI ஆலோசகர்",
      roadmap: "என் வரைபடம்",
      language: "English",
    },
    hero: {
      badge: "தமிழ்நாடு மற்றும் மத்திய அரசு தொழில் திட்ட வழிகாட்டி",
      titleLine1: "உங்கள் வணிகப் பயணம்",
      titleLine2: "இங்கிருந்து தொடங்குகிறது.",
      description:
        "கடினமான வணிக நடைமுறைகள், அரசு மானியங்கள் மற்றும் கடன் திட்டங்களை எளிய, படிப்படியான வணிக வரைபடமாக மாற்றுங்கள். தமிழ்நாடு தொழில்முனைவோருக்காக பிரத்யேகமாக உருவாக்கப்பட்டது.",
      primaryCta: "என் வணிகப் பயணத்தை தொடங்கு",
      secondaryCta: "அரசு திட்டங்களை காண்க",
      trustText: "தமிழ்நாடு மற்றும் இந்திய அரசின் அதிகாரப்பூர்வ தகவல்களின் அடிப்படையில் மட்டுமே இயங்குகிறது",
    },
    features: {
      title: "தொழில் தொடங்க தேவையான அனைத்தும் ஒரே இடத்தில்",
      subtitle: "புதிய தொழில்முனைவோர் மற்றும் சிறு வணிகர்களுக்காக எளிமையான வழிகாட்டுதல்.",
      f1Title: "எளிய சுயவிவர பதிவு",
      f1Desc: "உங்கள் தொழில் யோசனை, மாவட்டம் மற்றும் முதலீட்டு பட்ஜெட்டை எளிய முறையில் உள்ளீடு செய்யுங்கள்.",
      f2Title: "AI தொழில் தொடக்க வழிகாட்டி",
      f2Desc: "தொடக்க செலவுகள், உத்யாம் பதிவு, ஜிஎஸ்டி மற்றும் உரிமங்கள் பற்றிய முழுமையான தெளிவு.",
      f3Title: "அரசு மானியங்கள் & திட்ட கண்டறிதல்",
      f3Desc: "NEEDS, UYEGP, PMEGP, StartupTN போன்ற பொருத்தமான அரசு திட்டங்களை தகுதி விதிகளோடு கண்டறியவும்.",
      f4Title: "தனிப்பயனாக்கப்பட்ட வரைபடம்",
      f4Desc: "படிப்படியான பணிகள், தேவையான ஆவணங்கள் மற்றும் அதிகாரப்பூர்வ விண்ணப்ப இணைப்புகளைக் கொண்ட சரிபார்ப்பு பட்டியல்.",
    },
    howItWorks: {
      title: "இது எவ்வாறு செயல்படுகிறது?",
      subtitle: "தொழில் யோசனை முதல் அதிகாரப்பூர்வ தொடக்கம் வரை நான்கு எளிய படிகள்.",
      step1Title: "1. உங்கள் விவரங்களை பகிரவும்",
      step1Desc: "நீங்கள் தொடங்க விரும்பும் தொழில், பட்ஜெட் மற்றும் உங்கள் மாவட்டத்தை உள்ளிடவும்.",
      step2Title: "2. திட்ட தகுதி ஆய்வு",
      step2Desc: "எங்கள் விதிகள் சார்ந்த அமைப்பு உங்களுக்கு பொருந்தக்கூடிய மத்திய மற்றும் மாநில திட்டங்களை பட்டியலிடுகிறது.",
      step3Title: "3. தமிழ் AI ஆலோசகரிடம் கேளுங்கள்",
      step3Desc: "தமிழ் அல்லது ஆங்கிலத்தில் ஏதேனும் சந்தேகம் இருந்தால் கேளுங்கள்; அதிகாரப்பூர்வ ஆதாரங்களுடன் பதில் கிடைக்கும்.",
      step4Title: "4. வரைபடத்தை பின்பற்றி செயல்படுங்கள்",
      step4Desc: "ஒவ்வொரு பணியையும் செய்து முடித்து, அரசு இணையதளங்கள் வழியாக அதிகாரப்பூர்வமாக விண்ணப்பியுங்கள்.",
    },
    trust: {
      title: "நம்பகமான அதிகாரப்பூர்வ தகவல்கள்",
      description: "நாங்கள் தவறான தகவல்களையோ கற்பனையான மானிய தொகைகளையோ ஒருபோதும் வழங்குவதில்லை. அனைத்து தகவல்களும் அரசு இணையதளங்களிலிருந்து பெறப்பட்டவை.",
      source1: "தமிழ்நாடு MSME தளம் (msmeonline.tn.gov.in)",
      source2: "MyScheme தேசிய தளம் (myscheme.gov.in)",
      source3: "Startup India (startupindia.gov.in)",
      source4: "உத்யாம் பதிவு தளம் (udyamregistration.gov.in)",
      source5: "StartupTN அதிகாரப்பூர்வ மையம் (startuptn.in)",
    },
    disclaimer:
      "முக்கிய அறிவிப்பு: illusion AI என்பது பொது அரசு வழிகாட்டுதல்களை அடிப்படையாகக் கொண்ட ஒரு வழிகாட்டி தளம் மட்டுமே. திட்ட தகுதி, வங்கிக் கடன் அல்லது மானிய அனுமதியை நாங்கள் உறுதி செய்ய முடியாது. இறுதி முடிவுகள் சம்பந்தப்பட்ட அரசு துறைகள் மற்றும் வங்கிகளால் மட்டுமே எடுக்கப்படும்.",
    footer: {
      rights: "அனைத்து உரிமைகளும் பாதுகாக்கப்பட்டவை. தமிழ்நாட்டு தொழில்முனைவோருக்காக உருவாக்கப்பட்டது.",
      privacy: "தனியுரிமைக் கொள்கை",
      terms: "விதிமுறைகள்",
      officialPortals: "அரசு இணையதளங்கள்",
    },
  },
};

