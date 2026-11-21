import streamlit as st
from google import genai
from google.genai import types
from PIL import Image
import io
import sqlite3
import datetime

# ==========================================
# ១. ការកំណត់ Database រក្សាទុកប្រវត្តិ
# ==========================================
def init_db():
    conn = sqlite3.connect("vet_clinic.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS medical_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            animal_type TEXT,
            symptoms TEXT,
            diagnosis TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS plant_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            plant_type TEXT,
            symptoms TEXT,
            diagnosis TEXT
        )
    ''')
    conn.commit()
    conn.close()


def save_history(type_name, symptoms, diagnosis, category):
    conn = sqlite3.connect("vet_clinic.db")
    c = conn.cursor()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if category == "animal":
        c.execute(
            "INSERT INTO medical_history (date, animal_type, symptoms, diagnosis) VALUES (?, ?, ?, ?)",
            (now, type_name, symptoms, diagnosis)
        )
    else:
        c.execute(
            "INSERT INTO plant_history (date, plant_type, symptoms, diagnosis) VALUES (?, ?, ?, ?)",
            (now, type_name, symptoms, diagnosis)
        )
    conn.commit()
    conn.close()


init_db()

# ==========================================
# ២. ការគ្រប់គ្រងទំហំរូបភាព (Image Optimization)
# ==========================================
def compress_image(uploaded_file):
    img = Image.open(uploaded_file)
    if img.mode != "RGB":
        img = img.convert("RGB")

    img.thumbnail((1024, 1024))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=80)
    buf.seek(0)
    return Image.open(buf)


# ==========================================
# ៣. ការរៀបចំទំព័រ UI ឱ្យមានស្តង់ដារ (UI/UX)
# ==========================================
st.set_page_config(page_title="ប្រព័ន្ធវិភាគ ដើមកសិកម្ម AI", page_icon="🌱", layout="centered")

# រក្សាទុកលទ្ធផលក្នុង Session State កុំឱ្យបាត់ពេលចុច Download ឬ Copy
if "last_result" not in st.session_state:
    st.session_state["last_result"] = ""
if "last_meta" not in st.session_state:
    st.session_state["last_meta"] = {}

st.markdown("""
    <style>
        .main { background-color: #f9fbfd; }
        .stButton>button {
            border-radius: 8px;
            font-weight: bold;
            font-size: 16px;
            padding: 10px 24px;
            transition: all 0.3s ease-in-out;
        }
        .stButton>button:hover {
            transform: scale(1.02);
        }
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        h1, h2, h3 { color: #1e3a5f; }
    </style>
""", unsafe_allow_html=True)

st.title("🌱 ប្រព័ន្ធវិភាគ ដើមកសិកម្ម AI")
st.markdown(
    "<p style='font-size: 16px; color: #555;'>ប្រព័ន្ធប្រើប្រាស់បញ្ញាសិប្បនិម្មិត (AI) ដើម្បីវិភាគ និងចេញសេចក្តីណែនាំព្យាបាលសត្វ និងដំណាំ។</p>",
    unsafe_allow_html=True
)
st.divider()

# ទាញយក API Key ដោយសុវត្ថិភាព (មិន Error ទោះគ្មាន secrets.toml លើម៉ាស៊ីនក៏ដោយ)
try:
    api_key = st.secrets.get("GEMINI_API_KEY")
except Exception:
    api_key = None

# ==========================================
# ៤. របារចំហៀង (Sidebar) ស្អាតបាត
# ==========================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/1892/1892751.png", width=100)
    st.header("⚙ ការកំណត់ប្រព័ន្ធ")
    if not api_key:
        api_key = st.text_input("បញ្ចូល Google Gemini API Key៖", type="password")
        st.caption("សូមកំណត់ GEMINI_API_KEY នៅក្នុង Streamlit Secrets ដើម្បីលាក់ប្រអប់នេះ។")
    else:
        st.success("✅ ប្រព័ន្ធបានភ្ជាប់ API រួចរាល់")

    st.divider()
    st.header("📂 ជ្រើសរើសផ្នែកវិភាគ")
    app_mode = st.radio("សូមជ្រើសរើសជំនាញ៖", ["🩺 ផ្នែកពេទ្យសត្វ", "🌿 ផ្នែកដំណាំកសិកម្ម"])

    st.divider()
    st.markdown("### 📊 ប្រវត្តិវិភាគថ្មីៗ")
    try:
        conn = sqlite3.connect("vet_clinic.db")
        c = conn.cursor()
        if app_mode == "🩺 ផ្នែកពេទ្យសត្វ":
            c.execute("SELECT date, animal_type FROM medical_history ORDER BY id DESC LIMIT 5")
        else:
            c.execute("SELECT date, plant_type FROM plant_history ORDER BY id DESC LIMIT 5")

        history = c.fetchall()
        if history:
            for row in history:
                st.caption(f"🕒 {row[0]} - **{row[1]}**")
        else:
            st.caption("មិនទាន់មានប្រវត្តិទេ")
        conn.close()
    except Exception:
        st.caption("មិនទាន់មានប្រវត្តិទេ")

# ==========================================
# ៥. អនុគមន៍ហៅ AI (បញ្ចូលក្បួនផ្សំថ្នាំលម្អិតតាមក្រុម)
# ==========================================
def analyze_with_ai(target_type, extra_info, symptoms, images, key, mode):
    client = genai.Client(api_key=key)

    if mode == "animal":
        prompt = f"""អ្នកគឺជាវេជ្ជបណ្ឌិតពេទ្យសត្វជំនាញកម្រិតស្តង់ដារអន្តរជាតិ ប្រចាំហាង «ដើមកសិកម្ម»។
សូមធ្វើការវិភាគករណីខាងក្រោមជាភាសាខ្មែរឱ្យលម្អិត ច្បាស់លាស់ និងងាយស្រួលអនុវត្ត៖
- ប្រភេទសត្វ៖ {target_type}
- ទម្ងន់ / អាយុ / ស្ថានភាពសត្វ៖ {extra_info or 'មិនបានបញ្ជាក់'}
- រោគសញ្ញា៖ {symptoms or 'សូមពិនិត្យតាមរូបភាពដែលបានភ្ជាប់'}

ច្បាប់មាសឱសថសាស្ត្រពេទ្យសត្វដែលត្រូវគោរពដាច់ខាតក្នុងការផ្សំថ្នាំ៖
1. ចំណាត់ថ្នាក់ក្រុមថ្នាំផ្សះ៖
   - **ក្រុម A (សម្លាប់បាក់តេរី / Bactericidal)៖** Beta-lactams (Penicillins: Amoxicillin, Ampicillin; Cephalosporins: Ceftiofur, Cefquinome), Aminoglycosides (Gentamicin, Streptomycin, Neomycin), Polymyxins (Colistin), Fluoroquinolones (Enrofloxacin, Marbofloxacin), Sulfonamides + Trimethoprim។
   - **ក្រុម B (បង្អាក់ការលូតលាស់បាក់តេរី / Bacteriostatic)៖** Tetracyclines (Oxytetracycline, Doxycycline), Amphenicols (Florfenicol), Macrolides (Tylosin, Tilmicosin, Erythromycin), Lincosamides (Lincomycin), Pleuromutilins (Tiamulin)។
2. ក្បួនផ្សំថ្នាំផ្សះ៖
   - ✅ **ក្រុម A + ក្រុម A (បង្កើនប្រសិទ្ធភាពទ្វេដង / Synergism)៖** ឧ. Beta-lactam (Amoxicillin/Ceftiofur) + Aminoglycoside (Gentamicin/Colistin) ឬ Beta-lactam + Fluoroquinolone (Enrofloxacin)។
   - ✅ **ក្រុម B + ក្រុម B (ជួយបំពេញបន្ថែមគ្នា / Additive)៖** ឧ. Tetracycline (Doxycycline) + Macrolide (Tylosin) ឬ Florfenicol + Doxycycline ឬ Lincomycin + Spectinomycin។ (ចំណាំ៖ ជៀសវាងផ្សំ Macrolides + Lincosamides + Florfenicol ចូលគ្នា ព្រោះដណ្តើមទីតាំងភ្ជាប់ 50S តែមួយ)។
   - ❌ **ហាមដាច់ខាត ក្រុម A + ក្រុម B (ប្រឆាំងគ្នា / Antagonism)៖** ឧ. ហាមផ្សំ Amoxicillin/Ceftiofur ជាមួយ Oxytetracycline/Doxycycline/Florfenicol/Tylosin ព្រោះធ្វើឱ្យថ្នាំសាប និងបាក់តេរីស៊ាំថ្នាំ។
3. ក្បួនថ្នាំរលាក និងថ្នាំជំនួយ៖
   - ❌ ហាមផ្សំ **NSAIDs** (Flunixin, Meloxicam, Ketoprofen, Analgin) ជាមួយ **Corticosteroids** (Dexamethasone) ព្រមគ្នាដាច់ខាត។
   - ❌ ហាមប្រើ Dexamethasone លើសត្វផើម (ធ្វើឱ្យរលូតកូន) ឬជំងឺវីរុសធ្ងន់ធ្ងរ។
   - ❌ **ច្បាប់សឺរ៉ាំង៖** ហាមបូមថ្នាំផ្សះ ២ មុខ ឬថ្នាំផ្សះលាយជាមួយថ្នាំរលាក/កាល់ស្យូម/វីតាមីន ចូលក្នុង**សឺរ៉ាំងតែមួយ**ដាច់ខាត ត្រូវចាក់ផ្សេងសឺរ៉ាំង និងផ្សេងកន្លែង (ឧ. ក-ឆ្វេង និង ក-ស្តាំ)។

សូមឆ្លើយតបតាមទម្រង់ ៥ ចំណុចខាងក្រោម៖

### ១. ឈ្មោះជំងឺសង្ស័យ (ជាភាសាខ្មែរ និងឈ្មោះបច្ចេកទេសអង់គ្លេស)
### ២. ការវិភាគរូបភាព និងរោគសញ្ញា
### ៣. មូលហេតុបង្កជំងឺ (បាក់តេរី / វីរុស / ប៉ារ៉ាស៊ីត / ផ្សិត / កង្វះសារធាតុចិញ្ចឹម)
### ៤. 💊 វិធីព្យាបាល និងក្បួនផ្សំថ្នាំលម្អិត (គោរពតាមក្បួនក្រុមថ្នាំ)
ត្រូវបង្ហាញឱ្យបានគ្រប់ ៤ ផ្នែករងខាងក្រោម៖
- **ក. ក្បួនផ្សំថ្នាំប្រចាំករណីនេះ (ក្រុមណា + ក្រុមណា)៖**
  - បញ្ជាក់ឱ្យច្បាស់ថាជ្រើសរើស **រូបមន្ត A + A** ឬ **រូបមន្ត B + B** ឬ **ថ្នាំទោល** + ថ្នាំបំបាត់ឈឺ/រលាកក្រុមណា + ថ្នាំជំនួយអ្វីខ្លះ និងពន្យល់មូលហេតុខ្លីៗថាហេតុអ្វីក្រុមទាំងនេះផ្សំគ្នាបានប្រសិទ្ធភាពខ្ពស់។
  - *(បើជាជំងឺវីរុស ត្រូវបញ្ជាក់ថាគ្មានថ្នាំសម្លាប់វីរុសផ្ទាល់ទេ តែប្រើក្បួនថ្នាំផ្សះដើម្បីទប់ស្កាត់បាក់តេរីជ្រៀតជ្រែក និងផ្តោតលើថ្នាំបញ្ចុះកម្ដៅ+វីតាមីន/អេឡិចត្រូលីត)*។
- **ខ. តារាងកាលវិភាគព្យាបាលលម្អិត៖**
| ឈ្មោះសារធាតុសកម្ម (Generic Name) | ក្រុមថ្នាំ (Class & Group A/B/ជំនួយ) | តួនាទីព្យាបាល | កម្រិតប្រើ (mg/kg ឬ ml/kg) | វិធីប្រើ (ចាក់/លាយទឹក) & ទីតាំង | រយៈពេលព្យាបាល |
| :--- | :--- | :--- | :--- | :--- | :--- |
| ... | ... | ... | ... | ... | ... |
- **គ. ជម្រើសក្បួនផ្សំទី ២ (សម្រាប់ករណីស៊ាំថ្នាំ ឬរកថ្នាំទី ១ មិនបាន)៖**
  - បញ្ជាក់ឈ្មោះថ្នាំ និងក្រុមថ្នាំដែលផ្សំគ្នាបាន (ឧ. ក្រុមណា + ក្រុមណា)។
- **ឃ. ⛔ ក្រុមថ្នាំហាមផ្សំ និងការប្រុងប្រយ័ត្នដាច់ខាត៖**
  - បញ្ជាក់ឱ្យច្បាស់ថា **ហាមយកថ្នាំក្នុងតារាងខាងលើទៅផ្សំជាមួយក្រុមណាខ្លះ** (ឧ. ហាមផ្សំក្រុម A ជាមួយ B ឈ្មោះអ្វីខ្លះ, ហាមលាយសឺរ៉ាំងតែមួយ, ការព្រមានលើសត្វផើម)។
  - បញ្ជាក់ **រយៈពេលឈប់ប្រើថ្នាំមុនលក់សាច់/ស៊ុត/ទឹកដោះ (Withdrawal Time)**។

### ៥. 🛡️ វិធានការការពារ និងការគ្រប់គ្រងទ្រុង
"""
    else:
        prompt = f"""អ្នកគឺជាអ្នកជំនាញក្សេត្រសាស្ត្រកម្រិតស្តង់ដារអន្តរជាតិ ប្រចាំហាង «ដើមកសិកម្ម»។
សូមធ្វើការវិភាគករណីដំណាំខាងក្រោមជាភាសាខ្មែរឱ្យលម្អិត និងងាយស្រួលអនុវត្ត៖
- ប្រភេទដំណាំ៖ {target_type}
- ដំណាក់កាលលូតលាស់ / ផ្ទៃដី៖ {extra_info or 'មិនបានបញ្ជាក់'}
- រោគសញ្ញា៖ {symptoms or 'សូមពិនិត្យតាមរូបភាពដែលបានភ្ជាប់'}

សូមឆ្លើយតបតាមទម្រង់ ៥ ចំណុចខាងក្រោម៖

### ១. ឈ្មោះជំងឺ / សត្វល្អិតចង្រៃ / បញ្ហាដំណាំ (ខ្មែរ និងអង់គ្លេស)
### ២. ការវិភាគរូបភាព និងរោគសញ្ញា
### ៣. មូលហេតុបង្ក (ផ្សិត / បាក់តេរី / វីរុស / សត្វល្អិត / កង្វះជីជាតិ)
### ៤. 🌿 វិធីសង្គ្រោះ និងក្បួនផ្សំថ្នាំកសិកម្មលម្អិត (Tank-Mix & Resistance Rules)
ត្រូវបង្ហាញឱ្យបានគ្រប់ ៤ ផ្នែករងខាងក្រោម៖
- **ក. ក្បួនផ្សំថ្នាំបាញ់ប្រចាំករណីនេះ (ក្រុមណា + ក្រុមណា)៖**
  - បញ្ជាក់ការផ្សំសារធាតុសកម្មដែលជួយបង្កើនប្រសិទ្ធភាពគ្នា (ឧ. ថ្នាំផ្សិតប្រភេទជ្រាបចូល Systemic + ថ្នាំប្រភេទប៉ះផ្ទាល់ Contact ឬ ថ្នាំសត្វល្អិតក្រុម IRAC ណា + ក្រុមណា) ដើម្បីការពារការស៊ាំថ្នាំ។
- **ខ. តារាងកម្រិតលាយថ្នាំ និងកាលវិភាគបាញ់៖**
| ឈ្មោះសារធាតុសកម្ម (Active Ingredient) | ក្រុមថ្នាំ (FRAC / IRAC) | តួនាទីកម្ចាត់/ជំនួយ | កម្រិតលាយ (ក្នុងទឹក ១៦–២០ លីត្រ) | ចន្លោះថ្ងៃបាញ់ |
| :--- | :--- | :--- | :--- | :--- |
| ... | ... | ... | ... | ... |
- **គ. លំដាប់លាយថ្នាំក្នុងធុងបាញ់ (W-A-L-E-S) និងការបង្វិលក្រុមថ្នាំ៖**
  - ណែនាំលំដាប់ចាក់ថ្នាំចូលទឹក (ម្សៅ WP/WDG -> ទឹកខាប់ SC -> ទឹកថ្លា SL/EC -> ជីបំប៉នស្លឹក -> ថ្នាំស្អិត) និងក្រុមថ្នាំសម្រាប់ប្តូរវេនបាញ់លើកក្រោយ។
- **ឃ. ⛔ ក្រុមថ្នាំហាមលាយចូលគ្នា និងរយៈពេលឈប់បាញ់មុនប្រមូលផល (PHI)៖**
  - បញ្ជាក់ក្រុមថ្នាំដែល**ហាមលាយចូលធុងតែមួយ** (ឧ. ហាមលាយថ្នាំទង់ដែង/ស្ពាន់ធ័រជាមួយថ្នាំគីមីប្រតិកម្មអាស៊ីត ឬហាមលាយថ្នាំផ្សិតគីមីជាមួយផ្សិតជីវសាស្ត្រ Trichoderma ឬកាល់ស្យូមលាយផូស្វ័រ)។
  - បញ្ជាក់ចំនួនថ្ងៃឈប់បាញ់មុនប្រមូលផល (PHI)។

### ៥. 🛡️ វិធានការការពារ និងការថែទាំដី/ចម្ការ
"""

    contents_list = [prompt]
    contents_list.extend(images)
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=contents_list,
        config=types.GenerateContentConfig(temperature=0.2)
    )
    return response.text


# ==========================================
# ៦. ផ្ទាំងបញ្ចូលទិន្នន័យ
# ==========================================
with st.container():
    if app_mode == "🩺 ផ្នែកពេទ្យសត្វ":
        st.subheader("១. បញ្ចូលព័ត៌មាន និងរោគសញ្ញាសត្វ")
        c1, c2 = st.columns(2)
        input_type = c1.text_input(
            "ប្រភេទសត្វ (ឧ. មាន់, គោ, ជ្រូក, ទា...) ៖",
            placeholder="វាយបញ្ចូលទីនេះ...",
            key="animal_input"
        )
        extra_info = c2.text_input(
            "ទម្ងន់ / អាយុ / ស្ថានភាព (ជាការស្រេចចិត្ត)៖",
            placeholder="ឧ. ជ្រូក ២៥kg, មេជ្រូកផើម, មាន់ ១.៥kg...",
            key="animal_extra"
        )
        symptoms_input = st.text_area(
            "រៀបរាប់ពីរោគសញ្ញា ឬអាការៈសត្វ៖",
            height=120,
            placeholder="ឧទាហរណ៍៖ សត្វអត់ស៊ីចំណី, ក្ដៅខ្លួន, ក្អកហត់, រាកស...",
            key="animal_symptoms"
        )
        btn_text = "🔍 ចាប់ផ្តើមវិភាគជំងឺ និងរៀបចំក្បួនផ្សំថ្នាំសត្វ"
        mode_flag = "animal"
    else:
        st.subheader("១. បញ្ចូលព័ត៌មាន និងរោគសញ្ញាដំណាំ")
        c1, c2 = st.columns(2)
        input_type = c1.text_input(
            "ប្រភេទដំណាំ (ឧ. ស្រូវ, ស្វាយ, ម្រេច, បន្លែ...) ៖",
            placeholder="វាយបញ្ចូលទីនេះ...",
            key="plant_input"
        )
        extra_info = c2.text_input(
            "ដំណាក់កាលដំណាំ (ជាការស្រេចចិត្ត)៖",
            placeholder="ឧ. កំពុងបែកគុម្ព, កំពុងចេញផ្កា, ជិតប្រមូលផល...",
            key="plant_extra"
        )
        symptoms_input = st.text_area(
            "រៀបរាប់ពីរោគសញ្ញា៖",
            height=120,
            placeholder="ឧទាហរណ៍៖ ស្លឹកឡើងលឿងប្រឆុះ, ជាំចុងស្លឹក, មានដង្កូវស៊ីស្លឹក...",
            key="plant_symptoms"
        )
        btn_text = "🔍 ចាប់ផ្តើមវិភាគជំងឺ និងរៀបចំក្បួនផ្សំថ្នាំដំណាំ"
        mode_flag = "plant"

# រៀបចំកន្លែងដាក់រូបភាពជា Tabs
st.write("---")
st.subheader("📸 ២. បញ្ចូលរូបភាព (ជាការស្រេចចិត្ត)")
tab1, tab2 = st.tabs(["📷 ថតរូបផ្ទាល់ពីកាមេរ៉ា", "📁 ជ្រើសរើសពីរូបថតដែលមានស្រាប់"])

with tab1:
    camera_photo = st.camera_input("ថតរូបភាពទីនេះ៖")
with tab2:
    uploaded_files = st.file_uploader(
        "ជ្រើសរើសរូបភាព (អាចរើសបានច្រើនសន្លឹក)៖",
        type=["png", "jpg", "jpeg", "jfif", "webp"],
        accept_multiple_files=True
    )

all_photos = []
if camera_photo:
    all_photos.append(camera_photo)
if uploaded_files:
    all_photos.extend(uploaded_files)

optimized_images = []
if all_photos:
    st.success(f"ទទួលបានរូបភាពចំនួន {len(all_photos)} សន្លឹក")
    with st.expander("ចុចទីនេះដើម្បីមើលរូបភាពដែលបានបញ្ចូល", expanded=False):
        cols = st.columns(3)
        for idx, file in enumerate(all_photos):
            compressed_img = compress_image(file)
            optimized_images.append(compressed_img)
            with cols[idx % 3]:
                st.image(compressed_img, use_container_width=True)

# ==========================================
# ៧. ប៊ូតុងបញ្ជា និង ការបង្ហាញលទ្ធផល
# ==========================================
st.write("")
if st.button(btn_text, type="primary", use_container_width=True):
    if not api_key:
        st.error("⚠ សូមបញ្ចូល API Key នៅក្នុងផ្ទាំងកំណត់ (Sidebar) ឬកំណត់ក្នុង Secrets!")
    elif not input_type.strip():
        st.warning(f"⚠ សូមបញ្ជាក់ប្រភេទ{'សត្វ' if mode_flag == 'animal' else 'ដំណាំ'}!")
    elif not symptoms_input.strip() and not all_photos:
        st.warning("⚠ សូមរៀបរាប់ពីរោគសញ្ញា ឬបញ្ចូលរូបភាពយ៉ាងហោចណាស់មួយ!")
    else:
        with st.spinner("⏳ ប្រព័ន្ធ AI កំពុងវិភាគជំងឺ និងផ្ទៀងផ្ទាត់ក្បួនផ្សំថ្នាំតាមក្រុម... សូមរង់ចាំបន្តិច!"):
            try:
                result = analyze_with_ai(
                    input_type, extra_info, symptoms_input, optimized_images, api_key, mode_flag
                )
                save_history(input_type, symptoms_input, result, mode_flag)
                st.session_state["last_result"] = result
                st.session_state["last_meta"] = {
                    "type": input_type,
                    "extra": extra_info,
                    "symptoms": symptoms_input,
                }
            except Exception as e:
                error_msg = str(e).lower()
                if "quota" in error_msg or "429" in error_msg:
                    st.error("❌ គណនី API របស់អ្នកបានប្រើប្រាស់អស់កូតាហើយ។")
                elif "api key" in error_msg or "401" in error_msg or "403" in error_msg:
                    st.error("❌ API Key របស់អ្នកមិនត្រឹមត្រូវទេ។")
                else:
                    st.error(f"❌ មានបញ្ហាមិនប្រក្រតី៖ {e}")

# បង្ហាញលទ្ធផលពី Session State (មិនបាត់ពេលចុចប៊ូតុង Download)
if st.session_state["last_result"]:
    result = st.session_state["last_result"]
    meta = st.session_state["last_meta"]

    st.success("✅ ការវិភាគ និងក្បួនផ្សំថ្នាំទទួលបានជោគជ័យ!")

    with st.container(border=True):
        st.subheader("📋 វេជ្ជបញ្ជា និងក្បួនផ្សំថ្នាំលម្អិត")
        st.markdown(result)

    st.write("---")
    st.subheader("📋 ៣. ចម្លង និង នាំចេញឯកសារ")

    st.info("ចុចលើសញ្ញា 📋 នៅជ្រុងស្តាំខាងលើនៃប្រអប់ខាងក្រោម ដើម្បី Copy យកទៅផ្ញើក្នុង Telegram ឬ Facebook។")
    st.code(result, language="markdown")

    c_dl, c_clr = st.columns(2)
    with c_dl:
        export_text = (
            f"ប្រភេទ៖ {meta.get('type', '')}\n"
            f"ទម្ងន់/ស្ថានភាព៖ {meta.get('extra', 'មិនបានបញ្ជាក់')}\n"
            f"រោគសញ្ញា៖ {meta.get('symptoms', '')}\n\n"
            f"លទ្ធផលវិភាគ និងក្បួនផ្សំថ្នាំ៖\n{result}"
        )
        st.download_button(
            label="📥 ទាញយកជាឯកសារ (.txt)",
            data=export_text.encode("utf-8"),
            file_name=f"Diagnosis_{meta.get('type', 'report')}_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.txt",
            mime="text/plain",
            use_container_width=True
        )
    with c_clr:
        if st.button("🗑️ សម្អាតលទ្ធផលចាស់", use_container_width=True):
            st.session_state["last_result"] = ""
            st.session_state["last_meta"] = {}
            st.rerun()
