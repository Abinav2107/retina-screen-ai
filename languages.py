"""
languages.py -- Static offline multi-language translations (en, hi, bn, mr, te, ta)
for diabetic retinopathy screening, urgency triage, and patient guidance.
"""

from typing import Dict, Any


class SeverityMessage(dict):
    """
    Holds localized urgency, explanation, and clinical severity names.
    Supports dictionary access, attribute access, and str() evaluation.
    """

    def __init__(
        self,
        urgency: str,
        explanation: str,
        severity_name: str,
        action_timeline: str,
        color: str,
        badge_icon: str,
    ):
        super().__init__(
            urgency=urgency,
            explanation=explanation,
            severity_name=severity_name,
            action_timeline=action_timeline,
            color=color,
            badge_icon=badge_icon,
        )
        self.urgency = urgency
        self.explanation = explanation
        self.severity_name = severity_name
        self.action_timeline = action_timeline
        self.color = color
        self.badge_icon = badge_icon

    def __str__(self):
        return self.urgency


# ------------------------------------------------------------------
# Supported Languages Mapping
# ------------------------------------------------------------------
LANGUAGE_OPTIONS = ["English", "हिंदी", "বাংলা", "मराठी", "తెలుగు", "தமிழ்"]

LANGUAGE_CODE_MAP = {
    "English": "en",
    "हिंदी": "hi",
    "বাংলা": "bn",
    "मराठी": "mr",
    "తెలుగు": "te",
    "தமிழ்": "ta",
    "en": "en",
    "hi": "hi",
    "bn": "bn",
    "mr": "mr",
    "te": "te",
    "ta": "ta",
}


# ------------------------------------------------------------------
# Multi-Language MESSAGES Dictionary (6 Languages: en, hi, bn, mr, te, ta)
# ------------------------------------------------------------------
MESSAGES: Dict[str, Dict[Any, Any]] = {
    # ------------------------------------------------------------------
    # 1. English (en)
    # ------------------------------------------------------------------
    "en": {
        "language_name": "English",
        "disclaimer": "This is a screening aid, not a medical diagnosis. All flagged cases should be confirmed by a qualified ophthalmologist.",
        "offline_note": "Works fully offline — no internet required for translation",
        "rural_note": "This tool runs locally and does not require continuous internet access, making it suitable for use in low-connectivity rural health centers.",
        "ui": {
            "title": "NetraScreen — AI Diabetic Retinopathy Screening Assistant",
            "subtitle": "Automated retinal screening designed for frontline health workers.",
            "upload_label": "Upload Fundus Photograph",
            "analyse_btn": "🔍 Analyse Retina",
            "gradcam_label": "Grad-CAM Lesion Localization (Model Attention)",
            "urgency_header": "Patient Triage & Recommended Action",
            "explanation_header": "Patient-Friendly Explanation",
            "summary_label": "Clinical Summary",
            "scores_label": "Confidence Scores Across All 5 Severity Grades",
            "timeline_title": "RECOMMENDED ACTION TIMELINE",
            "caption_normal": "No significant abnormalities detected in the retina. The highlighted region shows areas the model focused on to confirm the absence of retinopathy.",
            "caption_mild_mod": "Highlighted regions show possible microaneurysms or small haemorrhages — early signs of diabetic retinopathy. Regular monitoring is recommended.",
            "caption_severe_pdr": "Highlighted regions show extensive retinal damage including possible abnormal blood vessel growth — urgent referral recommended.",
            "disclaimer_title": "Medical Screening Disclaimer",
            "rural_banner_title": "Rural Clinic Ready (100% Offline Edge Operation)",
            "stage_label": "Stage",
            "confidence_label": "Confidence",
            "triage_label": "Recommended Triage",
            "urgency_label": "Urgency",
            "timeline_label": "Recommended Timeline",
            "patient_label": "Patient",
            "eye_label": "Eye Examined",
            "history_label": "Clinical History",
            "sugar_label": "Blood Sugar",
            "htn_label": "Hypertension",
            "demographics_heading": "PATIENT DEMOGRAPHICS",
            "clinical_context_heading": "CLINICAL DIABETIC CONTEXT",
            "advisory_heading": "PATIENT ADVISORY",
        },
        0: SeverityMessage(
            urgency="No action needed",
            explanation="The retina appears healthy with no visible damage from diabetes. The blood vessels look clear and normal. Keep managing blood sugar and blood pressure, and get routine screening annually.",
            severity_name="No Diabetic Retinopathy",
            action_timeline="Annual screening recommended",
            color="green",
            badge_icon="🟢",
        ),
        1: SeverityMessage(
            urgency="Routine checkup recommended within 6 months",
            explanation="We detected minor, early changes in the small blood vessels at the back of the eye (tiny swelling spots). Your sight is usually unaffected right now, but regular monitoring is necessary to prevent progression.",
            severity_name="Mild Non-Proliferative Retinopathy",
            action_timeline="Within 6 months",
            color="yellow",
            badge_icon="🟡",
        ),
        2: SeverityMessage(
            urgency="See a doctor within 2 weeks",
            explanation="Some blood vessels in the retina are beginning to swell or leak fluid. Even if your vision feels normal today, the condition is progressing and requires a formal eye exam soon to protect your eyesight.",
            severity_name="Moderate Non-Proliferative Retinopathy",
            action_timeline="Within 2 weeks",
            color="orange",
            badge_icon="🟠",
        ),
        3: SeverityMessage(
            urgency="Urgent — see a doctor within 3 days",
            explanation="Multiple blood vessels are blocked, cutting off proper blood supply to the retina. This puts your vision at serious danger of sudden decline. Please visit an eye hospital or ophthalmologist promptly for specialized care.",
            severity_name="Severe Non-Proliferative Retinopathy",
            action_timeline="Within 3 days",
            color="red",
            badge_icon="🔴",
        ),
        4: SeverityMessage(
            urgency="Immediate referral required — risk of vision loss",
            explanation="Abnormal, fragile new blood vessels have started growing inside your eye. These can easily bleed into the eye or detach the retina, causing severe, permanent vision loss. Immediate referral to an eye hospital is required.",
            severity_name="Proliferative Diabetic Retinopathy",
            action_timeline="Immediate / Today",
            color="red",
            badge_icon="🚨",
        ),
    },

    # ------------------------------------------------------------------
    # 2. Hindi (hi) / हिंदी
    # ------------------------------------------------------------------
    "hi": {
        "language_name": "हिंदी",
        "disclaimer": "यह केवल एक स्क्रीनिंग सहायता है, चिकित्सीय निदान नहीं। सभी संदिग्ध मामलों की पुष्टि एक योग्य नेत्र विशेषज्ञ (ऑप्थल्मोलॉजिस्ट) द्वारा कराई जानी चाहिए।",
        "offline_note": "पूरी तरह से ऑफलाइन काम करता है — अनुवाद के लिए इंटरनेट की आवश्यकता नहीं है",
        "rural_note": "यह उपकरण पूरी तरह स्थानीय स्तर पर चलता है और इसके लिए निरंतर इंटरनेट कनेक्शन की आवश्यकता नहीं है, जिससे यह ग्रामीण स्वास्थ्य केंद्रों के लिए उपयुक्त है।",
        "ui": {
            "title": "नेत्रस्क्रीन — एआई डायबिटिक रेटिनोपैथी स्क्रीनिंग सहायक",
            "subtitle": "ग्रामीण स्वास्थ्य कार्यकर्ताओं के लिए स्वचालित रेटिना स्क्रीनिंग सुविधा।",
            "upload_label": "फंडस फोटोग्राफ अपलोड करें",
            "analyse_btn": "🔍 रेटिना की जांच करें",
            "gradcam_label": "ग्रैड-कैम घाव स्थानीयकरण (मॉडल का ध्यान)",
            "urgency_header": "मरीज़ ट्राइएज और अनुशंसित कार्रवाई",
            "explanation_header": "मरीज़ के लिए सरल व्याख्या",
            "summary_label": "नैदानिक सारांश",
            "scores_label": "सभी 5 गंभीरता स्तरों के विश्वास स्कोर",
            "timeline_title": "अनुशंसित कार्रवाई की समयसीमा",
            "caption_normal": "रेटिना में कोई महत्वपूर्ण असामान्यता नहीं पाई गई। हाइलाइट किए गए क्षेत्र रेटिनोपैथी की अनुपस्थिति की पुष्टि दर्शाते हैं।",
            "caption_mild_mod": "हाइलाइट किए गए क्षेत्र प्रारंभिक माइक्रोएन्यूरिज्म या छोटे रक्तस्राव को दर्शाते हैं — नियमित निगरानी की सलाह दी जाती है।",
            "caption_severe_pdr": "हाइलाइट किए गए क्षेत्र व्यापक रेटिना क्षति और असामान्य रक्त वाहिकाओं के विकास को दर्शाते हैं — तत्काल रेफरल आवश्यक है।",
            "disclaimer_title": "चिकित्सीय अस्वीकरण",
            "rural_banner_title": "ग्रामीण स्वास्थ्य केंद्र सक्षम (100% ऑफलाइन कार्य)",
            "stage_label": "स्तर",
            "confidence_label": "विश्वास",
            "triage_label": "अनुशंसित कार्रवाई",
            "urgency_label": "तत्कालता",
            "timeline_label": "अनुशंसित समयसीमा",
            "patient_label": "मरीज़",
            "eye_label": "जांची गई आंख",
            "history_label": "चिकित्सीय इतिहास",
            "sugar_label": "रक्त शर्करा",
            "htn_label": "उच्च रक्तचाप",
            "demographics_heading": "मरीज़ विवरण",
            "clinical_context_heading": "चिकित्सीय इतिहास",
            "advisory_heading": "मरीज़ के लिए निर्देश",
        },
        0: SeverityMessage(
            urgency="किसी कार्रवाई की आवश्यकता नहीं है",
            explanation="आंख का पर्दा (रेटिना) पूरी तरह स्वस्थ है और मधुमेह का कोई लक्षण नहीं दिख रहा है। रक्त वाहिकाएं सामान्य हैं। रक्त शर्करा नियंत्रित रखें और साल में एक बार जांच कराएं।",
            severity_name="कोई रेटिनोपैथी नहीं (No DR)",
            action_timeline="वार्षिक जांच की सलाह",
            color="green",
            badge_icon="🟢",
        ),
        1: SeverityMessage(
            urgency="6 महीने के भीतर नियमित जांच की सलाह",
            explanation="आंख के पिछले हिस्से की छोटी रक्त वाहिकाओं में हल्के शुरुआती बदलाव (छोटे धब्बे) दिखे हैं। अभी दृष्टि पर कोई असर नहीं है, लेकिन इसे बढ़ने से रोकने के लिए नियमित निगरानी जरूरी है।",
            severity_name="हल्की रेटिनोपैथी (Mild NPDR)",
            action_timeline="6 महीने के भीतर",
            color="yellow",
            badge_icon="🟡",
        ),
        2: SeverityMessage(
            urgency="2 सप्ताह के भीतर डॉक्टर से मिलें",
            explanation="रेटिना में कुछ रक्त वाहिकाओं में सूजन या हल्का रिसाव शुरू हो गया है। दृष्टि सामान्य लग सकती है, लेकिन आंखों की सुरक्षा के लिए जल्द ही नेत्र चिकित्सक से जांच कराना आवश्यक है।",
            severity_name="मध्यम रेटिनोपैथी (Moderate NPDR)",
            action_timeline="2 सप्ताह के भीतर",
            color="orange",
            badge_icon="🟠",
        ),
        3: SeverityMessage(
            urgency="तत्काल — 3 दिनों के भीतर डॉक्टर से मिलें",
            explanation="आंख की कई रक्त वाहिकाएं बंद हो गई हैं, जिससे रक्त आपूर्ति प्रभावित हो रही है। दृष्टि जाने का गंभीर खतरा है। कृपया 3 दिनों में किसी नेत्र विशेषज्ञ से संपर्क करें।",
            severity_name="गंभीर रेटिनोपैथी (Severe NPDR)",
            action_timeline="3 दिनों के भीतर",
            color="red",
            badge_icon="🔴",
        ),
        4: SeverityMessage(
            urgency="तत्काल रेफरल आवश्यक — दृष्टि हानि का गंभीर खतरा",
            explanation="आंख के अंदर नई और कमजोर रक्त वाहिकाएं बढ़ रही हैं, जिनसे कभी भी खून का रिसाव हो सकता है और आंखों की रोशनी जा सकती है। तुरंत नेत्र अस्पताल जाएं।",
            severity_name="अत्यधिक गंभीर रेटिनोपैथी (Proliferative DR)",
            action_timeline="तत्काल / आज ही",
            color="red",
            badge_icon="🚨",
        ),
    },

    # ------------------------------------------------------------------
    # 3. Bengali (bn) / বাংলা
    # ------------------------------------------------------------------
    "bn": {
        "language_name": "বাংলা",
        "disclaimer": "এটি শুধুমাত্র একটি স্ক্রীনিং সহায়তা, চিকিৎসাগত চূড়ান্ত রোগনির্ণয় নয়। সমস্ত ক্ষেত্রে একজন যোগ্য চক্ষুরোগ বিশেষজ্ঞের মাধ্যমে নিশ্চিত হওয়া উচিত।",
        "offline_note": "সম্পূর্ণ অফলাইনে কাজ করে — অনুবাদের জন্য কোনো ইন্টারনেটের প্রয়োজন নেই",
        "rural_note": "এই টুলটি সম্পূর্ণ স্থানীয়ভাবে কাজ করে এবং ক্রমাগত ইন্টারনেট সংযোগের প্রয়োজন হয় না, যা গ্রামীণ স্বাস্থ্য কেন্দ্রের জন্য উপযুক্ত।",
        "ui": {
            "title": "নেত্রস্ক্রিন — এআই ডায়াবেটিক রেটিনোপ্যাথি স্ক্রীনিং সহায়ক",
            "subtitle": "গ্রামীণ স্বাস্থ্যকর্মীদের জন্য স্বয়ংক্রিয় রেটিনা স্ক্রীনিং সুবিধা।",
            "upload_label": "ফান্ডাস ছবি আপলোড করুন",
            "analyse_btn": "🔍 রেটিনা বিশ্লেষণ করুন",
            "gradcam_label": "গ্র্যাড-ক্যাম ক্ষত চিহ্নিতকরণ (মডেলের মনোযোগ)",
            "urgency_header": "রোগীর ট্রায়াজ এবং করণীয় পদক্ষেপ",
            "explanation_header": "রোগীর জন্য সহজ ব্যাখ্যা",
            "summary_label": "ক্লিনিক্যাল সারাংশ",
            "scores_label": "সকল ৫টি তীব্রতার স্তরের আত্মবিশ্বাসের স্কোর",
            "timeline_title": "সুপারিশকৃত পদক্ষেপের সময়সীমা",
            "caption_normal": "রেটিনায় কোনো উল্লেখযোগ্য অস্বাভাবিকতা পাওয়া যায়নি। হাইলাইট করা অংশগুলি রেটিনোপ্যাথি না থাকার বিষয়টি নিশ্চিত করে।",
            "caption_mild_mod": "হাইলাইট করা স্থানগুলি প্রাথমিক রক্তনালীর সামান্য ক্ষতি নির্দেশ করে — নিয়মিত নজরদারি বাঞ্ছনীয়।",
            "caption_severe_pdr": "হাইলাইট করা স্থানগুলি রেটিনার গুরুতর ক্ষতি নির্দেশ করে — দ্রুত বিশেষজ্ঞের কাছে রেফারেল প্রয়োজন।",
            "disclaimer_title": "চিকিৎসা স্ক্রীনিং দাবিত্যাগ",
            "rural_banner_title": "গ্রামীণ ক্লিনিক উপযোগী (সম্পূর্ণ অফলাইন এজ অপারেশন)",
            "stage_label": "পর্যায়",
            "confidence_label": "আত্মবিশ্বাস",
            "triage_label": "সুপারিশকৃত পদক্ষেপ",
            "urgency_label": "জরুরীতা",
            "timeline_label": "সুপারিশকৃত সময়সীমা",
            "patient_label": "রোগী",
            "eye_label": "পরীক্ষিত চোখ",
            "history_label": "চিকিৎসা ইতিহাস",
            "sugar_label": "রক্তের শর্করা",
            "htn_label": "উচ্চ রক্তচাপ",
            "demographics_heading": "রোগীর বিবরণ",
            "clinical_context_heading": "ক্লিনিক্যাল ডায়াবেটিক প্রেক্ষাপট",
            "advisory_heading": "রোগীর জন্য পরামর্শ",
        },
        0: SeverityMessage(
            urgency="কোনো পদক্ষেপের প্রয়োজন নেই",
            explanation="রেটিনা সম্পূর্ণ সুস্থ এবং ডায়াবেটিসের কোনো ক্ষতি দৃশ্যমান নয়। রক্তনালীগুলি স্বাভাবিক রয়েছে। রক্তে শর্করার মাত্রা নিয়ন্ত্রণে রাখুন এবং বছরে একবার রুটিন পরীক্ষা করান।",
            severity_name="কোনো রেটিনোপ্যাথি নেই (No DR)",
            action_timeline="বার্ষিক পরীক্ষা বাঞ্ছনীয়",
            color="green",
            badge_icon="🟢",
        ),
        1: SeverityMessage(
            urgency="৬ মাসের মধ্যে নিয়মিত পরীক্ষার পরামর্শ",
            explanation="চোখের পেছনের সূক্ষ্ম রক্তনালীতে সামান্য প্রাথমিক পরিবর্তন দেখা গেছে। দৃষ্টিশক্তি এখনো ঠিক আছে, তবে অবস্থা যাতে আরও খারাপ না হয় তার জন্য নিয়মিত নজরদারি প্রয়োজন।",
            severity_name="মৃদু রেটিনোপ্যাথি (Mild NPDR)",
            action_timeline="৬ মাসের মধ্যে",
            color="yellow",
            badge_icon="🟡",
        ),
        2: SeverityMessage(
            urgency="২ সপ্তাহের মধ্যে ডাক্তারের সাথে পরামর্শ করুন",
            explanation="রেটিনার কিছু রক্তনালী ফুলতে বা তরল ক্ষরণ করতে শুরু করেছে। দৃষ্টিশক্তি স্বাভাবিক মনে হলেও চোখের সুরক্ষার জন্য দ্রুত চক্ষু বিশেষজ্ঞের পরামর্শ নিন।",
            severity_name="মাঝারি রেটিনোপ্যাথি (Moderate NPDR)",
            action_timeline="২ সপ্তাহের মধ্যে",
            color="orange",
            badge_icon="🟠",
        ),
        3: SeverityMessage(
            urgency="জরুরি — ৩ দিনের মধ্যে ডাক্তারের সাথে যোগাযোগ করুন",
            explanation="চোখের বেশ কয়েকটি রক্তনালী বন্ধ হয়ে গেছে, যা রক্তের প্রবাহকে ব্যাহত করছে। দৃষ্টিশক্তি দ্রুত হ্রাস পাওয়ার তীব্র ঝুঁকি রয়েছে। অবিলম্বে চক্ষু বিশেষজ্ঞের চিকিৎসা নিন।",
            severity_name="তীব্র রেটিনোপ্যাথি (Severe NPDR)",
            action_timeline="৩ দিনের মধ্যে",
            color="red",
            badge_icon="🔴",
        ),
        4: SeverityMessage(
            urgency="অবিলম্বে রেফারেল প্রয়োজন — দৃষ্টিশক্তি হারানোর ঝুঁকি",
            explanation="চোখের ভেতরে নতুন ও ভঙ্গুর রক্তনালী তৈরি হচ্ছে যা থেকে রক্তক্ষরণ হয়ে হঠাৎ দৃষ্টিশক্তি নষ্ট হতে পারে। অবিলম্বে চক্ষু হাসপাতালে জরুরি চিকিৎসা নিন।",
            severity_name="অত্যন্ত তীব্র রেটিনোপ্যাথি (Proliferative DR)",
            action_timeline="অবিলম্বে / আজই",
            color="red",
            badge_icon="🚨",
        ),
    },

    # ------------------------------------------------------------------
    # 4. Marathi (mr) / मराठी
    # ------------------------------------------------------------------
    "mr": {
        "language_name": "मराठी",
        "disclaimer": "हे केवळ तपासणीसाठी सहाय्यक साधन आहे, वैद्यकीय निदान नाही. सर्व संशयित प्रकरणांची खात्री पात्र नेत्रतज्ज्ञांकडून करून घ्यावी.",
        "offline_note": "पूर्णपणे ऑफलाइन कार्य करते — भाषांतरासाठी इंटरनेटची आवश्यकता नाही",
        "rural_note": "हे साधन पूर्णपणे ऑफलाइन चालते आणि सतत इंटरनेटची आवश्यकता नसते, ज्यामुळे ग्रामीण आरोग्य केंद्रांमध्ये वापरणे सोयीचे होते.",
        "ui": {
            "title": "नेत्रस्क्रीन — एआय डायबेटिक रेटिनोपॅथी स्क्रीनिंग सहाय्यक",
            "subtitle": "आरोग्य कर्मचाऱ्यांसाठी स्वयंचलित रेटिना तपासणी प्रणाली.",
            "upload_label": "फंडस फोटो अपलोड करा",
            "analyse_btn": "🔍 रेटिनाची तपासणी करा",
            "gradcam_label": "ग्रॅड-कॅम जखम स्थानिकीकरण (मॉडेलचे लक्ष)",
            "urgency_header": "रुग्ण ट्रायज आणि शिफारस केलेली कृती",
            "explanation_header": "रुग्णासाठी सोपे स्पष्टीकरण",
            "summary_label": "वैद्यकीय सारांश",
            "scores_label": "सर्व ५ तीव्रतेच्या स्तरांचे अचूकता गुण",
            "timeline_title": "शिफारस केलेली कृती कालमर्यादा",
            "caption_normal": "डोळ्याच्या पडद्यामध्ये कोणतीही विकृती आढळली नाही. हायलाइट केलेले भाग रेटिनोपॅथी नसल्याची पुष्टी करतात.",
            "caption_mild_mod": "हायलाइट केलेले भाग लहान रक्तस्त्राव किंवा फुगवटे दर्शवतात — नियमित तपासणीचा सल्ला दिला जातो.",
            "caption_severe_pdr": "हायलाइट केलेले भाग डोळ्याच्या पडद्याचे मोठे नुकसान दर्शवतात — तात्काळ नेत्रतज्ज्ञांकडे जाणे आवश्यक आहे.",
            "disclaimer_title": "वैद्यकीय तपासणी अस्वीकरण",
            "rural_banner_title": "ग्रामीण क्लिनिक सज्ज (100% ऑफलाइन ऑपरेशन)",
            "stage_label": "टप्पा",
            "confidence_label": "विश्वास",
            "triage_label": "शिफारस केलेली कारवाई",
            "urgency_label": "तातडी",
            "timeline_label": "शिफारस केलेली वेळ मर्यादा",
            "patient_label": "रुग्ण",
            "eye_label": "तपासलेला डोळा",
            "history_label": "वैद्यकीय इतिहास",
            "sugar_label": "रक्त शर्करा",
            "htn_label": "उच्च रक्तदाब",
            "demographics_heading": "रुग्ण तपशील",
            "clinical_context_heading": "वैद्यकीय मधुमेह पार्श्वभूमी",
            "advisory_heading": "रुग्णासाठी सूचना",
        },
        0: SeverityMessage(
            urgency="कोणत्याही कारवाईची आवश्यकता नाही",
            explanation="डोळ्याचा पडदा (रेटिना) निरोगी असून मधुमेहाची कोणतीही लक्षणे नाहीत. रक्तवाहिन्या सामान्य आहेत. रक्तातील साखर नियंत्रणात ठेवा आणि वर्षातून एकदा तपासणी करा.",
            severity_name="कोणतीही रेटिनोपॅथी नाही (No DR)",
            action_timeline="वार्षिक तपासणीची शिफारस",
            color="green",
            badge_icon="🟢",
        ),
        1: SeverityMessage(
            urgency="६ महिन्यांच्या आत नियमित तपासणीची शिफारस",
            explanation="डोळ्याच्या मागील भागातील सूक्ष्म रक्तवाहिन्यांमध्ये किरकोळ बदल दिसले आहेत. दृष्टीवर परिणाम झालेला नाही, परंतु आजार वाढू नये म्हणून नियमित तपासणी आवश्यक आहे.",
            severity_name="सौम्य रेटिनोपॅथी (Mild NPDR)",
            action_timeline="६ महिन्यांच्या आत",
            color="yellow",
            badge_icon="🟡",
        ),
        2: SeverityMessage(
            urgency="२ आठवड्यांच्या आत डॉक्टरांना भेटा",
            explanation="रेटिनामधील काही रक्तवाहिन्यांना सूज येणे किंवा गळती सुरू झाली आहे. दृष्टी चांगली वाटत असली तरी डोळ्यांच्या सुरक्षेसाठी लवकरच नेत्रतज्ज्ञांकडून तपासणी करून घ्या.",
            severity_name="मध्यम रेटिनोपॅथी (Moderate NPDR)",
            action_timeline="२ आठवड्यांच्या आत",
            color="orange",
            badge_icon="🟠",
        ),
        3: SeverityMessage(
            urgency="तातडीने — ३ दिवसांच्या आत डॉक्टरांना भेटा",
            explanation="डोळ्यातील अनेक रक्तवाहिन्या ब्लॉक झाल्या आहेत. यामुळे दृष्टी अचानक कमी होण्याचा मोठा धोका आहे. कृपया ३ दिवसांत नेत्रतज्ज्ञांचा सल्ला घ्या.",
            severity_name="तीव्र रेटिनोपॅथी (Severe NPDR)",
            action_timeline="३ दिवसांच्या आत",
            color="red",
            badge_icon="🔴",
        ),
        4: SeverityMessage(
            urgency="तातडीने रेफरल आवश्यक — दृष्टी जाण्याचा धोका",
            explanation="डोळ्यामध्ये नवीन व नाजूक रक्तवाहिन्या तयार झाल्या आहेत, ज्यामुळे रक्तस्त्राव होऊन दृष्टी कायमची जाऊ शकते. तात्काळ डोळ्यांच्या रुग्णालयात जाणे गरजेचे आहे.",
            severity_name="अत्यंत तीव्र रेटिनोपॅथी (Proliferative DR)",
            action_timeline="तातडीने / आजच",
            color="red",
            badge_icon="🚨",
        ),
    },

    # ------------------------------------------------------------------
    # 5. Telugu (te) / తెలుగు
    # ------------------------------------------------------------------
    "te": {
        "language_name": "తెలుగు",
        "disclaimer": "ఇది స్క్రీనింగ్ సహాయకం మాత్రమే, వైద్య నిర్ధారణ కాదు. అనుమానిత కేసులన్నీ అర్హత కలిగిన నేత్ర వైద్యుడిచే నిర్ధారించబడాలి.",
        "offline_note": "పూర్తిగా ఆఫ్‌లైన్‌లో పనిచేస్తుంది — అనువాదం కోసం ఇంటర్నెట్ అవసరం లేదు",
        "rural_note": "ఈ సాధనం పూర్తిగా స్థానికంగా పనిచేస్తుంది మరియు నిరంతర ఇంటర్నెట్ అవసరం లేదు, గ్రామీణ ఆరోగ్య కేంద్రాలకు అనుకూలమైనది.",
        "ui": {
            "title": "నేత్రస్క్రీన్ — ఏఐ డయాబెటిక్ రెటినోపతి స్క్రీనింగ్ సహాయకం",
            "subtitle": "గ్రామీణ ఆరోగ్య కార్యకర్తల కోసం ఆటోమేటెడ్ రెటీనా స్క్రీనింగ్ సౌకర్యం.",
            "upload_label": "ఫండస్ ఫోటో అప్‌లోడ్ చేయండి",
            "analyse_btn": "🔍 రెటీనాను విశ్లేషించండి",
            "gradcam_label": "గ్రాడ్-కామ్ గాయం స్థాన గుర్తింపు (మోడల్ దృష్టి)",
            "urgency_header": "రోగి ట్రియాజ్ & సిఫార్సు చేసిన చర్య",
            "explanation_header": "రోగికి సులభమైన వివరణ",
            "summary_label": "క్లినికల్ సారాంశం",
            "scores_label": "అన్ని 5 తీవ్రత స్థాయిల విశ్వాస స్కోర్లు",
            "timeline_title": "సిఫార్సు చేసిన చర్యల కాలపరిమితి",
            "caption_normal": "రెటీనాలో ఎటువంటి అసాధారణతలు కనిపించలేదు. హైలైట్ చేసిన భాగాలు రెటినోపతి లేకపోవడాన్ని నిర్ధారిస్తాయి.",
            "caption_mild_mod": "హైలైట్ చేసిన ప్రాంతాలు చిన్న రక్తస్రావం లేదా ప్రారంభ నష్టాన్ని సూచిస్తాయి — క్రమమైన పర్యవేక్షణ అవసరం.",
            "caption_severe_pdr": "హైలైట్ చేసిన భాగాలు తీవ్రమైన రెటీనా నష్టాన్ని సూచిస్తాయి — వెంటనే నిపుణుడి వద్దకు వెళ్లాలి.",
            "disclaimer_title": "వైద్య స్క్రీనింగ్ నిరాకరణ",
            "rural_banner_title": "గ్రామీణ క్లినిక్ సిద్ధం (100% ఆఫ్‌లైన్ ఎడ్జ్ ఆపరేషన్)",
            "stage_label": "దశ",
            "confidence_label": "విశ్వాసం",
            "triage_label": "సిఫార్సు చేయబడిన చర్య",
            "urgency_label": "అత్యవసరం",
            "timeline_label": "సిఫార్సు చేయబడిన సమయ పరిమితి",
            "patient_label": "రోగి",
            "eye_label": "పరీక్షించిన కన్ను",
            "history_label": "క్లినికల్ చరిత్ర",
            "sugar_label": "రక్తంలో చక్కెర",
            "htn_label": "రక్తపోటు",
            "demographics_heading": "రోగి వివరాలు",
            "clinical_context_heading": "క్లినికల్ డయాబెటిక్ వివరాలు",
            "advisory_heading": "రోగి సలహా",
        },
        0: SeverityMessage(
            urgency="ఎలాంటి చర్య అవసరం లేదు",
            explanation="కంటి రెటీనా ఆరోగ్యంగా ఉంది మరియు మధుమేహం వల్ల ఎటువంటి నష్టం కనిపించలేదు. రక్తనాళాలు స్పష్టంగా ఉన్నాయి. రక్తంలో చక్కెరను నియంత్రణలో ఉంచుకోండి మరియు సంవత్సరానికి ఒకసారి పరీక్ష చేయించుకోండి.",
            severity_name="రెటినోపతి లేదు (No DR)",
            action_timeline="వార్షిక పరీక్ష సిఫార్సు చేయబడింది",
            color="green",
            badge_icon="🟢",
        ),
        1: SeverityMessage(
            urgency="6 నెలల్లోపు సాధారణ పరీక్ష సిఫార్సు చేయబడింది",
            explanation="కంటి వెనుక చిన్న రక్తనాళాలలో స్వల్ప ప్రారంభ మార్పులు గమనించబడ్డాయి. ప్రస్తుతానికి చూపు సాధారణంగానే ఉంటుంది, కానీ ఇది పెరగకుండా ఉండటానికి క్రమం తప్పకుండా పర్యవేక్షించడం అవసరం.",
            severity_name="స్వల్ప రెటినోపతి (Mild NPDR)",
            action_timeline="6 నెలల్లోపు",
            color="yellow",
            badge_icon="🟡",
        ),
        2: SeverityMessage(
            urgency="2 వారాల్లోపు వైద్యుడిని సంప్రదించండి",
            explanation="రెటీనాలోని కొన్ని రక్తనాళాలు ఉబ్బడం లేదా లీక్ కావడం ప్రారంభమైంది. చూపు బాగానే ఉన్నట్లు అనిపించినా, మీ కంటి చూపును రక్షించుకోవడానికి వెంటనే నేత్ర వైద్యుడిని సంప్రదించాలి.",
            severity_name="మధ్యస్థ రెటినోపతి (Moderate NPDR)",
            action_timeline="2 వారాల్లోపు",
            color="orange",
            badge_icon="🟠",
        ),
        3: SeverityMessage(
            urgency="అత్యవసరం — 3 రోజుల్లోపు వైద్యుడిని సంప్రదించండి",
            explanation="కంటిలో రక్త ప్రసరణ తగ్గుతూ అనేక రక్తనాళాలు మూసుకుపోయాయి. చూపు అకస్మాత్తుగా తగ్గిపోయే తీవ్ర ప్రమాదం ఉంది. దయచేసి వెంటనే నిపుణుడైన నేత్ర వైద్యుడిని సంప్రదించండి.",
            severity_name="తీవ్రమైన రెటినోపతి (Severe NPDR)",
            action_timeline="3 రోజుల్లోపు",
            color="red",
            badge_icon="🔴",
        ),
        4: SeverityMessage(
            urgency="వెంటనే రిఫరల్ అవసరం — దృష్టి కోల్పోయే ప్రమాదం",
            explanation="కంటి లోపల అసాధారణమైన కొత్త రక్తనాళాలు పెరుగుతున్నాయి, ఇవి రక్తస్రావం కలిగించి శాశ్వత అంధత్వానికి దారితీయవచ్చు. వెంటనే కంటి ఆసుపత్రికి వెళ్లాలి.",
            severity_name="అత్యంత తీవ్రమైన రెటినోపతి (Proliferative DR)",
            action_timeline="వెంటనే / ఈరోజే",
            color="red",
            badge_icon="🚨",
        ),
    },

    # ------------------------------------------------------------------
    # 6. Tamil (ta) / தமிழ்
    # ------------------------------------------------------------------
    "ta": {
        "language_name": "தமிழ்",
        "disclaimer": "இது ஒரு பரிசோதனை வழிகாட்டி மட்டுமே, மருத்துவ நோய் கண்டறிதல் அல்ல. அனைத்து சந்தேகத்திற்குரிய நிலைகளும் தகுதிவாய்ந்த கண் மருத்துவரால் உறுதி செய்யப்பட வேண்டும்.",
        "offline_note": "முழுமையாக ஆஃப்லைனில் செயல்படும் — மொழிபெயர்ப்பிற்கு இணையம் தேவையில்லை",
        "rural_note": "இந்த கருவி முழுமையாக ஆஃப்லைனில் இயங்குகிறது, கிராமப்புற சுகாதார நிலையங்களுக்கு மிகவும் ஏற்றது.",
        "ui": {
            "title": "நேத்ராஸ்கிரீன் — ஏஐ சர்க்கரை நோய் விழித்திரை பரிசோதனை உதவியாளர்",
            "subtitle": "கிராமப்புற சுகாதாரப் பணியாளர்களுக்கான தானியங்கி விழித்திரை பரிசோதனை முறை.",
            "upload_label": "ஃபண்டஸ் புகைப்படத்தைப் பதிவேற்றவும்",
            "analyse_btn": "🔍 விழித்திரையை பரிசோதிக்கவும்",
            "gradcam_label": "கிரேடு-கேம் பாதிப்பு பகுதி (செயற்கை நுண்ணறிவின் கவனம்)",
            "urgency_header": "நோயாளி முன்னுரிமை & பரிந்துரைக்கப்பட்ட நடவடிக்கை",
            "explanation_header": "நோயாளிக்கான எளிய விளக்கம்",
            "summary_label": "மருத்துவச் சுருக்கம்",
            "scores_label": "அனைத்து 5 தீவிர நிலைகளின் துல்லியப் புள்ளிகள்",
            "timeline_title": "பரிந்துரைக்கப்பட்ட நடவடிக்கை காலக்கெடு",
            "caption_normal": "விழித்திரையில் குறிப்பிடத்தக்க பாதிப்புகள் எதுவும் இல்லை. ஹைலைட் செய்யப்பட்ட பகுதிகள் பாதிப்பு இல்லை என்பதை உறுதி செய்கின்றன.",
            "caption_mild_mod": "ஹைலைட் செய்யப்பட்ட பகுதிகள் ஆரம்ப நிலை ரத்தக் கசிவைக் குறிக்கின்றன — வழக்கமான கண்காணிப்பு தேவை.",
            "caption_severe_pdr": "ஹைலைட் செய்யப்பட்ட பகுதிகள் கடுமையான விழித்திரை சேதத்தைக் காட்டுகின்றன — அவசர கண் மருத்துவ சிகிச்சை தேவை.",
            "disclaimer_title": "மருத்துவ பரிசோதனை மறுப்பு",
            "rural_banner_title": "கிராமப்புற கிளினிக் தயார் (100% ஆஃப்லைன் செயல்பாடு)",
            "stage_label": "நிலை",
            "confidence_label": "நம்பகத்தன்மை",
            "triage_label": "பரிந்துரைக்கப்பட்ட நடவடிக்கை",
            "urgency_label": "அவசரம்",
            "timeline_label": "பரிந்துரைக்கப்பட்ட காலக்கெடு",
            "patient_label": "நோயாளி",
            "eye_label": "பரிசோதிக்கப்பட்ட கண்",
            "history_label": "மருத்துவ வரலாறு",
            "sugar_label": "ரத்த சர்க்கரை",
            "htn_label": "உயர் ரத்த அழுத்தம்",
            "demographics_heading": "நோயாளி விவரங்கள்",
            "clinical_context_heading": "மருத்துவ சர்க்கரை நோய் விவரம்",
            "advisory_heading": "நோயாளிக்கான ஆலோசனைகள்",
        },
        0: SeverityMessage(
            urgency="நடவடிக்கை தேவையில்லை",
            explanation="விழித்திரை ஆரோக்கியமாக உள்ளது மற்றும் சர்க்கரை நோயின் பாதிப்புகள் எதுவும் இல்லை. ரத்த நாளங்கள் இயல்பாக உள்ளன. ரத்த சர்க்கரையை கட்டுக்குள் வைத்து ஆண்டுதோறும் பரிசோதனை செய்துகொள்ளுங்கள்.",
            severity_name="விழித்திரை பாதிப்பு இல்லை (No DR)",
            action_timeline="வருடாந்திர பரிசோதனை பரிந்துரைக்கப்படுகிறது",
            color="green",
            badge_icon="🟢",
        ),
        1: SeverityMessage(
            urgency="6 மாதங்களுக்குள் வழக்கமான பரிசோதனை பரிந்துரைக்கப்படுகிறது",
            explanation="கண்ணின் பின்புறத்தில் உள்ள சிறிய ரத்த நாளங்களில் ஆரம்ப கட்ட சிறிய மாற்றங்கள் கண்டறியப்பட்டுள்ளன. பார்வை பாதிக்கப்படவில்லை என்றாலும், நிலைமை தீவிரமடையாமல் தடுக்க தொடர் கண்காணிப்பு அவசியம்.",
            severity_name="லேசான விழித்திரை பாதிப்பு (Mild NPDR)",
            action_timeline="6 மாதங்களுக்குள்",
            color="yellow",
            badge_icon="🟡",
        ),
        2: SeverityMessage(
            urgency="2 வாரங்களுக்குள் மருத்துவரை அணுகவும்",
            explanation="விழித்திரையில் சில ரத்த நாளங்கள் வீங்க அல்லது கசியத் தொடங்கியுள்ளன. பார்வை சீராகத் தோன்றினாலும், உங்கள் பார்வையைப் பாதுகாக்க விரைவில் கண் மருத்துவரை அணுக வேண்டும்.",
            severity_name="மிதமான விழித்திரை பாதிப்பு (Moderate NPDR)",
            action_timeline="2 வாரங்களுக்குள்",
            color="orange",
            badge_icon="🟠",
        ),
        3: SeverityMessage(
            urgency="அவசரம் — 3 நாட்களுக்குள் மருத்துவரை அணுகவும்",
            explanation="கண்ணில் பல ரத்த நாளங்கள் அடைபட்டு ரத்த ஓட்டம் குறைந்துள்ளது. திடீர் பார்வைக் குறைபாடு ஏற்படும் அபாயம் அதிகம். உடனடியாக கண் மருத்துவரிடம் சிகிச்சை பெறவும்.",
            severity_name="கடுமையான விழித்திரை பாதிப்பு (Severe NPDR)",
            action_timeline="3 நாட்களுக்குள்",
            color="red",
            badge_icon="🔴",
        ),
        4: SeverityMessage(
            urgency="உடனடி பரிந்துரை தேவை — பார்வை இழக்கும் அபாயம்",
            explanation="கண்ணுக்குள் புதிய பலவீனமான ரத்த நாளங்கள் வளரத் தொடங்கியுள்ளன, இதனால் ரத்தக் கசிவு ஏற்பட்டு பார்வை நிரந்தரமாகப் பறிபோகும் அபாயம் உள்ளது. உடனடியாக கண் மருத்துவமனைக்குச் செல்லவும்.",
            severity_name="மிகக் கடுமையான விழித்திரை பாதிப்பு (Proliferative DR)",
            action_timeline="உடனடியாக / இன்றே",
            color="red",
            badge_icon="🚨",
        ),
    },
}

# ------------------------------------------------------------------
# Add aliases for string keys so MESSAGES[lang][key] works flexibly
# ------------------------------------------------------------------
_SEV_KEY_ALIASES = {
    0: ["0", "no_dr", "No DR", "no diabetic retinopathy"],
    1: ["1", "mild_npdr", "Mild NPDR", "mild"],
    2: ["2", "moderate_npdr", "Moderate NPDR", "moderate"],
    3: ["3", "severe_npdr", "Severe NPDR", "severe"],
    4: ["4", "proliferative_dr", "Proliferative DR", "pdr"],
}

for lang, data in MESSAGES.items():
    for int_key, aliases in _SEV_KEY_ALIASES.items():
        val = data[int_key]
        for alias in aliases:
            data[alias] = val


def get_language_code(lang_str: str) -> str:
    """Normalize language name or code to a 2-letter code."""
    if not lang_str:
        return "en"
    return LANGUAGE_CODE_MAP.get(lang_str.strip(), "en")
