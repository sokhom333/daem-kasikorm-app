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
    img.save(buf, format="JPEG", quality=85)
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
    "<p style='font-size: 16px; color: #555;'>ប្រព័ន្ធ AI វិនិច្ឆ័យជំងឺសត្វ និងដំណាំកម្រិតស្តង់ដារអន្តរជាតិ (ប្រៀបធៀបជំងឺ + សញ្ញាផ្ទៀងផ្ទាត់ + ឈុតផ្សំថ្នាំតាមក្រុម)</p>",
    unsafe_allow_html=True,
)
st.divider()

try:
    api_key = st.secrets.get("GEMINI_API_KEY")
except Exception:
    api_key = None

# ==========================================
# ៤. របារចំហៀង (Sidebar)
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
# ៥. មូលដ្ឋានចំណេះដឹងជំងឺតាមប្រភេទសត្វ និងបញ្ជីថ្នាំក្នុងហាង
# ==========================================
SHOP_DRUG_CATALOG = """
- ថ្នាំផ្សះក្រុម A (សម្លាប់បាក់តេរី / Bactericidal):
  Amoxicillin, Ampicillin, Ceftiofur, Cefquinome, Gentamicin, Colistin, Enrofloxacin, Marbofloxacin, Sulfadiazine + Trimethoprim
- ថ្នាំផ្សះក្រុម B (បង្អាក់បាក់តេរី / Bacteriostatic):
  Oxytetracycline, Doxycycline, Florfenicol, Tylosin, Tilmicosin, Lincomycin, Spectinomycin, Tiamulin
- ថ្នាំប៉ារ៉ាស៊ីត / កុក្ស៊ីឌីយ៉ូស៊ីស / ព្រូន:
  Toltrazuril, Amprolium, Sulfaclozine, Ivermectin, Albendazole, Levamisole, Diminazene aceturate
- ថ្នាំបំបាត់ឈឺ / បញ្ចុះកម្ដៅ / រលាក:
  Analgin, Paracetamol (សម្រាប់បក្សី/ជ្រូក), Flunixin, Meloxicam, Ketoprofen, Dexamethasone (ហាមប្រើលើសត្វផើម និងជំងឺវីរុសធ្ងន់ធ្ងរ)
- ថ្នាំជំនួយ / វីតាមីន / រំលាយអាហារ:
  ADE B-Complex, Calcium B12, Vitamin C, អេឡិចត្រូលីត (Electrolytes), មេរំលាយអាហារ (Probiotics), ថ្នាំបំប៉នថ្លើម-តម្រងនោម (Sorbitol/Choline)
"""

SPECIES_DISEASE_KB = {
    "ទា": """
ឯកសារយោងជំងឺសំខាន់ៗលើសត្វទានៅកម្ពុជា (ត្រូវផ្ទៀងផ្ទាត់មុនសន្និដ្ឋាន ហាមច្រឡំជាមួយជំងឺមាន់)៖
- [វីរុស] ជំងឺប៉េស្តទា (Duck Plague / Duck Virus Enteritis): ហើមក្បាល ហើមមុខ ហូរទឹកភ្នែក រាកលាមកបៃតងលាយទឹក ទន់ជើង ងាប់លឿនច្រើនក្បាល។ វះពិនិត្យ៖ ចំណុចឈាមក្រហម ឬស្រទាប់ដំបៅពណ៌លឿងលើបំពង់អាហារ និងរន្ធគូទ ថ្លើមមានចំណុចឈាម។
- [វីរុស] ផ្ដាសាយបក្សី (Avian Influenza - H5N1): ងាប់ភ្លាមៗច្រើនក្បាល ងក់ក ភ្នែកឡើងពពក ហើមក្បាល ជាំជើង។
- [វីរុស] ជំងឺរលាកថ្លើមទា (Duck Viral Hepatitis): កើតលើកូនទាអាយុក្រោម ៣ សប្តាហ៍ ងាប់លឿនក្នុងឥរិយាបថងើយក្បាលទៅក្រោយ (Opisthotonos)។ វះពិនិត្យ៖ ថ្លើមហើមធំមានចំណុចឈាម។
- [បាក់តេរី] ជំងឺរលាកស្រោមបេះដូង-ថ្លើមទា (Riemerella anatipestifer): ហើមមុខ/រន្ធច្រមុះ ហៀរសំបោរ ងក់ក ញ័រក្បាល ដើរដួល រាកបៃតង។ វះពិនិត្យ៖ មានស្រទាប់ស/លឿងក្រាស់ (Fibrinous) គ្របលើបេះដូង ថ្លើម និងថង់ខ្យល់។
- [បាក់តេរី] ជំងឺសាទឹកទា (Fowl Cholera / Pasteurella multocida): ងាប់លឿន សំកុក រាកលឿង/បៃតង ហើមសន្លាក់ជើង។ វះពិនិត្យ៖ ថ្លើមមានចំណុចសតូចៗដូចក្បាលម្ជុល បេះដូងមានចំណុចឈាម។
- [បាក់តេរី] E. coli (Colibacillosis) និង Salmonellosis: រាកស រលាកផ្ចិតកូនទា រលាកថង់ខ្យល់។
- [ផ្សិត] Aspergillosis (ផ្សិតសួត): ដង្ហក់ហត់មាត់ចំហ គ្មានសំឡេងសំបោរ វះឃើញដុំពកលឿង/សក្នុងសួត។
""",
    "មាន់": """
ឯកសារយោងជំងឺសំខាន់ៗលើសត្វមាន់នៅកម្ពុជា៖
- [វីរុស] ជំងឺដង្កោ (Newcastle Disease): រាកបៃតង ដង្ហក់ហត់ ងក់ក ទន់ជើង ងាប់ខ្ពស់។ វះពិនិត្យ៖ ឈាមលើក្រពះក្រពេញ (Proventriculus) និងពោះវៀន។
- [វីរុស] ជំងឺហ្គាំបូរ៉ូ (IBD / Gumboro): កូនមាន់អាយុ ៣–៦ សប្តាហ៍ រាកទឹកស សំកុក ជ្រុះស្លាប។ វះពិនិត្យ៖ សាច់ដុំភ្លៅមានស្នាមឈាម ថង់បួសា (Bursa) ហើមមានទឹកឬឈាម។
- [វីរុស] ផ្ដាសាយបក្សី (Avian Influenza): ជាំសិរ ហើមមុខ ជាំស្បែកជើង ងាប់គំហុក។
- [វីរុស] ជំងឺរលាកទងសួត (IB) / ជំងឺអុតមាន់ (Fowl Pox): កន្ទួលក្រមរលើមុខ/សិរ ឬបន្ទះលឿងក្នុងមាត់។
- [បាក់តេរី] ជំងឺហើមមុខមាន់ (Infectious Coryza - Avibacterium paragallinarum): ហើមមុខ ហើមភ្នែក ហៀរសំបោរខាប់មានក្លិនស្អុយខ្លាំង។
- [បាក់តេរី] ជំងឺផ្លូវដង្ហើមរ៉ាំរ៉ៃ (CRD / Mycoplasma gallisepticum): ក្អក ហៀរសំបោរ ដកដង្ហើមឮសូរក្រោកៗ ភ្នែកមានពពុះ។
- [បាក់តេរី] ជំងឺសាទឹក (Fowl Cholera): ងាប់ភ្លាមៗ សិរឡើងស្វាយ រាកលឿង/បៃតង ថ្លើមមានចំណុចស។
- [ប៉ារ៉ាស៊ីត] ជំងឺរាកឈាម (Coccidiosis): រាកលាមកលាយឈាមស្រស់ ឬពណ៌ត្នោត ស្លេកសិរ។ វះពិនិត្យ៖ ពោះវៀនតាន់ (Ceca) ហើមពេញដោយឈាម។
""",
    "ជ្រូក": """
ឯកសារយោងជំងឺសំខាន់ៗលើសត្វជ្រូកនៅកម្ពុជា៖
- [វីរុស] ប៉េស្តជ្រូកអាហ្វ្រិក (ASF): ក្ដៅខ្លាំង (>41°C) អត់ស៊ី ស្បែកក្រហមជាំតាមត្រចៀក/ពោះ/ជើង ក្អួត រាកឈាម ងាប់ជិត ១០០% (គ្មានវ៉ាក់សាំងទូទៅ និងគ្មានថ្នាំព្យាបាល ត្រូវកម្ទេច/ដាក់ដាច់ដោយឡែកភ្លាម)។
- [វីរុស] ប៉េស្តជ្រូកបុរាណ (CSF): ក្ដៅខ្លាំង អាចម៍ភ្នែក ដើរទ្រេត រាកលឿង ជាំស្បែក។ វះពិនិត្យ៖ តម្រងនោមមានចំណុចឈាមដូចស៊ុតទាព្រៃ។
- [វីរុស] ជំងឺត្រចៀកខៀវ (PRRS): មេជ្រូករលូតកូនចុងខែ កូនជ្រូកហត់ដង្ហក់ ត្រចៀកឡើងពណ៌ខៀវស្វាយ។
- [វីរុស] អុតក្ដាម (FMD): ពងបែកលើច្រមុះ មាត់ និងក្រចកជើង ដើរខ្ញើច។
- [វីរុស] PED / TGE: កូនជ្រូកបៅដោះក្អួត រាកទឹកលឿងខ្លាំង ខ្សោះទឹកងាប់លឿន។
- [បាក់តេរី] សាទឹក (Pasteurellosis): ហើមបំពង់ក ដង្ហក់ហត់ ស្បែកក្រហមស្វាយ។
- [បាក់តេរី] រលាកសួតធ្ងន់ធ្ងរ (APP - Actinobacillus pleuropneumoniae): ក្អកខ្លាំង ដង្ហក់ ហូរពពុះឈាមតាមច្រមុះ ងាប់លឿន។
- [បាក់តេរី] Streptococcus suis: ងក់ក ប្រកាច់ ជើងធាក់ដូចជិះកង់ (រលាកស្រោមខួរ) ឬហើមសន្លាក់។
- [បាក់តេរី] រាកសកូនជ្រូក (E. coli) / រាកឈាម (Lawsonia / Brachyspira) / ក្អកស្ងួតរ៉ាំរ៉ៃ (Mycoplasma hyopneumoniae)។
""",
    "គោ/ក្របី": """
ឯកសារយោងជំងឺសំខាន់ៗលើគោ-ក្របីនៅកម្ពុជា៖
- [វីរុស] អុតក្ដាម (FMD): ហៀរទឹកមាត់ជាពពុះ ពងបែកក្នុងមាត់ អណ្ដាត និងចន្លោះក្រចក ដើរខ្ញើច។
- [វីរុស] ជំងឺដុំពកលើស្បែក (LSD - Lumpy Skin Disease): ក្ដៅខ្លួន ចេញដុំពករឹងពេញខ្លួន កូនកណ្ដុរហើម។
- [វីរុស] ជំងឺគ្រុន ៣ ថ្ងៃ (BEF): ក្ដៅខ្លួនភ្លាមៗ រឹងជើង ដើរខ្ញើច ហៀរទឹកភ្នែក/សំបោរ ភាគច្រើនធូរក្នុង ៣–៥ ថ្ងៃ។
- [បាក់តេរី] ជំងឺសាទឹក (Hemorrhagic Septicemia): ក្ដៅខ្លាំង ហើមបំពង់ក និងទ្រូង ដកដង្ហើមឮសូរខ្លាំង ងាប់លឿនក្នុង ២៤–៤៨ ម៉ោង។
- [បាក់តេរី] ជំងឺរលាកដោះ (Mastitis): ដោះហើមក្ដៅ ទឹកដោះមានកកឬឈាម។
- [ប៉ារ៉ាស៊ីតឈាម] Babesiosis / Anaplasmosis / Trypanosomiasis: ស្លេកស្លាំង លឿងភ្នែក នោមពណ៌ក្រហម/កាហ្វេ ស្គមរីងរៃ មានដង្កែឬរុយខាំ។
- [រំលាយអាហារ] ហើមពោះ (Ruminal Bloat): ពោះខាងឆ្វេងប៉ោងធំខ្លាំង ពិបាកដកដង្ហើម។
""",
    "ត្រី/កង្កែប": """
ឯកសារយោងជំងឺសំខាន់ៗលើត្រី-កង្កែបនៅកម្ពុជា៖
- [បាក់តេរី] Aeromonas (ជំងឺដំបៅក្រហម / ជើងក្រហមលើកង្កែប): មានដំបៅឈាមលើខ្លួន ពោះហើមមានទឹក ជើងកង្កែបក្រហម។
- [បាក់តេរី] Streptococcus: ត្រី/កង្កែបភ្នែកលៀន ភ្នែកឡើងស ងក់ក ហែលវិលវង់។
- [បាក់តេរី] Edwardsiella (ជំងឺចំណុចសក្នុងសរីរាង្គ): វះឃើញចំណុចសតូចៗលើថ្លើម តម្រងនោម និងផាល (ឧស្សាហ៍កើតលើត្រីប្រា/ត្រីពោ/ត្រីអណ្ដែង)។
- [ប៉ារ៉ាស៊ីត/ផ្សិត] ផ្សិតទឹក (Saprolegnia - សំឡីសលើស្បែក), ដង្កូវស្បែក/ដង្កូវស្រកី (ត្រីត្រដុសខ្លួន ហើបមាត់ដកដង្ហើមលើទឹក)។
- [បរិស្ថានទឹក] ពុលអាម៉ូញាក់ (NH3) ឬខ្វះអុកស៊ីសែន៖ ងាប់ព្រមគ្នាពេលទៀបភ្លឺ ឬក្រោយភ្លៀងធំ។
""",
    "ឆ្កែ/ឆ្មា": """
ឯកសារយោងជំងឺសំខាន់ៗលើឆ្កែ-ឆ្មានៅកម្ពុជា៖
- [វីរុស] Parvovirus (ឆ្កែ) / Panleukopenia (ឆ្មា): ក្អួតខ្លាំង រាកឈាមធុំក្លិនឆ្អាបខ្លាំង ខ្សោះទឹកធ្ងន់ធ្ងរ (ត្រូវព្យួរសេរ៉ូមជាបន្ទាន់)។
- [វីរុស] Canine Distemper (ការ៉េឆ្កែ): ក្ដៅខ្លួន ហៀរសំបោរ អាចម៍ភ្នែកខាប់ ក្អក ជើងក្រិន ឈានដល់កន្ត្រាក់ប្រព័ន្ធប្រសាទ។
- [ប៉ារ៉ាស៊ីតឈាម] Ehrlichiosis / Babesiosis (ឆ្លងតាមចៃឆ្កែ): ក្ដៅខ្លួន ស្លេកអញ្ចាញធ្មេញ ហូរឈាមច្រមុះ នោមពណ៌ចាស់។
- [សើស្បែក] រមាស់/ស្រែង (Demodex / Sarcoptes / Ringworm): ជ្រុះរោម ស្បែកក្រហមរមាស់ មានអង្គែ។
"""
}


def get_species_knowledge(species_group: str) -> str:
    return SPECIES_DISEASE_KB.get(
        species_group,
        "សូមវិភាគដោយបែងចែកច្បាស់លាស់រវាង វីរុស បាក់តេរី ប៉ារ៉ាស៊ីត និងកង្វះសារធាតុចិញ្ចឹម ឱ្យត្រូវតាមប្រភេទសត្វជាក់ស្តែង។"
    )


def build_vet_guardrails(species_group: str, extra_info: str, vaccine: str, mortality: str) -> str:
    """បង្កើតច្បាប់សុវត្ថិភាពស្វ័យប្រវត្តិតាមស្ថានភាពសត្វ"""
    rules = []
    extra_lower = (extra_info or "").lower()
    mort_lower = (mortality or "").lower()

    if any(k in extra_lower for k in ["ផើម", "មានផ្ទៃពោះ", "កូនក្នុងពោះ", "pregnant"]):
        rules.append(
            "សត្វកំពុងផើម៖ ហាមប្រើ Dexamethasone ដាច់ខាត (បណ្តាលឱ្យរលូតកូន) និងជៀសវាងថ្នាំដែលប៉ះពាល់គភ៌ (ឧ. ប្រុងប្រយ័ត្ន Albendazole/Florfenicol ដំណាក់កាលដំបូង)។"
        )

    if vaccine == "មិនទាន់ចាក់វ៉ាក់សាំង" or any(k in mort_lower for k in ["ងាប់", "ស្លាប់", "លឿន", "ច្រើន"]):
        rules.append(
            "ហានិភ័យជំងឺឆ្លងរាលដាល/វីរុស៖ ត្រូវវាយតម្លៃលទ្ធភាពជំងឺវីរុសធ្ងន់ធ្ងរ (ដូចជា ប៉េស្ត ផ្ដាសាយបក្សី ដង្កោ ASF) ជាអាទិភាព ហើយបញ្ជាក់ច្បាស់ថាថ្នាំផ្សះមិនសម្លាប់វីរុសទេ (ប្រើត្រឹមទប់បាក់តេរីជ្រៀតជ្រែក)។"
        )

    if species_group == "ត្រី/កង្កែប":
        rules.append(
            "សត្វទឹក (ត្រី/កង្កែប)៖ ហាមណែនាំវិធីចាក់សឺរ៉ាំង! ត្រូវណែនាំវិធីលាយថ្នាំជាមួយចំណី (គិតជា g/kg ចំណី ឬ g/100kg ត្រី) រួមជាមួយវិធីសម្លាប់មេរោគ និងកែគុណភាពទឹក (កំបោរ អំបិល អ៊ីយ៉ូដ ឬ BKC)។"
        )
    elif species_group in ["មាន់", "ទា"]:
        rules.append(
            "សត្វបក្សី (មាន់/ទា)៖ ត្រូវបញ្ជាក់ទាំងវិធីលាយទឹកផឹក/លាយចំណីសម្រាប់ព្យាបាលទាំងហ្វូង (គិតជា g ឬ ml ក្នុងទឹក ១ លីត្រ) និងវិធីចាក់សម្រាប់ក្បាលឈឺធ្ងន់។"
        )
    elif species_group == "ឆ្កែ/ឆ្មា":
        rules.append(
            "សត្វចិញ្ចឹម (ឆ្កែ/ឆ្មា)៖ ហាមប្រើ Paracetamol លើសត្វឆ្មាដាច់ខាត (ពុលដល់ស្លាប់) និងត្រូវណែនាំឱ្យនាំទៅគ្លីនិកព្យួរសេរ៉ូមបើសង្ស័យ Parvo/ក្អួតរាកធ្ងន់។"
        )

    if not rules:
        return "- គោរពច្បាប់មាស A+A, B+B, ហាម A+B, ហាម NSAIDs+Dexamethasone និងហាមលាយថ្នាំចូលសឺរ៉ាំងតែមួយ។"
    return "\n".join(f"- {r}" for r in rules)


# ==========================================
# ៦. អនុគមន៍ហៅ AI (ជួសជុលបញ្ហា API v1 រួចរាល់)
# ==========================================
def analyze_with_ai(payload: dict, images: list, key: str, mode: str) -> str:
    client = genai.Client(api_key=key)

    if mode == "animal":
        species_group = payload["species_group"]
        species_kb = get_species_knowledge(species_group)
        guardrails = build_vet_guardrails(
            species_group, payload["extra_info"], payload["vaccine"], payload["mortality"]
        )

        system_instruction = (
            "អ្នកគឺជាវេជ្ជបណ្ឌិតពេទ្យសត្វជំនាញកម្រិតស្តង់ដារអន្តរជាតិ ប្រចាំហាង «ដើមកសិកម្ម»។ "
            "គោលដៅរបស់អ្នកគឺវិនិច្ឆ័យឱ្យសុក្រឹតបំផុតតាមក្បួនពេទ្យសត្វអន្តរជាតិ ដោយហាមទាយផ្តេសផ្តាស ហាមច្រឡំឈ្មោះជំងឺឆ្លងប្រភេទសត្វ "
            "និងត្រូវផ្តល់សញ្ញាផ្ទៀងផ្ទាត់ជាក់ស្តែង (រួមទាំងសញ្ញាវះពិនិត្យសាកសព) ដើម្បីឱ្យម្ចាស់កសិដ្ឋានបញ្ជាក់ជំងឺបាន ១០០% នៅនឹងកន្លែង។"
        )

        prompt = f"""សូមធ្វើការវិភាគករណីសត្វខាងក្រោមជាភាសាខ្មែរឱ្យច្បាស់លាស់ និងត្រឹមត្រូវតាមស្តង់ដារពេទ្យសត្វ៖

=== ទិន្នន័យករណីអ្នកជំងឺសត្វ ===
- ប្រភេទសត្វ៖ {payload['target_type']} (ក្រុម៖ {species_group})
- ទម្ងន់ / អាយុ / ស្ថានភាព៖ {payload['extra_info'] or 'មិនបានបញ្ជាក់'}
- ប្រវត្តិចាក់វ៉ាក់សាំង៖ {payload['vaccine']}
- ចំនួនសត្វឈឺ និងងាប់៖ {payload['mortality'] or 'មិនបានបញ្ជាក់'}
- លក្ខណៈលាមក និងការស៊ីចំណី៖ {payload['stool_feed'] or 'មិនបានបញ្ជាក់'}
- លទ្ធផលវះពិនិត្យសាកសព (បើមាន)៖ {payload['necropsy'] or 'មិនទាន់បានវះពិនិត្យ'}
- រោគសញ្ញាលម្អិត៖ {payload['symptoms'] or 'សូមពិនិត្យតាមរូបភាពដែលបានភ្ជាប់'}

=== មូលដ្ឋានជំងឺយោងសម្រាប់ {species_group} ===
{species_kb}

=== ច្បាប់សុវត្ថិភាពបង្ខំសម្រាប់ករណីនេះ ===
{guardrails}

=== បញ្ជីឈ្មោះថ្នាំសម្រាប់ផ្សំ ===
{SHOP_DRUG_CATALOG}

=== ច្បាប់មាសផ្សំថ្នាំផ្សះដាច់ខាត ===
1. ✅ **ក្រុម A + ក្រុម A (Synergism):** Beta-lactam (Amoxicillin/Ceftiofur) + Aminoglycoside (Gentamicin/Colistin) ឬ Beta-lactam + Fluoroquinolone (Enrofloxacin)។
2. ✅ **ក្រុម B + ក្រុម B (Additive):** Florfenicol + Doxycycline, Tylosin + Doxycycline, Oxytetracycline + Tylosin, ឬ Lincomycin + Spectinomycin។ (ហាមផ្សំ Florfenicol + Tylosin/Lincomycin ព្រោះដណ្តើមទីតាំង 50S តែមួយ)។
3. ❌ **ហាមដាច់ខាត ក្រុម A + ក្រុម B (Antagonism)**។
4. ❌ **ហាមផ្សំ NSAIDs + Dexamethasone** ព្រមគ្នា និងហាមបូមថ្នាំផ្សះលាយជាមួយថ្នាំផ្សេងក្នុងសឺរ៉ាំងតែមួយ។

សូមឆ្លើយតបតាមទម្រង់ស្តង់ដារ ៥ ចំណុចខាងក្រោម (ចូលសាច់រឿងផ្ទាល់ មិនបាច់និយាយសួរសុខទុក្ខវែង)៖

### 🎯 ១. ការវិនិច្ឆ័យប្រៀបធៀបតាមលំដាប់ (Differential Diagnosis)
បំបែកជំងឺសង្ស័យ **៣ លទ្ធភាព** ពីខ្ពស់ទៅទាប ដោយដាក់ប្រភេទមេរោគ `[វីរុស]` / `[បាក់តេរី]` / `[ប៉ារ៉ាស៊ីត]` និងភាគរយសង្ស័យឱ្យច្បាស់៖
1. **លទ្ធភាពទី ១ (ខ្ពស់បំផុត - ប្រមាណ ...%)៖** `[ប្រភេទមេរោគ]` ឈ្មោះខ្មែរ (ឈ្មោះបច្ចេកទេសអង់គ្លេសត្រឹមត្រូវតាមប្រភេទសត្វ) — *ហេតុផលសង្ខេប*
2. **លទ្ធភាពទី ២ (មធ្យម - ប្រមាណ ...%)៖** `[ប្រភេទមេរោគ]` ឈ្មោះខ្មែរ (អង់គ្លេស) — *ហេតុផលសង្ខេប*
3. **លទ្ធភាពទី ៣ (ត្រូវតាមដាន - ប្រមាណ ...%)៖** `[ប្រភេទមេរោគ]` ឈ្មោះខ្មែរ (អង់គ្លេស) — *ហេតុផលសង្ខេប*

### 🔬 ២. វិធីផ្ទៀងផ្ទាត់ឱ្យច្បាស់ ១០០% នៅកសិដ្ឋាន (Field & Necropsy Confirmation)
ប្រាប់សញ្ញាចំណាំជាក់លាក់ **៣ ចំណុច** (ពិនិត្យខាងក្រៅ ឬសញ្ញាវះពិនិត្យសរីរាង្គខាងក្នុងដូចជា ថ្លើម បេះដូង សួត ពោះវៀន បំពង់អាហារ) ដើម្បីឱ្យម្ចាស់សត្វញែកដឹងច្បាស់ ១០០% ថាតើជាលទ្ធភាពទី ១ ទី ២ ឬទី ៣៖
- បើឃើញសញ្ញា (...) ➔ **បញ្ជាក់ ១០០% ថាជាជំងឺទី ១**
- បើឃើញសញ្ញា (...) ➔ **បញ្ជាក់ ១០០% ថាជាជំងឺទី ២**
- បើឃើញសញ្ញា (...) ➔ **បញ្ជាក់ ១០០% ថាជាជំងឺទី ៣**

### 📸 ៣. ការវិភាគរូបភាព និងមូលហេតុបង្ក
- ពិពណ៌នាសញ្ញាដែលឃើញក្នុងរូបភាព (ឬបញ្ជាក់បើគ្មានរូបភាព/រូបភាពមិនច្បាស់) និងកត្តាបង្កជំងឺ។

### 💊 ៤. វិធីព្យាបាល និងឈុតថ្នាំផ្សំ ២–៣ មុខ (គោរពតាមក្បួនក្រុមថ្នាំ)
- **ក. ឈុតថ្នាំផ្សំដែលអាចប្រើជាមួយគ្នាបាន (ជ្រើសឈុតណាមួយប្រើ)៖**
  * **🥇 ឈុតទី ១ (ឈុតអាទិភាព ២–៣ មុខ - បញ្ជាក់រូបមន្ត A+A ឬ B+B ឬថ្នាំប៉ារ៉ាស៊ីត)៖** `ថ្នាំទី ១` + `ថ្នាំទី ២` + `ថ្នាំទី ៣`
    * *ប្រសិទ្ធភាព៖* ពន្យល់ខ្លី ១ ប្រយោគ។
  * **🥈 ឈុតទី ២ (ឈុតជំនួស ២–៣ មុខ)៖** `ថ្នាំទី ១` + `ថ្នាំទី ២` + `ថ្នាំទី ៣`
    * *ប្រសិទ្ធភាព៖* ពន្យល់ខ្លី ១ ប្រយោគ។
  * **🥉 ឈុតទី ៣ (ឈុតសង្គ្រោះធ្ងន់ធ្ងរ ឬឈុតសន្សំសំចៃ ២–៣ មុខ)៖** `ថ្នាំទី ១` + `ថ្នាំទី ២` (+ `ថ្នាំទី ៣`)
    * *ប្រសិទ្ធភាព៖* ពន្យល់ខ្លី ១ ប្រយោគ។
  *(ចំណាំ៖ បើលទ្ធភាពទី ១ ជាវីរុស ត្រូវបញ្ជាក់ច្បាស់ពីការចាក់វ៉ាក់សាំងបន្ទាន់/ដាក់ដាច់ដោយឡែក និងថាឈុតថ្នាំផ្សះប្រើសម្រាប់ទប់ស្កាត់បាក់តេរីជ្រៀតជ្រែកប៉ុណ្ណោះ)*
- **ខ. តារាងកម្រិតប្រើប្រាស់លម្អិត (សម្រាប់ឈុតទី ១)៖**
| ឈ្មោះថ្នាំ | ក្រុមថ្នាំ (A/B/ជំនួយ) | តួនាទី | កម្រិតប្រើ | វិធីប្រើ & ទីតាំង | រយៈពេល |
| :--- | :--- | :--- | :--- | :--- | :--- |
| ... | ... | ... | ... | ... | ... |
- **គ. ⛔ ក្រុមថ្នាំហាមផ្សំ និងរយៈពេលឈប់ប្រើថ្នាំ (Withdrawal Time)៖**
  - បញ្ជាក់ក្រុមថ្នាំដែល**ហាមផ្សំ**ជាមួយឈុតខាងលើ, ការហាមលាយសឺរ៉ាំងតែមួយ (បើជាថ្នាំចាក់), និងចំនួនថ្ងៃឈប់ប្រើថ្នាំមុនលក់សាច់/ស៊ុត/ទឹកដោះ។

### 🛡️ ៥. វិធានការការពារ និងសុវត្ថិភាពជីវសាស្ត្រ
- វិធីសម្លាប់មេរោគក្នុងទ្រុង/ស្រះ ការញែកសត្វឈឺ និងកាលវិភាគវ៉ាក់សាំងការពារ។
"""
    else:
        system_instruction = (
            "អ្នកគឺជាអ្នកជំនាញក្សេត្រសាស្ត្រកម្រិតស្តង់ដារអន្តរជាតិ ប្រចាំហាង «ដើមកសិកម្ម»។ "
            "ត្រូវញែកឱ្យច្បាស់រវាង ផ្សិត បាក់តេរី វីរុស សត្វល្អិត និងកង្វះជីជាតិ "
            "ព្រមទាំងផ្តល់វិធីធ្វើតេស្តបឋមនៅចម្ការដើម្បីបញ្ជាក់មូលហេតុឱ្យច្បាស់ ១០០% និងគោរពលេខកូដក្រុមថ្នាំ FRAC/IRAC។"
        )

        prompt = f"""សូមធ្វើការវិភាគករណីដំណាំខាងក្រោមជាភាសាខ្មែរឱ្យលម្អិត និងត្រឹមត្រូវតាមស្តង់ដារក្សេត្រសាស្ត្រ៖

=== ទិន្នន័យករណីដំណាំ ===
- ប្រភេទដំណាំ៖ {payload['target_type']}
- ដំណាក់កាលលូតលាស់៖ {payload['extra_info'] or 'មិនបានបញ្ជាក់'}
- ល្បឿនរាលដាល និងលក្ខណៈអាកាសធាតុ៖ {payload['weather_spread'] or 'មិនបានបញ្ជាក់'}
- ថ្នាំធ្លាប់បាញ់លើកមុន (ដើម្បីបង្វិលក្រុម)៖ {payload['prev_sprays'] or 'មិនបានបញ្ជាក់'}
- រោគសញ្ញាលម្អិត៖ {payload['symptoms'] or 'សូមពិនិត្យតាមរូបភាពដែលបានភ្ជាប់'}

សូមឆ្លើយតបតាមទម្រង់ស្តង់ដារ ៥ ចំណុចខាងក្រោម៖

### 🎯 ១. ការវិនិច្ឆ័យប្រៀបធៀបតាមលំដាប់ (Differential Diagnosis)
បំបែកលទ្ធភាព **៣ ចំណាត់ថ្នាក់** ដោយបញ្ជាក់ `[ផ្សិត]` / `[បាក់តេរី]` / `[វីរុស]` / `[សត្វល្អិត]` / `[កង្វះជីជាតិ]` និងភាគរយសង្ស័យ៖
1. **លទ្ធភាពទី ១ (...%)៖** `[ប្រភេទ]` ឈ្មោះខ្មែរ (ឈ្មោះអង់គ្លេស/វិទ្យាសាស្ត្រ)
2. **លទ្ធភាពទី ២ (...%)៖** `[ប្រភេទ]` ឈ្មោះខ្មែរ (អង់គ្លេស)
3. **លទ្ធភាពទី ៣ (...%)៖** `[ប្រភេទ]` ឈ្មោះខ្មែរ (អង់គ្លេស)

### 🔬 ២. វិធីផ្ទៀងផ្ទាត់ឱ្យច្បាស់ ១០០% នៅចម្ការ (Field Confirmation Test)
ប្រាប់វិធីពិនិត្យជាក់ស្តែងងាយៗ ២–៣ វិធី (ឧ. ការកាត់ដើម/ស្លឹកជ្រលក់ទឹកថ្លាមើលជ័របាក់តេរី Ooze Test, ការពុះដើមមើលសរសៃទឹក, ការមើលក្រោមស្លឹករកសត្វល្អិតតូចៗ ឬផ្សិត) ដើម្បីបញ្ជាក់ជំងឺ ១០០% មុនទិញថ្នាំបាញ់។

### 📸 ៣. ការវិភាគរូបភាព និងមូលហេតុបង្ក
### 🌿 ៤. វិធីសង្គ្រោះ និងឈុតថ្នាំផ្សំបាញ់ ២–៣ មុខ (FRAC / IRAC)
- **ក. ឈុតថ្នាំផ្សំបាញ់ដែលអាចលាយចូលគ្នាបាន (បង្វិលក្រុមខុសពីថ្នាំធ្លាប់បាញ់)៖**
  * **🥇 ឈុតទី ១ (ឈុតអាទិភាព ២–៣ មុខ)៖** `ថ្នាំទី ១` + `ថ្នាំទី ២` + `ថ្នាំជំនួយ/ថ្នាំស្អិត`
    * *ប្រសិទ្ធភាព៖* ពន្យល់ខ្លី ១ ប្រយោគ។
  * **🥈 ឈុតទី ២ (ឈុតបង្វិលក្រុមការពារស៊ាំថ្នាំ ២–៣ មុខ)៖** `ថ្នាំទី ១` + `ថ្នាំទី ២` + `ថ្នាំជំនួយ/ថ្នាំស្អិត`
    * *ប្រសិទ្ធភាព៖* ពន្យល់ខ្លី ១ ប្រយោគ។
- **ខ. តារាងកម្រិតលាយថ្នាំ (សម្រាប់ឈុតទី ១)៖**
| ឈ្មោះសារធាតុសកម្ម | ក្រុមថ្នាំ (FRAC/IRAC) | តួនាទី | កម្រិតលាយ (ក្នុងទឹក ១៦–២០ លីត្រ) | ចន្លោះថ្ងៃបាញ់ |
| :--- | :--- | :--- | :--- | :--- |
| ... | ... | ... | ... | ... |
- **គ. លំដាប់លាយថ្នាំ (W-A-L-E-S) ក្រុមហាមលាយ និងរយៈពេលឈប់បាញ់មុនប្រមូលផល (PHI)៖**
  - បញ្ជាក់លំដាប់ចាក់ថ្នាំ ក្រុមហាមលាយចូលធុងតែមួយ (ដូចជា ទង់ដែង ស្ពាន់ធ័រ កាល់ស្យូម+ផូស្វ័រ ឬគីមី+ជីវសាស្ត្រ) និងចំនួនថ្ងៃ PHI។

### 🛡️ ៥. វិធានការការពារ និងការគ្រប់គ្រងដី/ទឹក
"""

    # បញ្ចូល system_instruction ទៅខាងលើ prompt ផ្ទាល់ ដើម្បីការពារ Error API v1
    full_prompt = f"{system_instruction}\n\n{prompt}"
    contents_list = [full_prompt]
    contents_list.extend(images)

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=contents_list,
        config=types.GenerateContentConfig(
            temperature=0.1,
        ),
    )
    return response.text


# ==========================================
# ៧. ផ្ទាំងបញ្ចូលទិន្នន័យស្នូលសម្រាប់វិនិច្ឆ័យសុក្រឹត
# ==========================================
with st.container():
    if app_mode == "🩺 ផ្នែកពេទ្យសត្វ":
        st.subheader("១. បញ្ចូលព័ត៌មានស្នូល និងរោគសញ្ញាសត្វ")
        c1, c2 = st.columns(2)
        species_group = c1.selectbox(
            "ជ្រើសរើសក្រុមសត្វ (សំខាន់សម្រាប់ភាពត្រឹមត្រូវ)៖",
            ["ទា", "មាន់", "ជ្រូក", "គោ/ក្របី", "ត្រី/កង្កែប", "ឆ្កែ/ឆ្មា", "ពពែ/សត្វផ្សេងៗ"],
            key="species_select",
        )
        specific_type = c2.text_input(
            "បញ្ជាក់ពូជ/ប្រភេទលម្អិត (ស្រេចចិត្ត)៖",
            placeholder="ឧ. ទាសំប៉ៅ, មាន់ស្រែ, ជ្រូកកូន, កង្កែប...",
            key="animal_input",
        )
        input_type = specific_type.strip() if specific_type.strip() else species_group

        c3, c4 = st.columns(2)
        extra_info = c3.text_input(
            "ទម្ងន់ / អាយុ / ស្ថានភាព៖",
            placeholder="ឧ. ២៥kg, អាយុ ៣ សប្តាហ៍, មេផើម...",
            key="animal_extra",
        )
        vaccine_status = c4.selectbox(
            "ប្រវត្តិចាក់វ៉ាក់សាំង៖",
            ["មិនប្រាកដ / មិនដឹង", "មិនទាន់ចាក់វ៉ាក់សាំង", "ចាក់វ៉ាក់សាំងរួចរាល់"],
            key="animal_vaccine",
        )

        c5, c6 = st.columns(2)
        mortality_info = c5.text_input(
            "អត្រាឈឺ និងងាប់ក្នុងហ្វូង៖",
            placeholder="ឧ. ឈឺ ១៥/១០០ ក្បាល, ងាប់ ៤ ក្បាលក្នុង ២ ថ្ងៃ",
            key="animal_mortality",
        )
        stool_feed = c6.text_input(
            "លាមក និងការស៊ីចំណី៖",
            placeholder="ឧ. រាកបៃតង/ស/ឈាម, អត់ស៊ីចំណី ២ ថ្ងៃ",
            key="animal_stool",
        )

        symptoms_input = st.text_area(
            "រៀបរាប់រោគសញ្ញាខាងក្រៅឱ្យលម្អិត៖",
            height=110,
            placeholder="ឧ. ហើមមុខ ហូរទឹកភ្នែក ងក់ក ដើរដួល ក្ដៅខ្លួន ក្អកហត់...",
            key="animal_symptoms",
        )
        necropsy_input = st.text_input(
            "🔬 លទ្ធផលវះពិនិត្យសាកសព (បើបានវះ នឹងជួយឱ្យ AI បញ្ជាក់ជំងឺជិត ១០០%)៖",
            placeholder="ឧ. ថ្លើមមានចំណុចស, ស្រោមបេះដូងមានស្រទាប់សក្រាស់, បំពង់អាហារមានចំណុចឈាម...",
            key="animal_necropsy",
        )

        payload = {
            "species_group": species_group,
            "target_type": input_type,
            "extra_info": extra_info,
            "vaccine": vaccine_status,
            "mortality": mortality_info,
            "stool_feed": stool_feed,
            "symptoms": symptoms_input,
            "necropsy": necropsy_input,
        }
        btn_text = "🔬 ចាប់ផ្តើមវិនិច្ឆ័យជំងឺ និងរៀបចំឈុតផ្សំថ្នាំសត្វ"
        mode_flag = "animal"

    else:
        st.subheader("១. បញ្ចូលព័ត៌មានស្នូល និងរោគសញ្ញាដំណាំ")
        c1, c2 = st.columns(2)
        input_type = c1.text_input(
            "ប្រភេទដំណាំ (ឧ. ស្រូវ, ស្វាយ, ម្រេច, ត្រសក់...) ៖",
            placeholder="វាយបញ្ចូលទីនេះ...",
            key="plant_input",
        )
        extra_info = c2.text_input(
            "ដំណាក់កាលលូតលាស់៖",
            placeholder="ឧ. កូនដំណាំ, បែកគុម្ព, ចេញផ្កា, ជិតប្រមូលផល...",
            key="plant_extra",
        )

        c3, c4 = st.columns(2)
        weather_spread = c3.text_input(
            "ល្បឿនរាលដាល និងអាកាសធាតុ៖",
            placeholder="ឧ. រាលដាលលឿនក្រោយភ្លៀងធ្លាក់ជោកជាំ ឬក្ដៅហែង",
            key="plant_weather",
        )
        prev_sprays = c4.text_input(
            "ថ្នាំធ្លាប់បាញ់លើកមុន (ដើម្បីបង្វិលក្រុម)៖",
            placeholder="ឧ. ធ្លាប់បាញ់ Abamectin, Mancozeb មិនបាត់...",
            key="plant_prev",
        )

        symptoms_input = st.text_area(
            "រៀបរាប់រោគសញ្ញាដំណាំឱ្យលម្អិត៖",
            height=110,
            placeholder="ឧ. ស្លឹកលឿងពីគល់ ឬចុងស្លឹក, មានស្នាមជាំប្រផេះ, ដើមស្អុយ, មានសត្វល្អិតក្រោមស្លឹក...",
            key="plant_symptoms",
        )

        payload = {
            "target_type": input_type,
            "extra_info": extra_info,
            "weather_spread": weather_spread,
            "prev_sprays": prev_sprays,
            "symptoms": symptoms_input,
        }
        btn_text = "🔬 ចាប់ផ្តើមវិនិច្ឆ័យជំងឺ និងរៀបចំឈុតផ្សំថ្នាំដំណាំ"
        mode_flag = "plant"

# រូបភាព
st.write("---")
st.subheader("📸 ២. បញ្ចូលរូបភាព (រូបសត្វ/ដំណាំ លាមក ឬរូបវះពិនិត្យសរីរាង្គ)")
tab1, tab2 = st.tabs(["📷 ថតរូបផ្ទាល់ពីកាមេរ៉ា", "📁 ជ្រើសរើសពីរូបថតដែលមានស្រាប់"])

with tab1:
    camera_photo = st.camera_input("ថតរូបភាពឱ្យច្បាស់នៅកន្លែងមានពន្លឺគ្រប់គ្រាន់៖")
with tab2:
    uploaded_files = st.file_uploader(
        "ជ្រើសរើសរូបភាព (អាចដាក់ច្រើនសន្លឹក ដូចជារូបខាងក្រៅ + រូបលាមក + រូបវះពិនិត្យ)៖",
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
# ៨. ប៊ូតុងបញ្ជា និង ការបង្ហាញលទ្ធផល
# ==========================================
st.write("")
if st.button(btn_text, type="primary", use_container_width=True):
    if not api_key:
        st.error("⚠ សូមបញ្ចូល API Key នៅក្នុងផ្ទាំងកំណត់ (Sidebar) ឬកំណត់ក្នុង Secrets!")
    elif not input_type.strip():
        st.warning(f"⚠ សូមបញ្ជាក់ប្រភេទ{'សត្វ' if mode_flag == 'animal' else 'ដំណាំ'}!")
    elif not symptoms_input.strip() and not all_photos and not payload.get("necropsy", "").strip():
        st.warning("⚠ សូមរៀបរាប់ពីរោគសញ្ញា ឬបញ្ចូលរូបភាពយ៉ាងហោចណាស់មួយ!")
    else:
        with st.spinner("⏳ ប្រព័ន្ធ AI កំពុងផ្ទៀងផ្ទាត់ជំងឺតាមប្រភេទសត្វ និងរៀបចំឈុតផ្សំថ្នាំ..."):
            try:
                result = analyze_with_ai(payload, optimized_images, api_key, mode_flag)
                save_history(input_type, symptoms_input or payload.get("necropsy", ""), result, mode_flag)
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

# បង្ហាញលទ្ធផលពី Session State
if st.session_state["last_result"]:
    result = st.session_state["last_result"]
    meta = st.session_state["last_meta"]

    st.success("✅ ការវិនិច្ឆ័យប្រៀបធៀប និងឈុតផ្សំថ្នាំបានបញ្ចប់!")

    with st.container(border=True):
        st.subheader("📋 របាយការណ៍វិនិច្ឆ័យ និងឈុតផ្សំថ្នាំលម្អិត")
        st.markdown(result)

    st.write("---")
    st.subheader("📋 ៣. ចម្លង និង នាំចេញឯកសារ")

    st.info("ចុចលើសញ្ញា 📋 នៅជ្រុងស្តាំខាងលើនៃប្រអប់ខាងក្រោម ដើម្បី Copy យកទៅផ្ញើក្នុង Telegram ឬ Facebook។")
    st.code(result, language="markdown")

    c_dl, c_clr = st.columns(2)
    with c_dl:
        export_text = (
            f"ប្រភេទ៖ {meta.get('type', '')}\n"
            f"ទម្ងន់/ដំណាក់កាល៖ {meta.get('extra', 'មិនបានបញ្ជាក់')}\n"
            f"រោគសញ្ញា៖ {meta.get('symptoms', '')}\n\n"
            f"លទ្ធផលវិនិច្ឆ័យ និងឈុតផ្សំថ្នាំ៖\n{result}"
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
