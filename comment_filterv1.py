# comment_filter.py - Enhanced AI Comment Filtering System v3
#
# Detection categories:
#   1. Hate Speech          - identity-based attacks
#   2. Harassment           - direct personal attacks
#   3. Threats              - physical/violent intent
#   4. Sexual Harassment    - unwanted sexual remarks
#   5. Profanity            - strong abusive language
#   6. Cyberbullying        - repeated targeted mockery
#   7. Toxic Sarcasm        - mocking/humiliating tone
#   8. Discrimination       - derogatory group targeting
#   9. Spam
#
# Languages: English, Hindi (Devanagari + Hinglish), Kannada (script + Kanglish)
# Architecture: Rule-based word banks + TF-IDF + Logistic Regression (CPU-only)

import re
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

# =============================================================================
# SECTION 1 — TOXIC CATEGORY PATTERNS (English + Romanized)
# =============================================================================

# ── 1a. HATE SPEECH ──────────────────────────────────────────────────────────
HATE_SPEECH_PATTERNS = [
    r'\bpeople like you\b.*\b(don.t belong|shouldn.t exist|are the problem)\b',
    r'\b(your kind|their kind|those people)\b.*\b(always|never|don.t|can.t)\b',
    r'\b(go back to|belong in)\b.*\b(your country|where you came from)\b',
    r'\b(you|they|your kind)\b.*\bdon.t deserve\b',
    r'\b(inferior|subhuman|lesser|primitive)\b.*\b(race|religion|group|people|caste)\b',
    r'\bshould be\b.*\b(banned|removed|deported|exterminated)\b',
]

HATE_SPEECH_KEYWORDS = {
    # Identity-based attacks (English)
    "vermin", "subhuman", "inferior race", "go back to your country",
    "your kind", "those people", "people like you don't belong",
    "you don't belong here", "shouldn't exist", "lower caste",
    # Hinglish identity attacks
    "tum log yahan nahi chahiye", "tumhari jaat", "neechi jaat",
    "tumhara dharm bekaar", "tumhara desh chodo",
    # Kanglish identity attacks
    "nimma jaathi", "nimage illi jagilla", "hodi hogi",
    "nimma dharma bekilla",
}

# ── 1b. HARASSMENT ───────────────────────────────────────────────────────────
HARASSMENT_PATTERNS = [
    r'\byou\b.*\b(are|re|r)\b.*\b(completely|totally|absolutely|utterly)\b.*\b(useless|worthless|pathetic|incompetent|stupid|dumb|idiot|moron|trash|garbage)\b',
    r'\b(nobody|no one|everyone|everybody)\b.*\b(likes|wants|cares about|respects)\b.*\byou\b',
    r'\byou\b.*\b(will never|can never|can.t|won.t ever)\b.*\b(succeed|amount|do|be)\b',
    r'\byou\b.*\b(should|deserve to)\b.*\b(leave|quit|disappear|go away|die|be gone)\b',
    r'\b(loser|waste of space|waste of time|burden|embarrassment)\b',
]

# ── Additional dismissive hostile phrases (pattern-based) ──────────────────
HOSTILE_DISMISSAL_PATTERNS = [
    r'(shut up|shut it|shut your mouth|shut your face)',
    r'(get lost|get out|go away|leave me alone|piss off|bugger off|bog off|sod off)',
    r'(nobody asked|no one asked|who asked you|who cares what you think)',
    r'(what rubbish|what nonsense|what garbage|what trash|what crap|what bull)',
    r'\b(you are rubbish|you are trash|you are garbage)\b',
    r'(this is rubbish|this is nonsense|this is garbage|this is bull)',
    r'(i hate (you|this|it|everything|everyone))',
    r'(i (despise|loathe|detest|abhor) you)',
    r'(you disgust me|you make me sick|you make me want to vomit)',
    r'(this sucks|you suck|it sucks|everything sucks)',
    r'\b(you are a joke|you are a clown|you are a bozo|you are an idiot|you are a fool|you are a muppet)\b',
    r'(go (to hell|die|kill yourself|end yourself|jump off))',
    r'\b(cringe|cringeworthy|so cringe|this is cringe)\b',
    r'(embarrassing yourself|embarrass yourself|so embarrassing)',
    r'(i hate (your|this|their) (content|post|page|channel|blog|face|voice))',
    # Hinglish dismissals
    r'(chup kar|chup ho ja|nikal ja|bhag ja|ja yahan se)',
    r'(bakwaas hai|ye kya bakwaas|kya nonsense|kya bakwaas)',
    r'(tujhse nafrat|main tujhse nafrat|mujhe tujhse nafrat)',
    # Kanglish dismissals
    r'(hogi bidi|hogi nimdu|bidi nimdu|illa yenu)',
    r'(nimma content bekilla|yenu idu bakwaas|idu trash)',
]

HARASSMENT_KEYWORDS = {
    # English
    "you are completely useless", "you are worthless", "you are pathetic",
    "nobody likes you", "no one wants you", "everyone hates you",
    "you will never succeed", "you should quit", "you are a burden",
    "waste of space", "waste of time", "you are an embarrassment",
    "you are a failure", "you are a joke", "total loser",
    "utter failure", "complete idiot", "you're nothing",
    # Hinglish harassment
    "tu bilkul bekaar hai", "koi tujhe pasand nahi karta",
    "tu kuch nahi kar sakta", "tu ek failure hai",
    "sab tujhse nafrat karte hain", "tu ek bakwaas insaan hai",
    "tu ek burden hai", "tu ghatiya hai", "tu nikamma hai",
    # Kanglish harassment
    "neevu yenu madolla", "nim ge yenu gothilla",
    "ella jana nimage ishtavilla", "neevu ondh failure",
    "neevu bekilla", "neevu useless", "nimage yenu aagolla",
}

# ── 1c. THREATS ──────────────────────────────────────────────────────────────
THREAT_PATTERNS = [
    r'\b(you.ll|you will|you.re going to|gonna)\b.*\b(regret|pay for|suffer|face consequences)\b',
    r'\b(i.ll|i will|i.m going to|gonna)\b.*\b(find|get|hurt|harm|destroy|ruin|kill|make you pay)\b.*\byou\b',
    r'\bwatch\b.*\byour\b.*\bback\b',
    r'\b(kill|murder|hurt|harm|destroy|beat|attack)\b.*\byou\b',
    r'\byou\b.*\bwon.t\b.*\b(get away|be safe|last long|survive)\b',
    r'\b(come for you|find you|track you|hunt you)\b',
    r'\b(send|post|expose|leak)\b.*\b(your|the|their)\b.*\b(address|location|info|details|photos|pictures)\b',
    r'\bmar denge\b|\bchod dunga\b|\btujhe dekhna\b',
    r'\bnobody\b.*\bsave\b.*\byou\b',
]

THREAT_KEYWORDS = {
    # English
    "you'll regret this", "you will regret this", "watch your back",
    "you won't get away", "i will find you", "i'll get you",
    "you're going to pay", "make you pay", "come after you",
    "hunt you down", "i know where you live", "not going to be safe",
    "better be careful", "your days are numbered",
    # Hinglish threats
    "tu pachtaega", "tujhe dekhna", "teri khabar karta hun",
    "tujhe chodungi nahi", "bata dunga tujhe", "aa ja samne",
    "tujhe mar dunga", "dekh lena tujhe",
    # Kanglish threats
    "nimage hoguthaini", "neevu nodikoli", "nange sigbedi",
    "nim kade barteeni", "nimage thoorbeke",
}

# ── 1d. SEXUAL HARASSMENT ────────────────────────────────────────────────────
SEXUAL_HARASSMENT_PATTERNS = [
    r'\b(send|show|share)\b.*\b(nudes|photos|pictures|body|private)\b',
    r'\b(you.re|you are)\b.*\b(so sexy|so hot|fuckable|bangable)\b',
    r'\bwant to\b.*\b(f[u\*]ck|sleep with|have sex with|do it with)\b.*\byou\b',
    r'\b(sexual|sex|body|physical)\b.*\b(favor|demand|request|want)\b',
    r'\bstop\b.*\b(sending|texting|messaging)\b.*\b(inappropriate|sexual|explicit)\b',
]

SEXUAL_HARASSMENT_KEYWORDS = {
    # English (mild / non-graphic versions)
    "send me your photos", "send nudes", "you're so sexy", "you look hot",
    "stop sending inappropriate messages", "you want it",
    "i know you want it", "sexual messages", "inappropriate messages",
    "inappropriate pictures", "stop harassing me sexually",
    # Hinglish
    "apni photo bhejo", "bahut sexy ho tum", "tum bahut hot ho",
    "mujhe achhe lagte ho aise", "galat message mat bhejo",
    # Kanglish
    "photo kalisu", "neevu tumba sexy agidira", "inappropriate message kalisbedu",
}

# ── 1e. PROFANITY (English + Hinglish + Kanglish) ───────────────────────────
EN_PROFANITY = {
    # Strong abusive English
    'damn', 'hell', 'ass', 'bastard', 'bitch', 'shit', 'fuck', 'crap',
    'dick', 'cock', 'pussy', 'whore', 'slut', 'faggot', 'cunt',
    'motherfucker', 'asshole', 'douchebag', 'jackass', 'prick',
    'bullshit', 'horseshit', 'dipshit', 'shithead', 'fuckwit',
    # Moderate
    'jerk', 'scum', 'freak', 'psycho', 'creep', 'pervert',
    'moron', 'imbecile', 'nitwit', 'halfwit', 'dimwit',
    'dumbass', 'stupid', 'idiot', 'dumb', 'ugly', 'loser',
    'kill', 'die', 'trash', 'garbage', 'worthless', 'pathetic',
    'disgusting', 'gross', 'awful', 'terrible', 'useless',
    'failure', 'hopeless', 'miserable', 'horrible', 'hate',
    'filth', 'filthy', 'ruin', 'destroy', 'scumbag', 'lowlife',
    'deadbeat', 'degenerate', 'vermin', 'pest', 'nutcase',
    # Common dismissive / hostile phrases people actually use
    'rubbish', 'nonsense', 'pathetic', 'disgusting', 'disgusted',
    'sucks', 'suck', 'sucking', 'shut up', 'shut it', 'get lost',
    'go away', 'get out', 'leave me alone', 'nobody asked',
    'no one asked', 'who asked', 'irrelevant', 'clown', 'clowns',
    'buffoon', 'ridiculous', 'absurd', 'embarrassing', 'cringeworthy',
    'cringe', 'eww', 'ew', 'yikes', 'bruh', 'bozo', 'dunce',
    'twit', 'numskull', 'muppet', 'prat', 'wanker', 'tosser',
    'git', 'pillock', 'muppet', 'slag', 'thicko', 'doofus',
    'dimwit', 'bonehead', 'blockhead', 'knucklehead', 'lamebrain',
    'dumbo', 'dolt', 'dullard', 'nincompoop', 'ninny', 'chump',
    # Hate/disgust direction words
    'despise', 'loathe', 'abhor', 'detest', 'repulsed',
    'vomit', 'nauseating', 'nauseous', 'revolting', 'repugnant',
}

HINGLISH_PROFANITY = {
    # Romanized Hindi — mild to strong
    'bakwaas', 'bevakoof', 'bewakoof', 'gadha', 'gadhe', 'ullu',
    'nalayak', 'kamina', 'kamine', 'harami', 'haramkhor', 'saala',
    'saali', 'besharam', 'darpok', 'nikamma', 'faltu', 'ghatiya',
    'ganda', 'bekar', 'bekaar', 'kutte', 'kutta', 'suar', 'suwar',
    'bhikari', 'chor', 'bhadwa', 'randwa', 'gawar', 'jahil',
    'andha', 'pagal', 'mental', 'paagal', 'kachra', 'kamine log',
    'teri maa', 'tera baap', 'bhad mein jao', 'chup ho jao',
    'bakwaas band karo', 'muh band karo', 'nikal yahan se',
    # Stronger (romanized, non-graphic)
    'chutiya', 'madarchod', 'behenchod', 'bhosdike', 'randi',
    'haraami', 'bkl', 'mc', 'bc', 'lund', 'gaand',
    # Hostile dismissals (Hinglish)
    'chup kar', 'chup ho', 'nikal ja', 'bhag ja', 'ja yahan se',
    'kya bakwaas', 'bakwaas band kar', 'ye bakwaas', 'yeh bakwaas',
    'tujhse nafrat', 'nafrat hai', 'ghanta', 'bakwas',
}

KANGLISH_PROFANITY = {
    # Romanized Kannada — mild to strong
    'bekilla', 'huchcha', 'daDDa', 'peda', 'naayi', 'nayee', 'nayi',
    'bevarse', 'bevarsi', 'sullu', 'sully', 'kalla', 'kalli',
    'badmash', 'chamcha', 'thikka', 'thika', 'hoda', 'hodakke',
    'nimma hakku', 'maga', 'magane', 'mundey', 'mundo',
    'madake', 'haavina makklu', 'naachike illa', 'naachikegetta',
    'boLu', 'bolu', 'ulta', 'yenu gothilla nimge', 'yenu madthira',
    # Stronger romanized (non-graphic)
    'sule', 'sooley', 'tika', 'tikaklage', 'nin amana',
    'nim amna', 'sala', 'saley', 'hole', 'hole maga',
    'kerige hogi', 'tika mele', 'bidi ninge', 'nimma thika',
}

# ── 1f. CYBERBULLYING ────────────────────────────────────────────────────────
CYBERBULLYING_PATTERNS = [
    r'\beveryone\b.*\b(knows|says|thinks|agrees)\b.*\b(you.re|you are)\b.*\b(a joke|stupid|useless|pathetic|loser|ugly|weird|creep)\b',
    r'\b(always|never)\b.*\b(fail|mess up|get it wrong|embarrass yourself)\b',
    r'\bno one\b.*\b(likes|wants|respects|cares about)\b.*\byou\b',
    r'\b(laugh at|mock|make fun of|ridicule)\b.*\byou\b',
    r'\b(spread|share|post|tell everyone)\b.*\babout\b.*\byou\b',
    r'\byou.re\b.*\b(always|forever|never going to be)\b.*\b(a loser|ugly|stupid|pathetic|nothing)\b',
]

CYBERBULLYING_KEYWORDS = {
    # English
    "everyone knows you're a joke", "everyone hates you",
    "you'll always be a failure", "nobody will ever like you",
    "you're always messing up", "you never get it right",
    "laughing at you", "make fun of you", "you are so ugly",
    "you'll never change", "always been a loser", "you'll always fail",
    "you're such a crybaby", "such a attention seeker",
    # Hinglish cyberbullying
    "sab tujhpe hasate hain", "tu hamesha galat karta hai",
    "koi tera dost nahi", "tu hamesha fail hoga",
    "sab jaante hain tu ek joke hai",
    # Kanglish cyberbullying
    "ella jana ninage nakkathare", "neevu yavaglu fail agthira",
    "nimage yaaru ishtapadalla", "neevu yavaglu sari agalla",
}

# ── 1g. DISCRIMINATION ───────────────────────────────────────────────────────
DISCRIMINATION_PATTERNS = [
    r'\b(your|their|those)\b.*\b(kind|type|people|race|religion|caste|community|group)\b.*\b(always|never|always fail|are inferior|can.t|don.t)\b',
    r'\b(typical|classic|expected)\b.*\b(from|of|for)\b.*\b(your|their|those|a)\b.*\b(kind|people|race|religion|community|caste|gender|group)\b',
    r'\b(because|since)\b.*\b(you.re|you are)\b.*\b(a|an)\b.*\b(woman|man|muslim|hindu|christian|black|white|dalit|brahmin|muslim|gay|lesbian)\b',
]

DISCRIMINATION_KEYWORDS = {
    # English
    "your kind always fails", "your kind always loses",
    "typical of your kind", "expected from your kind",
    "your people are all the same", "you people always",
    "your religion is", "your caste is inferior",
    "because you're a woman", "because you're a man",
    "women can't do this", "men are always like this",
    "your community is backward", "your community can't",
    # Hinglish discrimination
    "tumhari jaat yahi karti hai", "tumhara dharm hi aisa hai",
    "tumhare log hamesha yahi karte hain",
    "tumhare jaise log hamesha haarte hain",
    "aurat hoke ye nahi kar sakti",
    # Kanglish discrimination
    "nimma jaathi iddange", "nimma dharma heege",
    "nimma community yavaglu heege", "hengasru idu madoke agolla",
}

# ── 1h. APPEARANCE MOCKING / BODY SHAMING ────────────────────────────────────
# Covers indirect insults via comparisons, metaphors, animal/object likening
# e.g. "looks like a ghost", "bhoot jayse hai", "devva tara ide"

APPEARANCE_MOCK_PATTERNS = [
    r'\b(looks?|look)\b.{0,20}\b(like|similar to|just like|exactly like)\b.{0,30}\b(ghost|zombie|monster|witch|demon|devil|corpse|rat|pig|cow|donkey|monkey|ape|gorilla|clown|scarecrow|troll|ogre|beast|creature|freak|alien|vampire|skeleton)\b',
    r'\b(you|he|she|they|ur|u)\b.{0,10}\b(look|looks|looked)\b.{0,20}\b(dead|disgusting|horrifying|terrible|hideous|awful|gross|scary|terrifying|nasty|revolting)\b',
    r'\b(face|body|hair|skin)\b.{0,15}\b(like|resembles?|looks? like)\b.{0,20}\b(garbage|trash|mess|disaster|horror|nightmare|mistake|accident)\b',
    r'\b(what happened to|what is wrong with)\b.{0,10}\b(your|ur|his|her)\b.{0,10}\b(face|body|hair|skin|looks?|appearance)\b',
    r'\byou.re\b.{0,10}\b(hideous|repulsive|revolting|grotesque|vile)\b',
    r'\b(so fat|so skinny|too fat|too thin|obese|chubby)\b',
    r'\b(ugly as|ugly like|as ugly as)\b',
    r'\b(aana|aane|haathi|hathi)\b.{0,10}\b(tarah|tara|jaisa|jaisi|tara ide|tara kanthare)\b',
    # Kanglish ghost/devva patterns
    r'\b(devva|bhoota|bhoota|pisachi|rakshasa|zombie)\b.{0,10}\b(tara|taradanta|taradante|tara ide|tara kanthare|tara kanisthare|tara irthare)\b',
    # Hinglish ghost/bhoot patterns
    r'\b(bhoot|daayan|chudail|raakshas|pisach|zombie)\b.{0,10}\b(jaisa|jaisi|ki tarah|lag raha|lag rahi|dikhta|dikhti|jayse|jaise|jaese)\b',
    r'\b(bhoot|bhut)\b.{0,5}\b(jayse|jaise|jaisa|jaisi|tara|tarah)\b',
]

APPEARANCE_MOCK_KEYWORDS_EN = {
    "looks like a ghost", "look like a ghost", "you look like a ghost",
    "like a zombie", "looks like a zombie", "looks like a monster",
    "looks like a demon", "looks like a witch", "looks like a devil",
    "looks like a corpse", "looks like a scarecrow", "looks like a clown",
    "looks like a freak", "you look dead", "your face looks terrible",
    "you are so ugly", "you're so ugly", "so ugly it hurts",
    "ugly as sin", "ugly as hell", "you're hideous", "you're repulsive",
    "what happened to your face", "what's wrong with your face",
    "your body is disgusting", "you look disgusting", "you look gross",
    "looks like a monkey", "looks like an ape", "face like a pig",
    "you look like a rat", "you look like a cow", "looks like a gorilla",
    "its looks like a ghost",
}

APPEARANCE_MOCK_KEYWORDS_HINGLISH = {
    "bhoot jayse hai", "bhoot jaise hai", "bhoot jaisa hai",
    "bhoot jaisi hai", "bhoot jaisa dikhta hai", "bhoot jaisi dikhti hai",
    "bhoot lag raha hai", "bhoot lag rahi hai", "bhoot ki tarah",
    "bhoot tarah", "bhoot jaisa lag raha", "bhoot lagta hai",
    "daayan jaisi lag rahi hai", "daayan jaisa", "chudail jaisi",
    "raakshas jaisa", "raakshas lag raha hai", "zombie jaisa",
    "teri shakal dekhi hai", "apni shakal dekh", "muh dekh apna",
    "shakal se lage bhoot", "shakal dekho apni", "aaina dekh",
    "itna bura kyun dikhta hai", "itna bura kyun dikhti hai",
    "bahut bura dikhta hai", "bahut bura dikhti hai",
    "chehra dekha toh darr gaya", "bahut mota ho gaya",
    "bahut moti ho gayi", "hathi jaisa", "hathi jaisi",
    "ghinauna lagta hai", "ghinauni lagti hai",
    "dekh ke ulti aati hai", "badsoorat hai", "badsoorat insaan",
    "shakal barbaad hai", "dikhne mein bahut bura",
}

APPEARANCE_MOCK_KEYWORDS_KANGLISH = {
    "devva tara ide", "devva tara kanisthare", "devva tara kanthare",
    "devva tara irthare", "devva taradanta", "devva taradante kanisthare",
    "devva taradanta agide", "devva taradante agidira",
    "bhoota tara ide", "bhoota tara kanthare", "bhoota tara irthare",
    "bhoota tara kanisthare", "bhoota taradanta", "bhoot tara ide",
    "pisachi tara ide", "pisachi tara kanthare",
    "rakshasa tara ide", "rakshasa tara kanthare",
    "zombie tara ide", "zombie tara kanthare",
    "nimma mugha nodi darr aagthade", "mukha nodidre naachike",
    "yenu mugha idu", "mugha channagilla",
    "nodi naachike aagthade", "tumba badsoorat agidira",
    "kanisokke channagilla", "aane taradante agidira", "aane tara ide",
    "maNNu tindavane taradante", "nodidre hasivu hogthade",
    "nimage naachike agbeku", "mukha bhoota taradante",
}

APPEARANCE_MOCK_KEYWORDS_DEVANAGARI = {
    'भूत जैसा', 'भूत जैसी', 'भूत लग रहा', 'भूत लग रही',
    'भूत की तरह', 'भूत दिखता है', 'भूत दिखती है',
    'चुड़ैल जैसी', 'राक्षस जैसा', 'डायन जैसी',
    'इतना बदसूरत', 'इतनी बदसूरत', 'शकल देखो',
    'बदसूरत इंसान', 'इतना मोटा', 'इतनी मोटी',
    'हाथी जैसा', 'हाथी जैसी',
}

APPEARANCE_MOCK_KEYWORDS_KANNADA = {
    'ದೆವ್ವದ ತರ', 'ದೆವ್ವದ ತರ ಕಾಣ್ತಾರೆ', 'ಭೂತದ ತರ',
    'ಭೂತ ತರ ಕಾಣ್ತಾರೆ', 'ರಾಕ್ಷಸ ತರ', 'ಪಿಶಾಚಿ ತರ',
    'ಮುಖ ನೋಡಿದ್ರೆ ಭಯ', 'ಮುಖ ಚೆನ್ನಾಗಿಲ್ಲ',
    'ನೋಡೋಕೆ ಚೆನ್ನಾಗಿಲ್ಲ', 'ತುಂಬಾ ದಡ್ಡ',
    'ಆನೆ ತರ', 'ಆನೆ ತರ ಇದ್ದಾರೆ',
}

# ── 1i. TOXIC SARCASM MARKERS ─────────────────────────────────────────────────
SARCASM_PATTERNS = [
    r'\boh great\b', r'\bjust what i needed\b', r'\bwow so amazing\b',
    r'\bsuper helpful\b', r'\boh sure\b', r'\byeah right\b',
    r'\btotally\b.{0,20}\bnot\b', r'\bbrilliant\b.{0,10}[!]{2,}',
    r'\bwow\b.{0,15}\bbig deal\b', r'\bso impressed\b',
    r'\bsuuure\b', r'\byeaah\b', r'\bwhatever you say\b',
    r'\bif you say so\b', r'\bsure jan\b', r'/s\b',
    r'\bgenius move\b', r'\bnice one\b.{0,10}[!]{2,}',
    r'\boh wow\b.{0,15}\bgenius\b', r'\bvery smart\b.{0,10}[!]',
    r'\bso clever\b', r'\bwhat a genius\b', r'\bgreat job\b.{0,10}[!]{2,}',
    r'\btotally makes sense\b', r'\bobviously\b.{0,20}\bnot\b',
    # Hinglish sarcasm
    r'\bhaan bilkul\b', r'\bwah wah\b.{0,10}[!]',
    r'\bbahut accha kiya\b.{0,10}[!]{2,}', r'\bkya khoob\b',
    r'\bbe shak\b', r'\bzabardast\b.{0,10}[!]{3,}',
    # Kanglish sarcasm
    r'\bhaan haan\b', r'\bsakkath madidira\b.{0,10}[!]{2,}',
    r'\bchannagide\b.{0,10}[!]{3,}',
]

# Toxic escalators that turn sarcasm into a hard block
TOXIC_ESCALATORS = {
    'kill', 'die', 'destroy', 'ruin', 'hate',
    'worthless', 'useless', 'pathetic', 'garbage', 'trash',
    'idiot', 'moron', 'stupid', 'loser', 'scum',
    # Hinglish escalators
    'kamina', 'harami', 'nalayak', 'gadha', 'kutte',
    # Kanglish escalators
    'naayi', 'huchcha', 'sullu', 'bekilla yenu',
}

# =============================================================================
# SECTION 2 — POSITIVE & NEUTRAL WORD BANKS
# =============================================================================

EN_POSITIVE_WORDS = {
    'love', 'awesome', 'amazing', 'beautiful', 'great', 'fantastic',
    'wonderful', 'excellent', 'perfect', 'nice', 'good', 'cool',
    'sweet', 'adorable', 'cute', 'inspiring', 'motivating', 'happy',
    'joyful', 'brilliant', 'outstanding', 'marvelous', 'superb', 'lovely',
    'brilliant', 'impressive', 'stellar', 'magnificent', 'delightful',
    'charming', 'elegant', 'graceful', 'creative', 'talented',
}

HINGLISH_POSITIVE = {
    'bahut accha', 'mast', 'zabardast', 'shandar', 'bindaas',
    'wah', 'shukriya', 'badiya', 'lajawaab', 'ekdum',
    'solid', 'maja aa gaya', 'kya baat hai', 'dil khush ho gaya',
    'bahut sundar', 'bahut badiya', 'ek dum mast', 'superb hai',
}

KANGLISH_POSITIVE = {
    'sakkath', 'channagide', 'tumba channagide', 'superagide', 'bhale',
    'hodagide', 'adbhuta', 'nanna preethina', 'tumba ishta',
    'tumba chenna', 'manassu tumba khushi aythu',
}

DEVANAGARI_POSITIVE = {
    'अच्छा', 'बढ़िया', 'शानदार', 'लाजवाब', 'जबरदस्त',
    'धन्यवाद', 'बहुत अच्छा', 'सुंदर', 'प्यारा', 'सुंदर',
}

KANNADA_POSITIVE = {
    'ಚೆನ್ನಾಗಿದೆ', 'ಸೂಪರ್', 'ಅದ್ಭುತ', 'ತುಂಬಾ ಚೆನ್ನ', 'ಭಲೆ',
    'ತುಂಬಾ ಖುಷಿ', 'ಸಕ್ಕತ್ ಇದೆ',
}

EN_HUMOR_INDICATORS = {
    'haha', 'lol', 'lmao', 'funny', 'hilarious', 'joke', 'laugh',
    'comedy', 'humor', 'witty', 'clever', 'amusing', 'rofl',
    'giggle', 'hehe', 'xd', '😂', '🤣', '😄', '😆',
}

# =============================================================================
# SECTION 3 — DEVANAGARI & KANNADA SCRIPT WORD BANKS
# =============================================================================

DEVANAGARI_BAD_WORDS = {
    # Harassment / insults
    'बेवकूफ', 'मूर्ख', 'बकवास', 'गधा', 'कमीना', 'हरामी',
    'निकम्मा', 'घटिया', 'बेकार', 'पागल', 'उल्लू', 'बेशर्म',
    'भिखारी', 'चोर', 'कुत्ता', 'सुअर', 'नालायक', 'कचरा',
    'बेकार', 'नकारा', 'डरपोक', 'गंदा', 'कायर', 'झूठा',
    # Threats
    'मार डालूंगा', 'तुझे देखूंगा', 'पछताएगा', 'जान से मारूंगा',
    # Discrimination
    'नीची जात', 'तुम्हारी जाति', 'तुम्हारा धर्म', 'तुम्हारे लोग',
    # Hate
    'यहाँ से चले जाओ', 'तुम्हें यहाँ नहीं रहना चाहिए',
}

KANNADA_BAD_WORDS = {
    # Insults
    'ಮೂರ್ಖ', 'ಹುಚ್ಚ', 'ನಾಯಿ', 'ಕಳ್ಳ', 'ಬದ್ಮಾಶ',
    'ದಡ್ಡ', 'ಬೇವರ್ಸಿ', 'ಸೋಮಾರಿ', 'ಕಡಿಮೆ', 'ಹೆದರುಪುಕ್ಕ',
    'ಸುಳ್ಳುಗಾರ', 'ನಾಚಿಕೆಗೇಡಿ', 'ಹೊಲಸು', 'ಮಂಗ',
    # Threats
    'ನಿನ್ನ ನೋಡ್ಕೋತೀನಿ', 'ಬಿಡಲ್ಲ ನಿನ್ನ', 'ಪಶ್ಚಾತ್ತಾಪ ಪಡ್ತೀಯ',
    # Discrimination
    'ನಿಮ್ಮ ಜಾತಿ', 'ನಿಮ್ಮ ಧರ್ಮ', 'ನಿಮ್ಮ ಜನ', 'ಇಲ್ಲಿ ಜಾಗ ಇಲ್ಲ',
}

# =============================================================================
# SECTION 4 — LANGUAGE DETECTION
# =============================================================================

def detect_script(text: str) -> str:
    devanagari = sum(1 for ch in text if '\u0900' <= ch <= '\u097F')
    kannada    = sum(1 for ch in text if '\u0C80' <= ch <= '\u0CFF')
    latin      = sum(1 for ch in text if ch.isascii() and ch.isalpha())
    total = devanagari + kannada + latin or 1

    if devanagari / total > 0.35:
        return 'devanagari'
    if kannada / total > 0.35:
        return 'kannada'
    if (devanagari + kannada) / total > 0.12:
        return 'mixed_script'
    return 'latin'


# Expanded Hinglish grammar markers
HINGLISH_MARKERS = {
    'kya', 'hai', 'nahi', 'nahin', 'hain', 'bhi', 'toh', 'to', 'aur',
    'yaar', 'bhai', 'yeh', 'ye', 'woh', 'wo', 'accha', 'theek',
    'matlab', 'bilkul', 'zyada', 'thoda', 'iska', 'uska', 'mera',
    'tera', 'hum', 'tum', 'main', 'mujhe', 'tujhe', 'usse', 'inhe',
    'kuch', 'sab', 'bahut', 'ek', 'koi', 'nahi', 'tha', 'thi', 'the',
    'kar', 'karo', 'karta', 'karti', 'karte', 'raha', 'rahi', 'rahe',
    'ho', 'hoga', 'hogi', 'honge', 'hua', 'hui', 'hue', 'jao', 'ja',
    'bata', 'sun', 'dekh', 'lo', 'le', 'de', 'mat', 'na', 'hi',
}

# Expanded Kanglish grammar markers
KANGLISH_MARKERS = {
    'alli', 'idu', 'adhu', 'adhu', 'neen', 'neevu', 'avnu', 'avlu',
    'innu', 'illa', 'bekku', 'beku', 'beda', 'madko', 'hogona',
    'banni', 'heli', 'gottu', 'gothilla', 'agalla', 'agthilla',
    'channagide', 'sakkath', 'guru', 'yenu', 'yen', 'nin', 'nim',
    'nanna', 'nange', 'avarge', 'ivaru', 'avaru', 'illi', 'alli',
    'hogthini', 'bartini', 'madthini', 'madthira', 'hogthira',
    'bartira', 'irthira', 'ide', 'ive', 'hogi', 'baa', 'helu',
    'nodappa', 'kelappa', 'madappa', 'hogappa', 'tumba', 'thumba',
    'tumbha', 'yavaglu', 'yavagallu', 'modalige',
}


def detect_language(text: str) -> str:
    """Returns: english | hinglish | kanglish | devanagari | kannada | mixed_script"""
    script = detect_script(text)
    if script != 'latin':
        return script

    text_lower = text.lower()
    words = set(re.findall(r'\b[a-z]+\b', text_lower))

    hi_score = len(words & HINGLISH_MARKERS)
    kn_score = len(words & KANGLISH_MARKERS)

    # Lower threshold to 1 marker for better recall on short abusive messages
    if hi_score >= 1 and hi_score > kn_score:
        return 'hinglish'
    if kn_score >= 1 and kn_score >= hi_score:
        return 'kanglish'
    return 'english'


# =============================================================================
# SECTION 5 — MULTILINGUAL TOXIC WORD CHECK
# =============================================================================

def _word_match(text_lower: str, word_set: set) -> list:
    """Find any words from word_set present in text."""
    found = []
    words = set(re.findall(r'\b\w+\b', text_lower))
    for w in word_set:
        if ' ' in w:
            if w in text_lower:
                found.append(w)
        elif w in words:
            found.append(w)
    return found


def check_multilingual_toxicity(text: str) -> dict:
    lang = detect_language(text)
    text_lower = text.lower()

    result = {
        'detected_language': lang,
        'toxic_words_found': [],
        'is_multilingual_toxic': False,
        'category': None,
    }

    if lang == 'devanagari':
        hits = [w for w in DEVANAGARI_BAD_WORDS if w in text]
        result['toxic_words_found'] = hits
        result['is_multilingual_toxic'] = len(hits) > 0

    elif lang == 'kannada':
        hits = [w for w in KANNADA_BAD_WORDS if w in text]
        result['toxic_words_found'] = hits
        result['is_multilingual_toxic'] = len(hits) > 0

    elif lang == 'mixed_script':
        hits  = [w for w in DEVANAGARI_BAD_WORDS if w in text]
        hits += [w for w in KANNADA_BAD_WORDS if w in text]
        result['toxic_words_found'] = hits
        result['is_multilingual_toxic'] = len(hits) > 0

    elif lang == 'hinglish':
        hits = _word_match(text_lower, HINGLISH_PROFANITY)
        # Also check full phrases
        hits += [k for k in HARASSMENT_KEYWORDS | CYBERBULLYING_KEYWORDS
                 if k in text_lower and any(c > '\u0000' for c in k)]
        result['toxic_words_found'] = list(set(hits))
        result['is_multilingual_toxic'] = len(hits) > 0

    elif lang == 'kanglish':
        hits = _word_match(text_lower, KANGLISH_PROFANITY)
        hits += [k for k in HARASSMENT_KEYWORDS | CYBERBULLYING_KEYWORDS
                 if k in text_lower]
        result['toxic_words_found'] = list(set(hits))
        result['is_multilingual_toxic'] = len(hits) > 0

    else:  # english
        hits = _word_match(text_lower, EN_PROFANITY)
        result['toxic_words_found'] = hits
        result['is_multilingual_toxic'] = len(hits) > 0

    return result


# =============================================================================
# SECTION 6 — CATEGORY CLASSIFIER
# =============================================================================

def classify_toxic_category(text: str) -> dict:
    """
    Identify which of the 8 toxic categories this text falls into.
    Returns: category name + confidence + details
    """
    text_lower = text.lower()
    categories_hit = []

    def check_category(name, patterns, keywords):
        pattern_hit = any(re.search(p, text_lower) for p in patterns)
        keyword_hit = any(k in text_lower for k in keywords)
        if pattern_hit or keyword_hit:
            categories_hit.append({
                'category': name,
                'pattern_match': pattern_hit,
                'keyword_match': keyword_hit,
            })

    # Hostile dismissals — map to harassment (WARN tier)
    hostile_hit = any(re.search(p, text_lower) for p in HOSTILE_DISMISSAL_PATTERNS)
    if hostile_hit:
        categories_hit.append({'category': 'harassment', 'pattern_match': True, 'keyword_match': False})

    check_category('hate_speech',         HATE_SPEECH_PATTERNS,         HATE_SPEECH_KEYWORDS)
    check_category('harassment',          HARASSMENT_PATTERNS,          HARASSMENT_KEYWORDS)
    check_category('threat',              THREAT_PATTERNS,              THREAT_KEYWORDS)
    check_category('sexual_harassment',   SEXUAL_HARASSMENT_PATTERNS,   SEXUAL_HARASSMENT_KEYWORDS)
    check_category('cyberbullying',       CYBERBULLYING_PATTERNS,       CYBERBULLYING_KEYWORDS)
    check_category('discrimination',      DISCRIMINATION_PATTERNS,      DISCRIMINATION_KEYWORDS)
    combined_appearance_keywords = (
        APPEARANCE_MOCK_KEYWORDS_EN | APPEARANCE_MOCK_KEYWORDS_HINGLISH |
        APPEARANCE_MOCK_KEYWORDS_KANGLISH | APPEARANCE_MOCK_KEYWORDS_DEVANAGARI |
        APPEARANCE_MOCK_KEYWORDS_KANNADA
    )
    check_category('appearance_mocking',  APPEARANCE_MOCK_PATTERNS,     combined_appearance_keywords)

    # Profanity: word bank check
    lang = detect_language(text)
    if lang == 'hinglish':
        profanity_hits = _word_match(text_lower, HINGLISH_PROFANITY)
    elif lang == 'kanglish':
        profanity_hits = _word_match(text_lower, KANGLISH_PROFANITY)
    else:
        profanity_hits = _word_match(text_lower, EN_PROFANITY)

    if profanity_hits:
        categories_hit.append({
            'category': 'profanity',
            'pattern_match': False,
            'keyword_match': True,
            'words': profanity_hits[:5],
        })

    # Toxic sarcasm: pattern check
    sarcasm_hits = sum(1 for p in SARCASM_PATTERNS if re.search(p, text_lower))
    if sarcasm_hits >= 1:
        categories_hit.append({
            'category': 'toxic_sarcasm',
            'pattern_match': True,
            'keyword_match': False,
            'score': sarcasm_hits,
        })

    return {
        'categories': categories_hit,
        'primary_category': categories_hit[0]['category'] if categories_hit else None,
        'is_toxic': len(categories_hit) > 0,
    }


# =============================================================================
# SECTION 7 — SARCASM ANALYZER
# =============================================================================

def detect_sarcasm(text: str) -> dict:
    text_lower = text.lower()
    score = 0.0

    pattern_hits = sum(1 for p in SARCASM_PATTERNS if re.search(p, text_lower))
    score += pattern_hits * 0.35

    # Contradiction: positive surface + negative body
    pos = sum(1 for w in EN_POSITIVE_WORDS if w in text_lower)
    neg_en = _word_match(text_lower, EN_PROFANITY)
    neg_hi = _word_match(text_lower, HINGLISH_PROFANITY)
    neg_kn = _word_match(text_lower, KANGLISH_PROFANITY)
    neg = len(neg_en) + len(neg_hi) + len(neg_kn)
    if pos > 0 and neg > 0:
        score += 0.4

    # Irony markers
    if re.search(r'[!]{3,}', text):
        score += 0.15
    if re.search(r'[.]{3,}', text):
        score += 0.1
    if '/s' in text_lower:
        score += 0.5

    is_sarcastic = score >= 0.3

    # Toxic escalation: sarcasm + actual harm words
    escalator_hit = any(w in text_lower.split() for w in TOXIC_ESCALATORS)
    is_toxic_sarcasm = is_sarcastic and escalator_hit

    return {
        'is_sarcastic': is_sarcastic,
        'is_toxic_sarcasm': is_toxic_sarcasm,
        'sarcasm_score': round(min(score, 1.0), 3),
    }


# =============================================================================
# SECTION 8 — SPAM DETECTION
# =============================================================================

SPAM_KEYWORDS = [
    'click here', 'buy now', 'free money', 'you are a winner',
    'congratulations you have won', 'limited time offer', 'act now',
    'call now', 'earn money fast', 'make money online',
    'work from home', 'exclusive deal', 'discount offer',
    'casino', 'gambling', 'bet now', 'lottery',
]

def check_spam(text: str) -> bool:
    text_lower = text.lower()
    url_count = len(re.findall(r'https?://|www\.|\.com|\.net|\.org', text_lower))
    if url_count >= 2:
        return True

    spam_hits = sum(1 for s in SPAM_KEYWORDS if s in text_lower)
    if spam_hits >= 2:
        return True

    # Repetition
    words = text_lower.split()
    if len(words) > 3:
        freq = {}
        for w in words:
            freq[w] = freq.get(w, 0) + 1
        if max(freq.values()) / len(words) > 0.5:
            return True

    return False


# =============================================================================
# SECTION 9 — SENTIMENT
# =============================================================================

def analyze_sentiment(text: str) -> dict:
    text_lower = text.lower()
    words = re.findall(r'\b\w+\b', text_lower)

    pos = sum(1 for w in words if w in EN_POSITIVE_WORDS)
    # also check hinglish/kanglish positive phrases
    for phrase in HINGLISH_POSITIVE | KANGLISH_POSITIVE:
        if phrase in text_lower:
            pos += 1

    neg = sum(1 for w in words if w in EN_PROFANITY or
              w in HINGLISH_PROFANITY or w in KANGLISH_PROFANITY)

    total = pos + neg or 1
    polarity = (pos - neg) / total

    if polarity > 0.1:
        sentiment = 'positive'
    elif polarity < -0.1:
        sentiment = 'negative'
    else:
        sentiment = 'neutral'

    return {
        'sentiment': sentiment,
        'polarity': round(polarity, 3),
        'positive_word_count': pos,
        'negative_word_count': neg,
    }


# =============================================================================
# SECTION 10 — ML MODEL  (TF-IDF + Logistic Regression)
# =============================================================================

# Comprehensive training data across all 8 categories and all 4 languages
TRAINING_DATA = [
    # ─── ENGLISH CLEAN ────────────────────────────────────────────────────────
    ("This photo is absolutely stunning, great work!", 1),
    ("Love this content, keep it up!", 1),
    ("So beautiful and inspiring!", 1),
    ("Fantastic effort, really well done.", 1),
    ("This made my day, thank you for sharing.", 1),
    ("Haha this is hilarious, love your humor!", 1),
    ("Perfect lighting and composition here.", 1),
    ("Incredible talent, you should be proud.", 1),
    ("Such a wholesome and lovely post.", 1),
    ("This is exactly what I needed today, thanks!", 1),
    ("Your creativity is truly outstanding.", 1),
    ("What a lovely and heartfelt caption.", 1),
    ("Brilliant work as always!", 1),
    ("You are so talented, never stop creating.", 1),
    ("This is so cute and adorable!", 1),
    ("Amazing perspective, really thought-provoking.", 1),
    ("Keep up the great work, this is wonderful.", 1),
    ("So much positivity in this post, love it.", 1),

    # ─── HATE SPEECH ──────────────────────────────────────────────────────────
    ("People like you don't belong here.", 0),
    ("Your kind always causes problems.", 0),
    ("Go back to where you came from.", 0),
    ("You people are the worst.", 0),
    ("Your kind will never fit in here.", 0),
    ("Those people are ruining everything.", 0),
    ("You don't deserve to be here with us.", 0),
    ("People like you shouldn't exist.", 0),
    ("Your religion is a disease.", 0),
    ("Your race has no place here.", 0),
    ("Their kind always fails at everything.", 0),
    ("You lot don't belong in this country.", 0),

    # ─── HARASSMENT ───────────────────────────────────────────────────────────
    ("You are completely useless at everything you do.", 0),
    ("Nobody likes you and nobody ever will.", 0),
    ("You will never succeed at anything in life.", 0),
    ("You're an absolute waste of space.", 0),
    ("You're a complete embarrassment to everyone.", 0),
    ("You are beyond pathetic and hopeless.", 0),
    ("You are the worst person I've ever seen.", 0),
    ("Everyone can see how much of a failure you are.", 0),
    ("You should just quit and disappear.", 0),
    ("You are a burden to everyone around you.", 0),
    ("Nobody wants you here, you're worthless.", 0),
    ("You're too stupid to understand anything.", 0),
    ("You're a total loser with no future.", 0),
    ("You're an idiot and everyone knows it.", 0),
    ("Just give up, you're hopeless.", 0),

    # ─── THREATS ──────────────────────────────────────────────────────────────
    ("You'll regret this, I promise you.", 0),
    ("Watch your back, I'm coming for you.", 0),
    ("You won't get away with this.", 0),
    ("I'll find you and make you pay.", 0),
    ("You're going to pay for what you did.", 0),
    ("Better be careful, I know where you live.", 0),
    ("I'm going to destroy everything you have.", 0),
    ("You'll suffer for this, mark my words.", 0),
    ("Nobody can save you from what's coming.", 0),
    ("I'll make sure you lose everything.", 0),
    ("Your days are numbered.", 0),
    ("I'll ruin your life for this.", 0),

    # ─── SEXUAL HARASSMENT ────────────────────────────────────────────────────
    ("Stop sending me those inappropriate messages.", 0),
    ("Send me your photos, you look so hot.", 0),
    ("You're so sexy, I can't stop thinking about you.", 0),
    ("I know you want it, stop pretending.", 0),
    ("You should send me more private pictures.", 0),
    ("You're so fuckable, come on.", 0),
    ("Stop sending sexual messages, it's harassment.", 0),
    ("Your body is amazing, send me more.", 0),
    ("I want to sleep with you, just say yes.", 0),

    # ─── PROFANITY ────────────────────────────────────────────────────────────
    ("What absolute bullshit, this is crap.", 0),
    ("This is complete garbage and you know it.", 0),
    ("What the hell is wrong with you.", 0),
    ("You're a damn idiot and everyone sees it.", 0),
    ("This stupid nonsense is driving me crazy.", 0),
    ("What a piece of trash this whole thing is.", 0),
    ("You're such an asshole, I hate you.", 0),
    ("This is awful and disgusting.", 0),
    ("What a dumbass move that was.", 0),
    ("You're a scumbag and a lowlife.", 0),
    ("Go to hell you miserable jerk.", 0),
    ("This is the worst piece of shit I've seen.", 0),

    # ─── CYBERBULLYING ────────────────────────────────────────────────────────
    ("Everyone knows you're a joke, just stop trying.", 0),
    ("You'll always be a failure no matter what you do.", 0),
    ("Nobody will ever take you seriously.", 0),
    ("We all laugh at you behind your back.", 0),
    ("You've always been the weird one nobody likes.", 0),
    ("You'll never change, always the same loser.", 0),
    ("Everyone agrees you're pathetic and cringe.", 0),
    ("You've been a failure your whole life.", 0),
    ("Nobody wants to be associated with you.", 0),
    ("You're the kind of person everyone avoids.", 0),
    ("Stop embarrassing yourself in public.", 0),
    ("You're such a crybaby and an attention seeker.", 0),

    # ─── TOXIC SARCASM ────────────────────────────────────────────────────────
    ("Oh great, just what I needed, genius move.", 0),
    ("Wow, so impressive... not really.", 0),
    ("Yeah right, totally the best decision ever.", 0),
    ("Sure, because that's such a brilliant idea.", 0),
    ("Oh wow what a genius! /s", 0),
    ("Super helpful as always... not.", 0),
    ("Oh fantastic choice, very smart indeed.", 0),
    ("Wow genius move there buddy!!!", 0),
    ("Obviously that totally makes sense... not.", 0),
    ("Sure jan, if you say so lol.", 0),
    ("Great job, keep embarrassing yourself!!!", 0),

    # ─── DISCRIMINATION ───────────────────────────────────────────────────────
    ("Your kind always fails at this, typical.", 0),
    ("That's expected from people like you.", 0),
    ("Your community is backward and always will be.", 0),
    ("Women can't handle this kind of work.", 0),
    ("Your religion makes you incapable of logic.", 0),
    ("Your people have always been inferior.", 0),
    ("That's so typical of your caste, honestly.", 0),
    ("You're only here because of your gender, not merit.", 0),
    ("People from your background never succeed.", 0),
    ("Your type has always been a problem in society.", 0),

    # ─── HINGLISH CLEAN ───────────────────────────────────────────────────────
    ("yaar bahut accha hai ye content, mast hai", 1),
    ("bhai zabardast kaam kiya, ekdum shandar", 1),
    ("wah kya baat hai, bahut sundar laga", 1),
    ("shukriya itna accha share kiya bhai", 1),
    ("ekdum mast photo hai yaar, badiya hai", 1),
    ("bahut inspiring hai ye, dil khush ho gaya", 1),
    ("kya khoob likha hai yaar, bahut pasand aaya", 1),

    # ─── HINGLISH TOXIC ───────────────────────────────────────────────────────
    ("tu bilkul bevakoof hai, kuch nahi aata tujhe", 0),
    ("koi tujhe pasand nahi karta, nikal yahan se", 0),
    ("tu ek kamina aur harami insaan hai", 0),
    ("tu hamesha fail hoga, nikamma hai tu", 0),
    ("sab tujhpe hasate hain, tu ek joke hai", 0),
    ("tu bilkul bekaar aur faltu hai", 0),
    ("yeh bakwaas band karo, besharam ho tum", 0),
    ("tujhe dekh lunga, pachtaega tu", 0),
    ("teri maa ko bata dunga tera kaam", 0),
    ("tu harami hai, chup ho ja", 0),
    ("kya ganda aadmi hai tu, ghatiya", 0),
    ("sab jaante hain tu ek bhadwa hai", 0),
    ("apni photo bhejo, tum bahut sexy ho", 0),
    ("tumhari jaat hi aisi hai, hamesha haarte hain", 0),
    ("tum log yahan nahi chahiye, nikal jao", 0),
    ("bevakoof kahin ka, bakwaas mat kar", 0),
    ("gadha hai tu, dimag nahi hai kya", 0),
    ("kutte ki tarah hai tera kaam", 0),
    ("tu ek burden hai sab ke liye", 0),
    ("nalayak hai tu, kuch nahi kar sakta", 0),

    # ─── KANGLISH CLEAN ───────────────────────────────────────────────────────
    ("sakkath ide guru, tumba channagide", 1),
    ("bhale madidira, superagide", 1),
    ("tumba ishta aythu nodi, channagide", 1),
    ("manassu tumba khushi aythu nodidhu", 1),
    ("neevu tumba chenna maadidira, thanks", 1),
    ("adbhuta kanna, keep it up guru", 1),
    ("hodagide banni, tumba mast ide", 1),

    # ─── KANGLISH TOXIC ───────────────────────────────────────────────────────
    ("naayi maga neevu, bekilla idu", 0),
    ("huchcha maga, sullu mathadthira", 0),
    ("neevu yenu madolla, useless agidira", 0),
    ("bevarse ide nimdu, bidu bidi", 0),
    ("ella jana nimage nakkathare, neevu joke", 0),
    ("neevu yavaglu fail agthira, nikamma", 0),
    ("sule maga, thika tika idu", 0),
    ("nim amna, sala neevu", 0),
    ("nimage yaaru ishtapadalla", 0),
    ("kerige hogi neevu, bekilla illi", 0),
    ("neevu yenu agolla, daDDa neevu", 0),
    ("mundey neevu, hogi bidi", 0),
    ("hole maga idu, thika madidira", 0),
    ("neevu burden agidira, hogi bidi", 0),
    ("ninge illi jagilla, hogi", 0),
    ("nimma jaathi iddange, yavaglu heege", 0),
    ("bevarse maga, kalla neevu", 0),
    ("photo kalisu, neevu tumba sexy agidira", 0),
    ("nimage thoorbeke, nim kade barteeni", 0),
    ("peda neevu, thika maadidira nimdu", 0),
]


def build_training_arrays():
    texts  = [t for t, _ in TRAINING_DATA]
    labels = [l for _, l in TRAINING_DATA]
    return texts, labels


# =============================================================================
# SECTION 11 — MAIN COMMENT FILTER CLASS
# =============================================================================

class CommentFilter:
    VERDICT_ALLOW = 'allow'
    VERDICT_WARN  = 'warn'
    VERDICT_BLOCK = 'block'

    # Hard-block categories — no user override
    HARD_BLOCK_CATEGORIES = {
        'hate_speech', 'threat', 'sexual_harassment', 'discrimination',
        'appearance_mocking'
    }
    # Warn categories — user may force-post
    WARN_CATEGORIES = {
        'cyberbullying', 'harassment', 'profanity', 'toxic_sarcasm'
    }
    # Single-word toxic triggers that always hard-block regardless of ML score
    SINGLE_WORD_HARD_BLOCK = {
        'idiot', 'moron', 'stupid', 'loser', 'worthless', 'pathetic',
        'garbage', 'trash', 'hate', 'kill', 'die', 'useless', 'scum',
        'bastard', 'bitch', 'shit', 'fuck', 'ass', 'crap', 'damn',
        'shut up', 'get lost', 'go away', 'piss off', 'rubbish',
        'what rubbish', 'you suck', 'this sucks', 'i hate you',
        'chup kar', 'chup ho', 'nikal ja', 'bhag ja',
        'kya bakwaas', 'ye bakwaas', 'bakwas', 'ghanta', 'naayi', 'bevarsi','anista','tu','munde','mundede','gandu',
    }

    def __init__(self):
        self.load_or_train_model()

    # ------------------------------------------------------------------
    def load_or_train_model(self):
        try:
            self.vectorizer = joblib.load('comment_vectorizer.pkl')
            self.classifier = joblib.load('comment_classifier.pkl')
        except Exception:
            self._train()

    def _train(self):
        texts, labels = build_training_arrays()
        self.vectorizer = TfidfVectorizer(
            max_features=3000,
            ngram_range=(1, 3),   # unigrams, bigrams, trigrams
            analyzer='word',
            sublinear_tf=True,
            min_df=1,
        )
        X = self.vectorizer.fit_transform(texts)
        self.classifier = LogisticRegression(
            C=3.0,
            max_iter=1000,
            class_weight='balanced',
            solver='lbfgs',
        )
        self.classifier.fit(X, labels)
        try:
            joblib.dump(self.vectorizer, 'comment_vectorizer.pkl')
            joblib.dump(self.classifier, 'comment_classifier.pkl')
        except Exception:
            pass

    # ------------------------------------------------------------------
    def _ml_score(self, text: str) -> dict:
        try:
            vec   = self.vectorizer.transform([text])
            proba = self.classifier.predict_proba(vec)[0]
            # proba[0] = bad, proba[1] = good
            return {
                'toxicity_score': round(float(proba[0]), 3),
                'is_toxic': float(proba[0]) > 0.55,
                'confidence': round(float(max(proba)), 3),
            }
        except Exception:
            return {'toxicity_score': 0.0, 'is_toxic': False, 'confidence': 0.5}

    # ------------------------------------------------------------------
    def analyze_comment(self, comment_text: str) -> dict:
        if not comment_text or not comment_text.strip():
            return {
                'should_display': False,
                'is_hard_block': True,
                'verdict': self.VERDICT_BLOCK,
                'reasons': ['Empty comment'],
                'analysis': {},
            }

        # Run all detectors
        lang_analysis  = check_multilingual_toxicity(comment_text)
        category_result= classify_toxic_category(comment_text)
        sarcasm        = detect_sarcasm(comment_text)
        ml             = self._ml_score(comment_text)
        sentiment      = analyze_sentiment(comment_text)
        spam           = check_spam(comment_text)
        humorous       = any(h in comment_text.lower() for h in EN_HUMOR_INDICATORS)

        reasons  = []
        hard_block = False
        warn       = False

        # ── HARD BLOCK logic ──────────────────────────────────────────
        # 1. Hard-block categories from rule engine
        for cat in category_result['categories']:
            if cat['category'] in self.HARD_BLOCK_CATEGORIES:
                hard_block = True
                label = cat['category'].replace('_', ' ').title()
                reasons.append(f"Detected: {label}")

        # 2. Multilingual toxic words (script-based or romanized)
        if lang_analysis['is_multilingual_toxic']:
            hard_block = True
            lang  = lang_analysis['detected_language'].upper()
            words = ', '.join(lang_analysis['toxic_words_found'][:4])
            reasons.append(f"Toxic language ({lang}): {words}")

        # 3. Toxic sarcasm (sarcasm + escalator words)
        if sarcasm['is_toxic_sarcasm']:
            hard_block = True
            reasons.append("Toxic sarcasm with harmful intent")

        # 4. Single-word / short phrase hard block (common standalone insults)
        text_lower_check = comment_text.lower().strip()
        for phrase in self.SINGLE_WORD_HARD_BLOCK:
            if phrase == text_lower_check or re.search(r'\b' + re.escape(phrase) + r'\b', text_lower_check):
                hard_block = True
                reasons.append(f'Toxic content detected: "{phrase}"')
                break

        # 5. Very high ML confidence
        if ml['toxicity_score'] >= 0.82:
            hard_block = True
            reasons.append(f"High-confidence toxicity (ML: {ml['toxicity_score']:.2f})")

        if hard_block:
            return self._result(
                False, True, self.VERDICT_BLOCK, reasons,
                sentiment, lang_analysis, category_result,
                sarcasm, ml, spam, humorous, comment_text
            )

        # ── Native script positive override (ML not trained on Devanagari/Kannada) ──
        lang = lang_analysis['detected_language']
        if lang in ('devanagari', 'kannada', 'mixed_script') and not lang_analysis['is_multilingual_toxic']:
            # Check for positive words in native script
            pos_words_d = any(w in comment_text for w in DEVANAGARI_POSITIVE)
            pos_words_k = any(w in comment_text for w in KANNADA_POSITIVE)
            if pos_words_d or pos_words_k:
                reasons.append(f"Positive content ({lang.title()} script)")
                return self._result(
                    True, False, self.VERDICT_ALLOW, reasons,
                    sentiment, lang_analysis, category_result,
                    sarcasm, ml, spam, humorous, comment_text
                )

        # ── WARN logic ────────────────────────────────────────────────
        for cat in category_result['categories']:
            if cat['category'] in self.WARN_CATEGORIES:
                warn = True
                label = cat['category'].replace('_', ' ').title()
                reasons.append(f"Flagged: {label}")

        if spam:
            warn = True
            reasons.append("Possible spam")

        if sarcasm['is_sarcastic'] and not sarcasm['is_toxic_sarcasm']:
            warn = True
            reasons.append(f"Sarcasm detected (score: {sarcasm['sarcasm_score']:.2f}) — benign")

        if ml['is_toxic'] and ml['toxicity_score'] < 0.82:
            warn = True
            reasons.append(f"Borderline content (ML: {ml['toxicity_score']:.2f})")

        if warn:
            return self._result(
                False, False, self.VERDICT_WARN, reasons,
                sentiment, lang_analysis, category_result,
                sarcasm, ml, spam, humorous, comment_text
            )

        # ── ALLOW ─────────────────────────────────────────────────────
        if humorous:
            reasons.append("Humor detected 😄")
        if sentiment['sentiment'] == 'positive':
            reasons.append("Positive sentiment")
        lang = lang_analysis['detected_language']
        if lang != 'english':
            reasons.append(f"Language: {lang.title()}")

        return self._result(
            True, False, self.VERDICT_ALLOW, reasons or ['Clean comment'],
            sentiment, lang_analysis, category_result,
            sarcasm, ml, spam, humorous, comment_text
        )

    def _result(
        self, should_display, is_hard_block, verdict, reasons,
        sentiment, lang_analysis, category_result,
        sarcasm, ml, spam, humorous, text
    ) -> dict:
        return {
            'should_display': should_display,
            'is_hard_block': is_hard_block,
            'verdict': verdict,
            'reasons': reasons,
            'analysis': {
                'sentiment': sentiment,
                'language': lang_analysis,
                'categories': category_result,
                'sarcasm': sarcasm,
                'toxicity': ml,
                'is_spam': spam,
                'is_humorous': humorous,
                'text_length': len(text),
                'word_count': len(text.split()),
            },
        }

    def filter_comments(self, comments_list: list) -> list:
        filtered = []
        for comment in comments_list:
            result = self.analyze_comment(comment.get('content', ''))
            if result['should_display']:
                comment['ai_analysis'] = result['analysis']
                comment['ai_verdict']  = result['verdict']
                comment['ai_reasons']  = result['reasons']
                filtered.append(comment)
        return filtered


# =============================================================================
# MODULE-LEVEL API (drop-in compatible with existing app.py)
# =============================================================================

comment_filter = CommentFilter()

def analyze_comment_text(text: str) -> dict:
    return comment_filter.analyze_comment(text)

def filter_comment_list(comments: list) -> list:
    return comment_filter.filter_comments(comments)