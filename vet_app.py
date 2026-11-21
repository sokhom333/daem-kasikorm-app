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
    c.execute("""
        CREATE TABLE IF NOT EXISTS medical_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            animal_type TEXT,
            symptoms TEXT,
            diagnosis TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS plant_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            plant_type TEXT,
            symptoms TEXT,
            diagnosis TEXT
        )
    """)
    conn.commit()
    conn.close()


def save_history(type_name, symptoms, diagnosis, category):
    conn = sqlite3.connect("vet_clinic.db")
    c = conn.cursor()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if category == "animal":
        c.execute(
            "INSERT INTO medical_history (date, animal_type, symptoms, diagnosis) VALUES (?, ?, ?, ?)",
            (now, type_name, symptoms, diagnosis),
        )
    else:
        c.execute(
            "INSERT INTO plant_history (date, plant_type, symptoms, diagnosis) VALUES (?, ?, ?, ?)",
            (now, type_name, symptoms, diagnosis),
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
    unsafe_allow_html=True,
)
st.divider()

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
# ៥. បញ្ជីឈ្មោះថ្នាំក្នុងហាង និង អនុគមន៍ហៅ AI
# ==========================================
# 💡 អ្នកអាចវាយបន្ថែម ឬកែឈ្មោះផលិតផលថ្នាំក្នុងហាងរបស់អ្នកនៅទីនេះបានតាមចិត្ត៖
SHOP_DRUG_CATALOG = """
- ថ្នាំផ្សះក្រុម A (សម្លាប់បាក់តេរី / Bactericidal):
  Amoxicillin, Ampicillin, Ceftiofur, Cefquinome, Gentamicin, Colistin, Enrofloxacin, Marbofloxacin, Sulfadiazine + Trimethoprim
- ថ្នាំផ្សះក្រុម B (បង្អាក់បាក់តេរី / Bacteriostatic):
  Oxytetracycline, Doxycycline, Florfenicol, Tylosin, Tilmicosin, Lincomycin, Spectinomycin, Tiamulin
- ថ្នាំបំបាត់ឈឺ / បញ្ចុះកម្ដៅ / រលាក:
  Analgin, Flunixin, Meloxicam, Ketoprofen, Dexamethasone (ហាមប្រើលើសត្វផើម)
- ថ្នាំជំនួយ / វីតាមីន / រ៉ែ:
  ADE B-Complex, Calcium B12, Vitamin C, អេឡិចត្រូលីត (Electrolytes), មេរំលាយអាហារ (Probiotics)
"""


def analyze_with_ai(target_type, extra_info, symptoms, images, key, mode):
    client = genai.Client(api_key=key)

    if mode == "animal":
        prompt = f"""អ្នកគឺជាវេជ្ជបណ្ឌិតពេទ្យសត្វជំនាញកម្រិតស្តង់ដារអន្តរជាតិ ប្រចាំហាង «ដើមកសិកម្ម»។
សូមធ្វើការវិភាគករណីខាងក្រោមជាភាសាខ្មែរឱ្យខ្លី ច្បាស់លាស់ និងងាយអនុវត្តលើទូរស័ព្ទ៖
- ប្រភេទសត្វ៖ {target_type}
- ទម្ងន់ / អាយុ / ស្ថានភាពសត្វ៖ {extra_info or 'មិនបានបញ្ជាក់'}
- រោគសញ្ញា៖ {symptoms or 'សូមពិនិត្យតាមរូបភាពដែលបានភ្ជាប់'}

បញ្ជីឈ្មោះថ្នាំដែលមានស្រាប់សម្រាប់ជ្រើសរើសផ្សំ៖
{SHOP_DRUG_CATALOG}

ច្បាប់មាសផ្សំថ្នាំពេទ្យសត្វដាច់ខាត (៨ ក្រុមថ្នាំផ្សះ)៖
1. ✅ **ក្រុម A + ក្រុម A (Synergism)៖** Beta-lactam (Amoxicillin/Ampicillin/Ceftiofur) + Aminoglycoside (Gentamicin/Colistin) ឬ Beta-lactam + Fluoroquinolone (Enrofloxacin)។
2. ✅ **ក្រុម B + ក្រុម B (Additive)៖** Florfenicol + Doxycycline, Tylosin + Doxycycline, Oxytetracycline + Tylosin ឬ Lincomycin + Spectinomycin។ (ជៀសវាងផ្សំ Florfenicol + Tylosin/Lincomycin ចូលគ្នា ព្រោះដណ្តើមទីតាំង 50S តែមួយ)។
3. ❌ **ហាមដាច់ខាត ក្រុម A + ក្រុម B (Antagonism)៖** ធ្វើឱ្យថ្នាំប្រឆាំងគ្នា សាបប្រសិទ្ធភាព និងបាក់តេរីស៊ាំថ្នាំ។
4. ❌ ហាមផ្សំ **NSAIDs** (Analgin, Flunixin, Meloxicam, Ketoprofen) ជាមួយ **Dexamethasone** ព្រមគ្នា និងហាមប្រើ Dexamethasone លើសត្វផើម។
5. ❌ **ច្បាប់សឺរ៉ាំង៖** ហាមបូមថ្នាំផ្សះ ២ មុខ ឬថ្នាំផ្សះលាយជាមួយថ្នាំរលាក/Calcium B12/វីតាមីន ចូលក្នុង**សឺរ៉ាំងតែមួយ**ដាច់ខាត ត្រូវចាក់ផ្សេងសឺរ៉ាំង និងផ្សេងកន្លែង (ឧ. ក-ឆ្វេង និង ក-ស្តាំ)។

សូមឆ្លើយតបតាមទម្រង់ ៥ ចំណុចខាងក្រោម៖

### ១. ឈ្មោះជំងឺសង្ស័យ (ខ្មែរ និងអង់គ្លេស)
### ២. ការវិភាគរូបភាព និងរោគសញ្ញា
### ៣. មូលហេតុបង្កជំងឺ
### ៤. 💊 វិធីព្យាបាល និងឈុតថ្នាំផ្សំ ២–៣ មុខ (គោរពតាមក្បួនក្រុមថ្នាំ)

- **ក. ឈុតថ្នាំផ្សំដែលអាចប្រើជាមួយគ្នាបាន (ជ្រើសរើសឈុតណាមួយប្រើ)៖**
  បង្ហាញ **៣ ឈុតជម្រើស** ដោយឈុតនីមួយៗផ្សំ **២ ទៅ ៣ មុខ** ឱ្យច្បាស់លាស់តាមទម្រង់នេះ៖
  * **🥇 ឈុតទី ១ (ឈុតអាទិភាព - រូបមន្ត A+A ឬ B+B)៖** `ឈ្មោះថ្នាំទី ១` + `ឈ្មោះថ្នាំទី ២` + `ឈ្មោះថ្នាំទី ៣ (ថ្នាំរលាក/កម្ដៅ ឬវីតាមីន)`
    * *ប្រសិទ្ធភាព៖* ពន្យល់ខ្លី ១ ប្រយោគថាហេតុអ្វី ២–៣ មុខនេះផ្សំគ្នាត្រូវជំងឺ។
  * **🥈 ឈុតទី ២ (ឈុតជំនួស ២–៣ មុខ)៖** `ឈ្មោះថ្នាំទី ១` + `ឈ្មោះថ្នាំទី ២` + `ឈ្មោះថ្នាំទី ៣`
    * *ប្រសិទ្ធភាព៖* ពន្យល់ខ្លី ១ ប្រយោគ (ប្រើពេលរកឈុតទី ១ មិនបាន ឬធ្លាប់ប្រើឈុតទី ១ ហើយមិនបាត់)។
  * **🥉 ឈុតទី ៣ (ឈុតសង្គ្រោះធ្ងន់ធ្ងរ ឬឈុតសន្សំសំចៃ ២–៣ មុខ)៖** `ឈ្មោះថ្នាំទី ១` + `ឈ្មោះថ្នាំទី ២` (+ `ឈ្មោះថ្នាំទី ៣`)
    * *ប្រសិទ្ធភាព៖* ពន្យល់ខ្លី ១ ប្រយោគ។

- **ខ. តារាងកម្រិតប្រើប្រាស់លម្អិត (សម្រាប់ឈុតទី ១)៖**
| ឈ្មោះថ្នាំ | ក្រុមថ្នាំ (A/B/ជំនួយ) | តួនាទី | កម្រិតប្រើ (mg/kg ឬ ml/kg) | វិធីប្រើ & ទីតាំង | រយៈពេល |
| :--- | :--- | :--- | :--- | :--- | :--- |
| ... | ... | ... | ... | ... | ... |

- **គ. ⛔ ក្រុមថ្នាំហាមផ្សំ និងការប្រុងប្រយ័ត្ន៖**
  - បញ្ជាក់ឈ្មោះថ្នាំដែល**ហាមផ្សំ**ជាមួយឈុតខាងលើ ការហាមលាយសឺរ៉ាំងតែមួយ ការព្រមានលើសត្វផើម និង**រយៈពេលឈប់ប្រើថ្នាំមុនលក់សាច់/ស៊ុត/ទឹកដោះ (Withdrawal Time)**។

### ៥. 🛡️ វិធានការការពារ និងការគ្រប់គ្រងទ្រុង
"""
    else:
        prompt = f"""អ្នកគឺជាអ្នកជំនាញក្សេត្រសាស្ត្រកម្រិតស្តង់ដារអន្តរជាតិ ប្រចាំហាង «ដើមកសិកម្ម»។
សូមធ្វើការវិភាគករណីដំណាំខាងក្រោមជាភាសាខ្មែរឱ្យលម្អិត និងងាយស្រួលអនុវត្ត៖
- ប្រភេទដំណាំ៖ {target_type}
- ដំណាក់កាលដំណាំ៖ {extra_info or 'មិនបានបញ្ជាក់'}
- រោគសញ្ញា៖ {symptoms or 'សូមពិនិត្យតាមរូបភាពដែលបានភ្ជាប់'}

សូមឆ្លើយតបតាមទម្រង់ ៥ ចំណុចខាងក្រោម៖

### ១. ឈ្មោះជំងឺ / សត្វល្អិតចង្រៃ (ខ្មែរ និងអង់គ្លេស)
### ២. ការវិភាគរូបភាព និងរោគសញ្ញា
### ៣. មូលហេតុបង្ក
### ៤. 🌿 វិធីសង្គ្រោះ និងឈុតថ្នាំផ្សំបាញ់ ២–៣ មុខ (FRAC / IRAC)
- **ក. ឈុតថ្នាំផ្សំបាញ់ដែលអាចលាយចូលគ្នាបាន៖**
  * **🥇 ឈុតទី ១ (ឈុតអាទិភាព ២–៣ មុខ)៖** `ថ្នាំទី ១` + `ថ្នាំទី ២` + `ថ្នាំជំនួយ/ថ្នាំស្អិត`
    * *ប្រសិទ្ធភាព៖* ពន្យល់ខ្លី ១ ប្រយោគ។
  * **🥈 ឈុតទី ២ (ឈុតបង្វិលក្រុមការពារស៊ាំថ្នាំ ២–៣ មុខ)៖** `ថ្នាំទី ១` + `ថ្នាំទី ២` + `ថ្នាំជំនួយ/ថ្នាំស្អិត`
    * *ប្រសិទ្ធភាព៖* ពន្យល់ខ្លី ១ ប្រយោគ។
- **ខ. តារាងកម្រិតលាយថ្នាំ (សម្រាប់ឈុតទី ១)៖**
| ឈ្មោះសារធាតុសកម្ម | ក្រុមថ្នាំ (FRAC/IRAC) | តួនាទី | កម្រិតលាយ (ក្នុងទឹក ១៦–២០ លីត្រ) | ចន្លោះថ្ងៃបាញ់ |
| :--- | :--- | :--- | :--- | :--- |
| ... | ... | ... | ... | ... |
- **គ. លំដាប់លាយថ្នាំ (W-A-L-E-S) ក្រុមហាមលាយ និងរយៈពេលឈប់បាញ់មុនប្រមូលផល (PHI)៖**
  - ណែនាំលំដាប់លាយ (ម្សៅ WP/WDG -> ទឹកខាប់ SC -> ទឹកថ្លា SL/EC -> ជីបំប៉នស្លឹក -> ថ្នាំស្អិត) ក្រុមថ្នាំហាមលាយចូលធុងតែមួយ និងចំនួនថ្ងៃឈប់បាញ់មុនប្រមូលផល។

### ៥. 🛡️ វិធានការការពារ និងការថែទាំដី/ចម្ការ
"""

    contents_list = [prompt]
    contents_list.extend(images)
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=contents_list,
        config=types.GenerateContentConfig(temperature=0.2),
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
            key="animal_input",
        )
        extra_info = c2.text_input(
            "ទម្ងន់ / អាយុ / ស្ថានភាព (ជាការស្រេចចិត្ត)៖",
            placeholder="ឧ. ជ្រូក ២៥kg, មេជ្រូកផើម, មាន់ ១.៥kg...",
            key="animal_extra",
        )
        symptoms_input = st.text_area(
            "រៀបរាប់ពីរោគសញ្ញា ឬអាការៈសត្វ៖",
            height=120,
            placeholder="ឧទាហរណ៍៖ សត្វអត់ស៊ីចំណី, ក្ដៅខ្លួន, ក្អកហត់, រាកស...",
            key="animal_symptoms",
        )
        btn_text = "🔍 ចាប់ផ្តើមវិភាគជំងឺ និងរៀបចំឈុតផ្សំថ្នាំសត្វ"
        mode_flag = "animal"
    else:
        st.subheader("១. បញ្ចូលព័ត៌មាន និងរោគសញ្ញាដំណាំ")
        c1, c2 = st.columns(2)
        input_type = c1.text_input(
            "ប្រភេទដំណាំ (ឧ. ស្រូវ, ស្វាយ, ម្រេច, បន្លែ...) ៖",
            placeholder="វាយបញ្ចូលទីនេះ...",
            key="plant_input",
        )
        extra_info = c2.text_input(
            "ដំណាក់កាលដំណាំ (ជាការស្រេចចិត្ត)៖",
            placeholder="ឧ. កំពុងបែកគុម្ព, កំពុងចេញផ្កា, ជិតប្រមូលផល...",
            key="plant_extra",
        )
        symptoms_input = st.text_area(
            "រៀបរាប់ពីរោគសញ្ញា៖",
            height=120,
            placeholder="ឧទាហរណ៍៖ ស្លឹកឡើងលឿងប្រឆុះ, ជាំចុងស្លឹក, មានដង្កូវស៊ីស្លឹក...",
            key="plant_symptoms",
        )
        btn_text = "🔍 ចាប់ផ្តើមវិភាគជំងឺ និងរៀបចំឈុតផ្សំថ្នាំដំណាំ"
        mode_flag = "plant"

st.write("---")
st.subheader("📸 ២. បញ្ចូលរូបភាព (ជាការស្រេចចិត្ត)")
tab1, tab2 = st.tabs(["📷 ថតរូបផ្ទាល់ពីកាមេរ៉ា", "📁 ជ្រើសរើសពីរូបថតដែលមានស្រាប់"])

with tab1:
    camera_photo = st.camera_input("ថតរូបភាពទីនេះ៖")
with tab2:
    uploaded_files = st.file_uploader(
        "ជ្រើសរើសរូបភាព (អាចរើសបានច្រើនសន្លឹក)៖",
        type=["png", "jpg", "jpeg", "jfif", "webp"],
        accept_multiple_files=True,
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
        with st.spinner("⏳ ប្រព័ន្ធ AI កំពុងវិភាគជំងឺ និងផ្គូផ្គងឈុតផ្សំថ្នាំ... សូមរង់ចាំបន្តិច!"):
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

    st.success("✅ ការវិភាគ និងឈុតផ្សំថ្នាំទទួលបានជោគជ័យ!")

    with st.container(border=True):
        st.subheader("📋 វេជ្ជបញ្ជា និងឈុតផ្សំថ្នាំលម្អិត")
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
            f"លទ្ធផលវិភាគ និងឈុតផ្សំថ្នាំ៖\n{result}"
        )
        st.download_button(
            label="📥 ទាញយកជាឯកសារ (.txt)",
            data=export_text.encode("utf-8"),
            file_name=f"Diagnosis_{meta.get('type', 'report')}_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.txt",
            mime="text/plain",
            use_container_width=True,
        )
    with c_clr:
        if st.button("🗑️ សម្អាតលទ្ធផលចាស់", use_container_width=True):
            st.session_state["last_result"] = ""
            st.session_state["last_meta"] = {}
            st.rerun()
