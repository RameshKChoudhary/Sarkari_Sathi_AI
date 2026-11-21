"""SAMPLE FIXTURE CONTENT -- NOT OFFICIAL DOCUMENTS.

Short paraphrased summaries of 10 well-known Indian schemes, written by the project author
(an AI assistant) from general knowledge, in English / Hindi / Marathi. They exist so the
pipeline, API, UI and evaluation can run offline immediately. They are NOT copies of
government documents, may be out of date or wrong, and the Hindi/Marathi text has NOT been
verified by a native speaker. Replace with real official PDFs using scripts/add_scheme.py.
"""
from __future__ import annotations

NOTICE = {
    "en": "SAMPLE FIXTURE - not an official government document. Verify on the official portal.",
    "hi": "नमूना फ़िक्स्चर - यह आधिकारिक सरकारी दस्तावेज़ नहीं है। आधिकारिक पोर्टल पर सत्यापित करें।",
    "mr": "नमुना फिक्स्चर - हा अधिकृत सरकारी दस्तावेज नाही. अधिकृत पोर्टलवर खात्री करा.",
}
SECTION_ORDER = ["eligibility", "benefits", "documents", "how_to_apply"]

SCHEMES: list[dict] = [
    {
        "id": "pm_kisan", "level": "central", "url": "https://pmkisan.gov.in/",
        "names": {
            "en": "PM-KISAN (Pradhan Mantri Kisan Samman Nidhi)",
            "hi": "पीएम-किसान (प्रधानमंत्री किसान सम्मान निधि)",
            "mr": "पीएम-किसान (प्रधानमंत्री किसान सन्मान निधी)",
        },
        "aliases": ["pm kisan", "pm-kisan", "pmkisan", "पीएम-किसान", "पीएम किसान", "पंतप्रधान किसान", "प्रधानमंत्री किसान"],
        "sections": {
            "eligibility": {
                "en": "Farmer families who own cultivable land are eligible. Institutional landholders and persons who paid income tax in the last assessment year are excluded.",
                "hi": "जिन किसान परिवारों के पास कृषि योग्य भूमि है, वे पात्र हैं। संस्थागत भूमिधारक और पिछले आकलन वर्ष में आयकर चुकाने वाले व्यक्ति पात्र नहीं हैं।",
                "mr": "लागवडीयोग्य जमीन असलेली शेतकरी कुटुंबे पात्र आहेत. संस्थात्मक जमीनधारक आणि मागील कर निर्धारण वर्षात आयकर भरलेल्या व्यक्ती पात्र नाहीत.",
            },
            "benefits": {
                "en": "Eligible farmer families receive ₹6,000 per year. The amount is paid in three instalments of ₹2,000 directly into the bank account.",
                "hi": "पात्र किसान परिवारों को प्रति वर्ष ₹6,000 मिलते हैं। यह राशि ₹2,000 की तीन किस्तों में सीधे बैंक खाते में जमा की जाती है।",
                "mr": "पात्र शेतकरी कुटुंबांना दरवर्षी ₹6,000 मिळतात. ही रक्कम ₹2,000 च्या तीन हप्त्यांमध्ये थेट बँक खात्यात जमा केली जाते.",
            },
            "documents": {
                "en": "Aadhaar card, land ownership records and a bank account passbook are required. A bank account linked to Aadhaar is also needed.",
                "hi": "आधार कार्ड, भूमि स्वामित्व के अभिलेख और बैंक खाते की पासबुक आवश्यक हैं। आधार से जुड़ा बैंक खाता भी आवश्यक है।",
                "mr": "आधार कार्ड, जमीन मालकीची कागदपत्रे आणि बँक खात्याचे पासबुक आवश्यक आहे. आधारशी जोडलेले बँक खातेही आवश्यक आहे.",
            },
            "how_to_apply": {
                "en": "Farmers can register through the Farmers Corner on the PM-KISAN portal or at a Common Service Centre. State nodal officers and local revenue officials can also help with registration.",
                "hi": "किसान पीएम-किसान पोर्टल के फार्मर्स कॉर्नर या कॉमन सर्विस सेंटर पर पंजीकरण कर सकते हैं। राज्य के नोडल अधिकारी और स्थानीय राजस्व अधिकारी भी पंजीकरण में सहायता करते हैं।",
                "mr": "शेतकरी पीएम-किसान पोर्टलवरील फार्मर्स कॉर्नर किंवा कॉमन सर्व्हिस सेंटरवर नोंदणी करू शकतात. राज्याचे नोडल अधिकारी आणि स्थानिक महसूल अधिकारी देखील नोंदणीसाठी मदत करतात.",
            },
        },
    },
    {
        "id": "pmjay", "level": "central", "url": "https://pmjay.gov.in/",
        "names": {
            "en": "Ayushman Bharat PM-JAY",
            "hi": "आयुष्मान भारत पीएम-जेएवाई",
            "mr": "आयुष्मान भारत पीएम-जेएवाय",
        },
        "aliases": ["ayushman bharat", "ayushman", "pmjay", "pm-jay", "आयुष्मान भारत", "आयुष्मान"],
        "sections": {
            "eligibility": {
                "en": "Eligibility is based on deprivation and occupational criteria from the Socio-Economic Caste Census 2011 database. Families do not need to pay any enrolment fee.",
                "hi": "पात्रता सामाजिक-आर्थिक जाति जनगणना 2011 के अभाव और व्यावसायिक मानदंडों पर आधारित है। परिवारों को कोई पंजीकरण शुल्क नहीं देना पड़ता।",
                "mr": "पात्रता सामाजिक-आर्थिक जात जनगणना 2011 मधील वंचितता आणि व्यावसायिक निकषांवर आधारित आहे. कुटुंबांना कोणतेही नोंदणी शुल्क द्यावे लागत नाही.",
            },
            "benefits": {
                "en": "Each eligible family gets health cover of ₹5 lakh per year for secondary and tertiary hospital care. Treatment is cashless at empanelled public and private hospitals.",
                "hi": "प्रत्येक पात्र परिवार को द्वितीयक और तृतीयक अस्पताल देखभाल के लिए प्रति वर्ष ₹5 लाख का स्वास्थ्य कवर मिलता है। सूचीबद्ध सरकारी और निजी अस्पतालों में इलाज कैशलेस होता है।",
                "mr": "प्रत्येक पात्र कुटुंबाला दुय्यम आणि तृतीय स्तरावरील रुग्णालयीन उपचारांसाठी दरवर्षी ₹5 लाखांचे आरोग्य संरक्षण मिळते. नोंदणीकृत सरकारी आणि खासगी रुग्णालयांत उपचार कॅशलेस असतात.",
            },
            "documents": {
                "en": "Aadhaar card and a ration card or other identity proof are generally used to verify the family. Hospitals verify identity at the Ayushman Mitra help desk.",
                "hi": "परिवार के सत्यापन के लिए आमतौर पर आधार कार्ड और राशन कार्ड या अन्य पहचान प्रमाण का उपयोग होता है। अस्पताल में आयुष्मान मित्र हेल्प डेस्क पर पहचान सत्यापित की जाती है।",
                "mr": "कुटुंबाच्या पडताळणीसाठी साधारणपणे आधार कार्ड आणि रेशन कार्ड किंवा इतर ओळखपत्र वापरले जाते. रुग्णालयातील आयुष्मान मित्र मदत कक्षावर ओळख तपासली जाते.",
            },
            "how_to_apply": {
                "en": "Check eligibility on the official PM-JAY portal or helpline. Eligible people can get an Ayushman card from an empanelled hospital's Ayushman Mitra or a Common Service Centre.",
                "hi": "आधिकारिक पीएम-जेएवाई पोर्टल या हेल्पलाइन पर पात्रता जांचें। पात्र लोग सूचीबद्ध अस्पताल के आयुष्मान मित्र या कॉमन सर्विस सेंटर से आयुष्मान कार्ड बनवा सकते हैं।",
                "mr": "अधिकृत पीएम-जेएवाय पोर्टल किंवा हेल्पलाइनवर पात्रता तपासा. पात्र व्यक्ती नोंदणीकृत रुग्णालयातील आयुष्मान मित्र किंवा कॉमन सर्व्हिस सेंटरमधून आयुष्मान कार्ड मिळवू शकतात.",
            },
        },
    },
    {
        "id": "ladki_bahin", "level": "state", "url": "https://ladakibahin.maharashtra.gov.in/",
        "names": {
            "en": "Mukhyamantri Majhi Ladki Bahin Yojana",
            "hi": "मुख्यमंत्री माझी लाडकी बहीण योजना",
            "mr": "मुख्यमंत्री माझी लाडकी बहीण योजना",
        },
        "aliases": ["ladki bahin", "ladki bahini", "ladaki bahin", "majhi ladki bahin", "लाडकी बहीण", "लाडकी बहिण"],
        "sections": {
            "eligibility": {
                "en": "Women residing in Maharashtra aged 21 to 65 years are eligible. The annual family income should not exceed ₹2.5 lakh.",
                "hi": "महाराष्ट्र में रहने वाली 21 से 65 वर्ष की महिलाएं पात्र हैं। परिवार की वार्षिक आय ₹2.5 लाख से अधिक नहीं होनी चाहिए।",
                "mr": "महाराष्ट्रात राहणाऱ्या 21 ते 65 वर्षे वयोगटातील महिला पात्र आहेत. कुटुंबाचे वार्षिक उत्पन्न ₹2.5 लाखांपेक्षा जास्त नसावे.",
            },
            "benefits": {
                "en": "Eligible women receive ₹1,500 per month through direct bank transfer.",
                "hi": "पात्र महिलाओं को प्रति माह ₹1,500 सीधे बैंक हस्तांतरण द्वारा मिलते हैं।",
                "mr": "पात्र महिलांना दरमहा ₹1,500 थेट बँक हस्तांतरणाद्वारे मिळतात.",
            },
            "documents": {
                "en": "Aadhaar card, proof of Maharashtra residence, income proof and a bank account linked to Aadhaar are needed. A recent photograph is also required.",
                "hi": "आधार कार्ड, महाराष्ट्र निवास का प्रमाण, आय प्रमाण और आधार से जुड़ा बैंक खाता आवश्यक है। हाल का फोटो भी चाहिए।",
                "mr": "आधार कार्ड, महाराष्ट्रातील रहिवासाचा पुरावा, उत्पन्नाचा पुरावा आणि आधारशी जोडलेले बँक खाते आवश्यक आहे. अलीकडील फोटोही लागतो.",
            },
            "how_to_apply": {
                "en": "Applications can be submitted online through the Nari Shakti Doot app or the official scheme portal. Applicants can also seek help at the Anganwadi centre or the local ward or gram panchayat office.",
                "hi": "आवेदन नारी शक्ति दूत ऐप या आधिकारिक योजना पोर्टल के माध्यम से ऑनलाइन किया जा सकता है। आवेदक आंगनवाड़ी केंद्र या स्थानीय वार्ड या ग्राम पंचायत कार्यालय से भी सहायता ले सकते हैं।",
                "mr": "अर्ज नारी शक्ती दूत ॲप किंवा अधिकृत योजना पोर्टलद्वारे ऑनलाइन सादर करता येतो. अर्जदार अंगणवाडी केंद्र किंवा स्थानिक वॉर्ड किंवा ग्रामपंचायत कार्यालयातही मदत घेऊ शकतात.",
            },
        },
    },
    {
        "id": "pmayg", "level": "central", "url": "https://pmayg.nic.in/",
        "names": {
            "en": "Pradhan Mantri Awas Yojana - Gramin (PMAY-G)",
            "hi": "प्रधानमंत्री आवास योजना - ग्रामीण (पीएमएवाई-जी)",
            "mr": "प्रधानमंत्री आवास योजना - ग्रामीण (पीएमएवाय-जी)",
        },
        "aliases": ["awas yojana", "pmay", "pmay-g", "pmayg", "pradhan mantri awas", "awas plus", "आवास योजना", "आवास प्लस"],
        "sections": {
            "eligibility": {
                "en": "Rural households without a pucca house, or living in kutcha or dilapidated houses, are eligible. Beneficiaries are identified from the Socio-Economic Caste Census data and verified by the Gram Sabha.",
                "hi": "बिना पक्के मकान वाले या कच्चे या जर्जर मकानों में रहने वाले ग्रामीण परिवार पात्र हैं। लाभार्थियों की पहचान सामाजिक-आर्थिक जाति जनगणना के आंकड़ों से होती है और ग्राम सभा उनका सत्यापन करती है।",
                "mr": "पक्के घर नसलेली किंवा कच्च्या किंवा मोडकळीस आलेल्या घरात राहणारी ग्रामीण कुटुंबे पात्र आहेत. लाभार्थ्यांची निवड सामाजिक-आर्थिक जात जनगणनेच्या आकडेवारीवरून होते आणि ग्रामसभा त्यांची पडताळणी करते.",
            },
            "benefits": {
                "en": "Financial assistance of ₹1.2 lakh in plain areas and ₹1.3 lakh in hilly areas is provided for building a pucca house. Beneficiaries are also entitled to 90 days of unskilled wage employment under MGNREGA.",
                "hi": "पक्का मकान बनाने के लिए मैदानी क्षेत्रों में ₹1.2 लाख और पहाड़ी क्षेत्रों में ₹1.3 लाख की वित्तीय सहायता दी जाती है। लाभार्थियों को मनरेगा के तहत 90 दिन का अकुशल मजदूरी रोजगार भी मिलता है।",
                "mr": "पक्के घर बांधण्यासाठी सपाट भागात ₹1.2 लाख आणि डोंगराळ भागात ₹1.3 लाख आर्थिक सहाय्य दिले जाते. लाभार्थ्यांना मनरेगा अंतर्गत 90 दिवसांचा अकुशल मजुरी रोजगारही मिळतो.",
            },
            "documents": {
                "en": "Aadhaar card, MGNREGA job card and bank account details are required for the beneficiary.",
                "hi": "लाभार्थी के लिए आधार कार्ड, मनरेगा जॉब कार्ड और बैंक खाते का विवरण आवश्यक है।",
                "mr": "लाभार्थ्यासाठी आधार कार्ड, मनरेगा जॉब कार्ड आणि बँक खात्याचा तपशील आवश्यक आहे.",
            },
            "how_to_apply": {
                "en": "Households should contact the Gram Panchayat or block development office to check whether their name is on the Awaas Plus beneficiary list.",
                "hi": "परिवारों को अपना नाम आवास प्लस लाभार्थी सूची में है या नहीं, यह जांचने के लिए ग्राम पंचायत या खंड विकास कार्यालय से संपर्क करना चाहिए।",
                "mr": "कुटुंबांनी त्यांचे नाव आवास प्लस लाभार्थी यादीत आहे का हे तपासण्यासाठी ग्रामपंचायत किंवा गट विकास कार्यालयाशी संपर्क साधावा.",
            },
        },
    },
    {
        "id": "pmuy", "level": "central", "url": "https://www.pmuy.gov.in/",
        "names": {
            "en": "Pradhan Mantri Ujjwala Yojana (PMUY)",
            "hi": "प्रधानमंत्री उज्ज्वला योजना (पीएमयूवाई)",
            "mr": "प्रधानमंत्री उज्ज्वला योजना (पीएमयूवाय)",
        },
        "aliases": ["ujjwala", "ujwala", "pmuy", "उज्ज्वला", "उज्वला"],
        "sections": {
            "eligibility": {
                "en": "An adult woman from a poor household who does not already have an LPG connection in the household is eligible.",
                "hi": "गरीब परिवार की वयस्क महिला, जिसके घर में पहले से एलपीजी कनेक्शन नहीं है, पात्र है।",
                "mr": "गरीब कुटुंबातील प्रौढ महिला, जिच्या घरात आधीपासून एलपीजी जोडणी नाही, ती पात्र आहे.",
            },
            "benefits": {
                "en": "Eligible women get an LPG connection without paying the security deposit. The aim is to provide clean cooking fuel to poor households.",
                "hi": "पात्र महिलाओं को सुरक्षा जमा राशि दिए बिना एलपीजी कनेक्शन मिलता है। उद्देश्य गरीब परिवारों को स्वच्छ खाना पकाने का ईंधन उपलब्ध कराना है।",
                "mr": "पात्र महिलांना सुरक्षा ठेव न भरता एलपीजी जोडणी मिळते. गरीब कुटुंबांना स्वच्छ स्वयंपाकाचे इंधन उपलब्ध करून देणे हा उद्देश आहे.",
            },
            "documents": {
                "en": "Aadhaar card, proof of address, a bank account and the family's below-poverty-line or similar eligibility proof are required along with the application form.",
                "hi": "आवेदन पत्र के साथ आधार कार्ड, पते का प्रमाण, बैंक खाता और परिवार का गरीबी रेखा से नीचे या समान पात्रता प्रमाण आवश्यक है।",
                "mr": "अर्जासोबत आधार कार्ड, पत्त्याचा पुरावा, बँक खाते आणि कुटुंबाचा दारिद्र्यरेषेखालील किंवा तत्सम पात्रतेचा पुरावा आवश्यक आहे.",
            },
            "how_to_apply": {
                "en": "Applicants can submit the KYC application form at the nearest LPG distributor. The form can also be downloaded from the official PMUY portal.",
                "hi": "आवेदक निकटतम एलपीजी वितरक के पास केवाईसी आवेदन पत्र जमा कर सकते हैं। यह फॉर्म आधिकारिक पीएमयूवाई पोर्टल से भी डाउनलोड किया जा सकता है।",
                "mr": "अर्जदार जवळच्या एलपीजी वितरकाकडे केवायसी अर्ज सादर करू शकतात. हा अर्ज अधिकृत पीएमयूवाय पोर्टलवरूनही डाउनलोड करता येतो.",
            },
        },
    },
    {
        "id": "ssy", "level": "central", "url": "https://www.indiapost.gov.in/",
        "names": {
            "en": "Sukanya Samriddhi Yojana (SSY)",
            "hi": "सुकन्या समृद्धि योजना (एसएसवाई)",
            "mr": "सुकन्या समृद्धी योजना (एसएसवाय)",
        },
        "aliases": ["sukanya", "sukanya samriddhi", "ssy", "सुकन्या"],
        "sections": {
            "eligibility": {
                "en": "An account can be opened in the name of a girl child who is below 10 years of age. A parent or legal guardian opens and operates the account, and only one account is allowed per girl.",
                "hi": "10 वर्ष से कम आयु की बालिका के नाम पर खाता खोला जा सकता है। माता-पिता या कानूनी अभिभावक खाता खोलते और संचालित करते हैं, और प्रत्येक बालिका के लिए केवल एक खाता अनुमत है।",
                "mr": "10 वर्षांपेक्षा कमी वयाच्या मुलीच्या नावाने खाते उघडता येते. पालक किंवा कायदेशीर संरक्षक खाते उघडतात व चालवतात, आणि प्रत्येक मुलीसाठी फक्त एकच खाते चालते.",
            },
            "benefits": {
                "en": "The minimum deposit is ₹250 per year and the maximum is ₹1.5 lakh per year. The account matures 21 years after opening, and the interest rate is notified by the government every quarter.",
                "hi": "न्यूनतम जमा ₹250 प्रति वर्ष और अधिकतम ₹1.5 लाख प्रति वर्ष है। खाता खोलने के 21 वर्ष बाद परिपक्व होता है, और ब्याज दर सरकार हर तिमाही अधिसूचित करती है।",
                "mr": "किमान ठेव दरवर्षी ₹250 आणि कमाल ठेव दरवर्षी ₹1.5 लाख आहे. खाते उघडल्यापासून 21 वर्षांनी परिपक्व होते, आणि व्याजदर सरकार दर तिमाहीला जाहीर करते.",
            },
            "documents": {
                "en": "The girl's birth certificate and the identity and address proof of the parent or guardian are required.",
                "hi": "बालिका का जन्म प्रमाण पत्र तथा माता-पिता या अभिभावक के पहचान और पते का प्रमाण आवश्यक है।",
                "mr": "मुलीचा जन्म दाखला तसेच पालक किंवा संरक्षकाचा ओळख आणि पत्त्याचा पुरावा आवश्यक आहे.",
            },
            "how_to_apply": {
                "en": "The account can be opened at any post office or at authorised branches of banks by submitting the account opening form with the documents and the initial deposit.",
                "hi": "खाता किसी भी डाकघर या बैंकों की अधिकृत शाखाओं में खाता खोलने का फॉर्म, दस्तावेज़ और प्रारंभिक जमा के साथ जमा करके खोला जा सकता है।",
                "mr": "खाते कोणत्याही पोस्ट ऑफिसमध्ये किंवा बँकांच्या अधिकृत शाखांमध्ये खाते उघडण्याचा अर्ज, कागदपत्रे आणि प्रारंभिक ठेवीसह सादर करून उघडता येते.",
            },
        },
    },
    {
        "id": "apy", "level": "central", "url": "https://www.npscra.nsdl.co.in/scheme-details.php",
        "names": {
            "en": "Atal Pension Yojana (APY)",
            "hi": "अटल पेंशन योजना (एपीवाई)",
            "mr": "अटल पेन्शन योजना (एपीवाय)",
        },
        "aliases": ["atal pension", "apy", "अटल पेंशन", "अटल पेन्शन"],
        "sections": {
            "eligibility": {
                "en": "Indian citizens aged 18 to 40 years who have a savings bank account can join. Income taxpayers are not eligible to join after 1 October 2022.",
                "hi": "18 से 40 वर्ष की आयु के भारतीय नागरिक जिनके पास बचत बैंक खाता है, इसमें शामिल हो सकते हैं। 1 अक्टूबर 2022 के बाद आयकर दाता शामिल होने के पात्र नहीं हैं।",
                "mr": "18 ते 40 वर्षे वयाचे बचत बँक खाते असलेले भारतीय नागरिक यात सहभागी होऊ शकतात. 1 ऑक्टोबर 2022 नंतर आयकरदाते सहभागी होण्यास पात्र नाहीत.",
            },
            "benefits": {
                "en": "Subscribers receive a guaranteed monthly pension of ₹1,000 to ₹5,000 from the age of 60, depending on the contribution chosen.",
                "hi": "चुने गए अंशदान के अनुसार अभिदाताओं को 60 वर्ष की आयु से ₹1,000 से ₹5,000 तक की गारंटीशुदा मासिक पेंशन मिलती है।",
                "mr": "निवडलेल्या वर्गणीनुसार सदस्यांना वयाच्या 60 व्या वर्षापासून ₹1,000 ते ₹5,000 पर्यंत हमखास मासिक पेन्शन मिळते.",
            },
            "documents": {
                "en": "Aadhaar card or other identity proof, a mobile number and a savings bank account number are needed to enrol.",
                "hi": "नामांकन के लिए आधार कार्ड या अन्य पहचान प्रमाण, मोबाइल नंबर और बचत बैंक खाता संख्या आवश्यक है।",
                "mr": "नोंदणीसाठी आधार कार्ड किंवा इतर ओळखपत्र, मोबाइल नंबर आणि बचत बँक खाते क्रमांक आवश्यक आहे.",
            },
            "how_to_apply": {
                "en": "Enrol through the bank branch or post office where the savings account is held, or through the bank's net banking or mobile app where available. Monthly contributions are auto-debited from the account.",
                "hi": "बचत खाता जिस बैंक शाखा या डाकघर में है, वहां या जहां उपलब्ध हो वहां बैंक की नेट बैंकिंग या मोबाइल ऐप से नामांकन करें। मासिक अंशदान खाते से स्वतः कट जाता है।",
                "mr": "बचत खाते असलेल्या बँक शाखेत किंवा पोस्ट ऑफिसमध्ये, किंवा उपलब्ध असल्यास बँकेच्या नेट बँकिंग किंवा मोबाइल ॲपद्वारे नोंदणी करा. मासिक वर्गणी खात्यातून आपोआप वजा होते.",
            },
        },
    },
    {
        "id": "mudra", "level": "central", "url": "https://www.mudra.org.in/",
        "names": {
            "en": "Pradhan Mantri Mudra Yojana (PMMY)",
            "hi": "प्रधानमंत्री मुद्रा योजना (पीएमएमवाई)",
            "mr": "प्रधानमंत्री मुद्रा योजना (पीएमएमवाय)",
        },
        "aliases": ["mudra", "pmmy", "मुद्रा"],
        "tables": {  # rendered as a real table inside the benefits section (tests table preservation)
            "benefits": {
                "en": [["Category", "Loan amount"], ["Shishu", "up to ₹50,000"], ["Kishor", "₹50,001 to ₹5 lakh"], ["Tarun", "₹5 lakh to ₹10 lakh"]],
                "hi": [["श्रेणी", "ऋण राशि"], ["शिशु", "₹50,000 तक"], ["किशोर", "₹50,001 से ₹5 लाख"], ["तरुण", "₹5 लाख से ₹10 लाख"]],
                "mr": [["श्रेणी", "कर्जाची रक्कम"], ["शिशु", "₹50,000 पर्यंत"], ["किशोर", "₹50,001 ते ₹5 लाख"], ["तरुण", "₹5 लाख ते ₹10 लाख"]],
            }
        },
        "sections": {
            "eligibility": {
                "en": "Any Indian citizen with a business plan for a non-farm income-generating activity in manufacturing, processing, trading or services can apply for a loan up to ₹10 lakh.",
                "hi": "विनिर्माण, प्रसंस्करण, व्यापार या सेवा क्षेत्र में गैर-कृषि आय-सृजन गतिविधि की व्यवसाय योजना वाला कोई भी भारतीय नागरिक ₹10 लाख तक के ऋण के लिए आवेदन कर सकता है।",
                "mr": "उत्पादन, प्रक्रिया, व्यापार किंवा सेवा क्षेत्रात बिगरशेती उत्पन्न देणाऱ्या व्यवसायाची योजना असलेला कोणताही भारतीय नागरिक ₹10 लाखांपर्यंतच्या कर्जासाठी अर्ज करू शकतो.",
            },
            "benefits": {
                "en": "Collateral-free loans are offered in three categories according to the loan amount.",
                "hi": "ऋण राशि के अनुसार तीन श्रेणियों में बिना गारंटी के ऋण दिए जाते हैं।",
                "mr": "कर्जाच्या रकमेनुसार तीन श्रेणींमध्ये तारणमुक्त कर्ज दिले जाते.",
            },
            "documents": {
                "en": "Identity and address proof, a passport-size photograph, and proof of the business such as registration or licence are usually needed.",
                "hi": "पहचान और पते का प्रमाण, पासपोर्ट आकार का फोटो और व्यवसाय का प्रमाण जैसे पंजीकरण या लाइसेंस आमतौर पर आवश्यक होते हैं।",
                "mr": "ओळख आणि पत्त्याचा पुरावा, पासपोर्ट आकाराचा फोटो आणि नोंदणी किंवा परवाना यांसारखा व्यवसायाचा पुरावा साधारणपणे लागतो.",
            },
            "how_to_apply": {
                "en": "Apply at any bank, microfinance institution or non-banking finance company that offers Mudra loans, or through the Udyamimitra portal.",
                "hi": "मुद्रा ऋण देने वाले किसी भी बैंक, सूक्ष्म वित्त संस्था या गैर-बैंकिंग वित्त कंपनी में या उद्यमिमित्र पोर्टल के माध्यम से आवेदन करें।",
                "mr": "मुद्रा कर्ज देणाऱ्या कोणत्याही बँक, सूक्ष्म वित्त संस्था किंवा बिगर-बँकिंग वित्तीय कंपनीकडे किंवा उद्यमिमित्र पोर्टलद्वारे अर्ज करा.",
            },
        },
    },
    {
        "id": "pmfby", "level": "central", "url": "https://pmfby.gov.in/",
        "names": {
            "en": "Pradhan Mantri Fasal Bima Yojana (PMFBY)",
            "hi": "प्रधानमंत्री फसल बीमा योजना (पीएमएफबीवाई)",
            "mr": "प्रधानमंत्री पीक विमा योजना (पीएमएफबीवाय)",
        },
        "aliases": ["pmfby", "fasal bima", "pik vima", "crop insurance", "फसल बीमा", "पीक विमा", "पीएमएफबीवाई", "पीएमएफबीवाय"],
        "sections": {
            "eligibility": {
                "en": "All farmers growing notified crops in notified areas, including sharecroppers and tenant farmers, can enrol. Enrolment is voluntary for all farmers.",
                "hi": "अधिसूचित क्षेत्रों में अधिसूचित फसलें उगाने वाले सभी किसान, जिनमें बटाईदार और काश्तकार भी शामिल हैं, नामांकन कर सकते हैं। सभी किसानों के लिए नामांकन स्वैच्छिक है।",
                "mr": "अधिसूचित क्षेत्रात अधिसूचित पिके घेणारे सर्व शेतकरी, ज्यात बटाईदार आणि कुळ शेतकऱ्यांचाही समावेश आहे, नोंदणी करू शकतात. सर्व शेतकऱ्यांसाठी नोंदणी ऐच्छिक आहे.",
            },
            "benefits": {
                "en": "Farmers pay a premium of 2 percent for kharif food and oilseed crops, 1.5 percent for rabi crops and 5 percent for commercial and horticultural crops. Insurance covers yield losses due to natural calamities, pests and diseases.",
                "hi": "किसान खरीफ की खाद्यान्न और तिलहन फसलों के लिए 2 प्रतिशत, रबी फसलों के लिए 1.5 प्रतिशत और वाणिज्यिक तथा बागवानी फसलों के लिए 5 प्रतिशत प्रीमियम देते हैं। बीमा प्राकृतिक आपदाओं, कीटों और रोगों से होने वाली उपज हानि को कवर करता है।",
                "mr": "शेतकरी खरीप अन्नधान्य व तेलबिया पिकांसाठी 2 टक्के, रब्बी पिकांसाठी 1.5 टक्के आणि व्यावसायिक व फळबाग पिकांसाठी 5 टक्के हप्ता भरतात. विमा नैसर्गिक आपत्ती, कीड आणि रोगांमुळे होणाऱ्या उत्पादन नुकसानीस संरक्षण देतो.",
            },
            "documents": {
                "en": "Aadhaar card, bank account passbook, land records or a tenancy agreement, and a sowing declaration are needed.",
                "hi": "आधार कार्ड, बैंक पासबुक, भूमि अभिलेख या किरायेदारी अनुबंध और बुवाई की घोषणा आवश्यक हैं।",
                "mr": "आधार कार्ड, बँक पासबुक, जमिनीचे अभिलेख किंवा कुळवहिवाटीचा करार आणि पेरणीचे घोषणापत्र आवश्यक आहे.",
            },
            "how_to_apply": {
                "en": "Farmers can enrol through the National Crop Insurance Portal, a bank branch, a Common Service Centre or an authorised insurance agent before the notified cut-off date for each season.",
                "hi": "किसान प्रत्येक मौसम की अधिसूचित अंतिम तिथि से पहले राष्ट्रीय फसल बीमा पोर्टल, बैंक शाखा, कॉमन सर्विस सेंटर या अधिकृत बीमा एजेंट के माध्यम से नामांकन कर सकते हैं।",
                "mr": "शेतकरी प्रत्येक हंगामासाठी अधिसूचित अंतिम तारखेपूर्वी राष्ट्रीय पीक विमा पोर्टल, बँक शाखा, कॉमन सर्व्हिस सेंटर किंवा अधिकृत विमा प्रतिनिधीमार्फत नोंदणी करू शकतात.",
            },
        },
    },
    {
        "id": "namo_shetkari", "level": "state", "url": "https://krishi.maharashtra.gov.in/",
        "names": {
            "en": "Namo Shetkari Mahasanman Nidhi Yojana",
            "hi": "नमो शेतकरी महासन्मान निधि योजना",
            "mr": "नमो शेतकरी महासन्मान निधी योजना",
        },
        "aliases": ["namo shetkari", "namo", "नमो शेतकरी", "नमो"],
        "sections": {
            "eligibility": {
                "en": "Farmers of Maharashtra who are eligible beneficiaries under PM-KISAN are eligible for this state scheme.",
                "hi": "महाराष्ट्र के जो किसान पीएम-किसान के पात्र लाभार्थी हैं, वे इस राज्य योजना के लिए पात्र हैं।",
                "mr": "पीएम-किसान अंतर्गत पात्र लाभार्थी असलेले महाराष्ट्रातील शेतकरी या राज्य योजनेसाठी पात्र आहेत.",
            },
            "benefits": {
                "en": "The state government gives an additional ₹6,000 per year to eligible farmers, paid in three instalments of ₹2,000 each, on top of the PM-KISAN amount.",
                "hi": "राज्य सरकार पात्र किसानों को पीएम-किसान राशि के अतिरिक्त प्रति वर्ष ₹6,000 देती है, जो ₹2,000 की तीन किस्तों में दिए जाते हैं।",
                "mr": "राज्य सरकार पात्र शेतकऱ्यांना पीएम-किसान रकमेव्यतिरिक्त दरवर्षी ₹6,000 देते, जे ₹2,000 च्या तीन हप्त्यांमध्ये दिले जातात.",
            },
            "documents": {
                "en": "The same documents as PM-KISAN are used: Aadhaar card, land records and an Aadhaar-linked bank account.",
                "hi": "पीएम-किसान के समान दस्तावेज़ उपयोग किए जाते हैं: आधार कार्ड, भूमि अभिलेख और आधार से जुड़ा बैंक खाता।",
                "mr": "पीएम-किसानप्रमाणेच कागदपत्रे वापरली जातात: आधार कार्ड, जमिनीचे अभिलेख आणि आधारशी जोडलेले बँक खाते.",
            },
            "how_to_apply": {
                "en": "Eligibility is linked to PM-KISAN registration, so farmers should first complete or update their PM-KISAN registration. Details can be confirmed at the village agriculture office or the Krishi Sahayak.",
                "hi": "पात्रता पीएम-किसान पंजीकरण से जुड़ी है, इसलिए किसानों को पहले अपना पीएम-किसान पंजीकरण पूरा या अपडेट करना चाहिए। जानकारी गांव के कृषि कार्यालय या कृषि सहायक से सत्यापित की जा सकती है।",
                "mr": "पात्रता पीएम-किसान नोंदणीशी जोडलेली आहे, त्यामुळे शेतकऱ्यांनी आधी त्यांची पीएम-किसान नोंदणी पूर्ण किंवा अद्ययावत करावी. माहितीची खात्री गावातील कृषी कार्यालय किंवा कृषी सहायकाकडे करता येते.",
            },
        },
    },
]
