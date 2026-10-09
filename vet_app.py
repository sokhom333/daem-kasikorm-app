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
        c.execute("INSERT INTO medical_history (date, animal_type, symptoms, diagnosis) VALUES (?, ?, ?, ?)",
                  (now, type_name, symptoms, diagnosis))
    else:
        c.execute("INSERT INTO plant_history (date, plant_type, symptoms, diagnosis) VALUES (?, ?, ?, ?)",
                  (now, type_name, symptoms, diagnosis))
    conn.commit()
    conn.close()

init_db()

# ==========================================
# ២. ការគ្រប់គ្រងទំហំរូបភាព (Image Optimization)
# ==========================================
def compress_image(uploaded_file):
    img = Image.open(uploaded_file)
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    img.thumbnail((1024, 1024))
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=80)
    buf.seek(0)
    return Image.open(buf)

# ==========================================
# ៣. ការរៀបចំទំព័រ UI ឱ្យមានស្តង់ដារ (UI/UX)
# ==========================================
st.set_page_config(page_title="ប្រព័ន្ធវិភាគ ដើមកសិកម្ម AI", page_icon="🌱", layout="centered")

# បន្ថែម CSS ដើម្បីរចនាប៊ូតុង និងពុម្ពអក្សរឱ្យមើលទៅទំនើប
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

# ផ្នែកក្បាល (Header)
st.title("🌱 ប្រព័ន្ធវិភាគ ដើមកសិកម្ម AI")
st.markdown("<p style='font-size: 16px; color: #555;'>ប្រព័ន្ធប្រើប្រាស់បញ្ញាសិប្បនិម្មិត (AI) ដើម្បីវិភាគ និងចេញសេចក្តីណែនាំព្យាបាលសត្វ និងដំណាំ។</p>", unsafe_allow_html=True)
st.divider()

api_key = st.secrets.get("GEMINI_API_KEY")

# ==========================================
# ៤. របារចំហៀង (Sidebar) ស្អាតបាត
# ==========================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/1892/1892751.png", width=100) # អាចប្តូរ Link រូប Logo អ្នកបាន
    st.header("⚙ ការកំណត់ប្រព័ន្ធ")
    if not api_key:
        api_key = st.text_input("បញ្ចូល Google Gemini API Key៖", type="password")
        st.caption("សូមកំណត់ GEMINI_API_KEY នៅក្នុង Streamlit Secrets ដើម្បលាក់ប្រអប់នេះ។")
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
            c.execute("SELECT date, animal_type FROM medical_history ORDER BY id DESC LIMIT 3")
        else:
            c.execute("SELECT date, plant_type FROM plant_history ORDER BY id DESC LIMIT 3")
            
        history = c.fetchall()
        for row in history:
            st.caption(f"🕒 {row[0]} - **{row[1]}**")
        conn.close()
    except Exception as e:
        st.caption("មិនទាន់មានប្រវត្តិទេ")

# ==========================================
# ៥. អនុគមន៍ហៅ AI
# ==========================================
def analyze_with_ai(target_type, symptoms, images, key, mode):
    client = genai.Client(api_key=key)
    if mode == "animal":
        prompt = f"""អ្នកគឺជាពេទ្យសត្វជំនាញប្រចាំហាង «ដើមកសិកម្ម»។ 
        សូមធ្វើការវិភាគ៖ ប្រភេទសត្វ៖ {target_type}, រោគសញ្ញា៖ {symptoms}
        ឆ្លើយតបជា៖ ១.ឈ្មោះជំងឺសង្ស័យ ២.ការវិភាគរូបភាព ៣.មូលហេតុ ៤.វិធីព្យាបាល និងថ្នាំ ៥.វិធានការការពារ។"""
    else:
        prompt = f"""អ្នកគឺជាអ្នកជំនាញក្សេត្រសាស្ត្រ ប្រចាំហាង «ដើមកសិកម្ម»។ 
        សូមធ្វើការវិភាគ៖ ប្រភេទដំណាំ៖ {target_type}, រោគសញ្ញា៖ {symptoms}
        ឆ្លើយតបជា៖ ១.ឈ្មោះជំងឺ/បញ្ហា ២.ការវិភាគរូបភាព ៣.មូលហេតុ ៤.វិធីសង្គ្រោះ/ថ្នាំ ៥.វិធានការការពារ។"""
        
    contents_list = [prompt]
    contents_list.extend(images) 
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=contents_list,
        config=types.GenerateContentConfig(temperature=0.2)
    )
    return response.text

# ==========================================
# ៦. ផ្ទាំងបញ្ចួលទិន្នន័យ (រចនាដោយប្រើ Tabs និង Containers)
# ==========================================
with st.container():
    if app_mode == "🩺 ផ្នែកពេទ្យសត្វ":
        st.subheader("១. បញ្ចូលព័ត៌មាន និងរោគសញ្ញាសត្វ")
        input_type = st.text_input("ប្រភេទសត្វ (ឧទាហរណ៍៖ មាន់, គោ, ជ្រូក...) ៖", placeholder="វាយបញ្ចូលទីនេះ...", key="animal_input")
        symptoms_input = st.text_area("រៀបរាប់ពីរោគសញ្ញា ឬអាការៈសត្វ៖", height=120, placeholder="ឧទាហរណ៍៖ សត្វអត់ស៊ីចំណី, ហៀរសំបោរ...", key="animal_symptoms")
        btn_text = "🔍 ចាប់ផ្តើមវិភាគជំងឺសត្វ"
        mode_flag = "animal"
    else:
        st.subheader("១. បញ្ចូលព័ត៌មាន និងរោគសញ្ញាដំណាំ")
        input_type = st.text_input("ប្រភេទដំណាំ (ឧទាហរណ៍៖ ស្រូវ, ស្វាយ, ម្រេច...) ៖", placeholder="វាយបញ្ចូលទីនេះ...", key="plant_input")
        symptoms_input = st.text_area("រៀបរាប់ពីរោគសញ្ញា៖", height=120, placeholder="ឧទាហរណ៍៖ ស្លឹកឡើងលឿងប្រឆុះ, មានដង្កូវសុីស្លឹក...", key="plant_symptoms")
        btn_text = "🔍 ចាប់ផ្តើមវិភាគជំងឺដំណាំ"
        mode_flag = "plant"

# រៀបចំកន្លែងដាក់រូបភាពជា Tabs ដើម្បីសន្សំសំចៃទំហំ
st.write("---")
st.subheader("📸 ២. បញ្ចូលរូបភាព (ជាការស្រេចចិត្ត)")
tab1, tab2 = st.tabs(["📷 ថតរូបផ្ទាល់ពីកាមេរ៉ា", "📁 ជ្រើសរើសពីរូបថតដែលមានស្រាប់"])

with tab1:
    camera_photo = st.camera_input("ថតរូបភាពទីនេះ៖")
with tab2:
    uploaded_files = st.file_uploader("ជ្រើសរើសរូបភាព (អាចរើសបានច្រើនសន្លឹក)៖", type=['png', 'jpg', 'jpeg', 'jfif', 'webp'], accept_multiple_files=True)

# ប្រមូល និងបង្ហាញរូបភាពដែលបានបញ្ចូល
all_photos = []
if camera_photo: all_photos.append(camera_photo)
if uploaded_files: all_photos.extend(uploaded_files)

optimized_images = []
if all_photos:
    st.success(f"ទទួលបានរូបភាពចំនួន {len(all_photos)} សន្លឹក")
    with st.expander("ចុចទីនេះដើម្បីមើលរូបភាពដែលបានបញ្ចូល", expanded=False):
        cols = st.columns(3) # ចែកជា ៣ ជួរដើម្បីកុំឱ្យរូបធំពេក
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
        st.warning("⚠ សូមរៀបរាប់ពីរោគសញ្ញា ឬបញ្ចួលរូបភាពយ៉ាងហោចណាស់មួយ!")
    else:
        with st.spinner("⏳ ប្រព័ន្ធ AI កំពុងធ្វើការវិភាគយ៉ាងយកចិត្តទុកដាក់... សូមរង់ចាំបន្តិច!"):
            try:
                # ហៅ AI និងរក្សាទុក
                result = analyze_with_ai(input_type, symptoms_input, optimized_images, api_key, mode_flag)
                save_history(input_type, symptoms_input, result, mode_flag)
                
                # បង្ហាញលទ្ធផលក្នុងប្រអប់ពណ៌ស្អាត
                st.success("✅ ការវិភាគទទួលបានជោគជ័យ!")
                
                with st.container(border=True):
                    st.subheader("វេជ្ជបញ្ជា និងសេចក្តីណែនាំ")
                    st.markdown(result)
                
                # ផ្នែកចម្លង និងទាញយក
                st.write("---")
                st.subheader("📋 ៣. ចម្លង និង នាំចេញឯកសារ")
                
                st.info("ចុចលើសញ្ញា 📋 នៅជ្រុងស្តាំនៃប្រអប់ខាងក្រោម ដើម្បី Copy យកទៅផ្ញើក្នុង Telegram ឬ Facebook។")
                st.code(result, language="markdown")
                
                st.download_button(
                    label="📥 ទាញយកជាឯកសារ (Download Text File)",
                    data=f"ប្រភេទ៖ {input_type}\nរោគសញ្ញា៖ {symptoms_input}\n\nលទ្ធផលវិភាគ៖\n{result}",
                    file_name=f"Diagnosis_{input_type}_{datetime.datetime.now().strftime('%Y%m%d')}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            
            except Exception as e:
                error_msg = str(e).lower()
                if "quota" in error_msg or "429" in error_msg:
                    st.error("❌ គណនី API របស់អ្នកបានប្រើប្រាស់អស់កូតាហើយ។")
                elif "api key" in error_msg or "401" in error_msg or "403" in error_msg:
                    st.error("❌ API Key របស់អ្នកមិនត្រឹមត្រូវទេ។")
                else:
                    st.error(f"❌ មានបញ្ហាមិនប្រក្រតី៖ {e}")
