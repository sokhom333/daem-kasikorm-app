import streamlit as st
from google import genai
from google.genai import types
from PIL import Image
import io
import sqlite3
import datetime

# ==========================================
# ១. ការកំណត់ Database រក្សាទុកប្រវត្តិ (សត្វ និង ដំណាំ)
# ==========================================
def init_db():
    conn = sqlite3.connect("vet_clinic.db")
    c = conn.cursor()
    # តារាងសម្រាប់ប្រវត្តិសត្វ
    c.execute('''
        CREATE TABLE IF NOT EXISTS medical_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            animal_type TEXT,
            symptoms TEXT,
            diagnosis TEXT
        )
    ''')
    # តារាងថ្មីសម្រាប់ប្រវត្តិដំណាំ
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
# ៣. ការរៀបចំទំព័រ UI និង ការគ្រប់គ្រង API Key
# ==========================================
st.set_page_config(page_title="ប្រព័ន្ធវិភាគ ដើមកសិកម្ម", page_icon="🌱", layout="centered")

st.title("🌱ប្រព័ន្ធវិភាគ ដើមកសិកម្ម AI")
st.markdown("**ប្រព័ន្ធប្រើប្រាស់បញ្ញាសិប្បនិម្មិត (AI) ដើម្បីវិភាគ និងចេញសេចក្តីណែនាំព្យាបាលសត្វ និងដំណាំ។**")
st.divider()

api_key = st.secrets.get("GEMINI_API_KEY")

with st.sidebar:
    st.header("⚙ ការកំណត់ប្រព័ន្ធ")
    if not api_key:
        api_key = st.text_input("បញ្ចូល Google Gemini API Key របស់អ្នក៖", type="password")
        st.caption("គន្លឹះ៖ សូមកំណត់ GEMINI_API_KEY នៅក្នុង Streamlit Secrets ដើម្បីលាក់ប្រអប់នេះ។")
    else:
        st.success("✅ ប្រព័ន្ធបានភ្ជាប់ API Key ស្វ័យប្រវត្តិរួចរាល់។")
    
    st.divider()
    # បន្ថែមម៉ឺនុយសម្រាប់ជ្រើសរើសផ្នែក
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
# ៤. អនុគមន៍ហៅ AI មកវិភាគ (Dynamic Prompt តាមផ្នែក)
# ==========================================
def analyze_with_ai(target_type, symptoms, images, key, mode):
    client = genai.Client(api_key=key)
    
    if mode == "animal":
        prompt = f"""
        អ្នកគឺជាពេទ្យសត្វជំនាញប្រចាំហាង «ដើមកសិកម្ម»។ 
        សូមធ្វើការវិភាគ៖ ប្រភេទសត្វ៖ {target_type}, រោគសញ្ញា៖ {symptoms}

        សូមឆ្លើយតបជារចនាសម្ព័ន្ធច្បាស់លាស់៖
        ១. **ឈ្មោះជំងឺសង្ស័យ** (ខ្មែរ/អង់គ្លេស និងភាគរយសង្ស័យ)
        ២. **ការវិភាគពីរូបភាព** (បើមានរូបភាព)
        ៣. **មូលហេតុចម្បង**
        ៤. **វិធីសាស្ត្រព្យាបាល និងសង្គ្រោះបន្ទាន់** (ឈ្មោះថ្នាំ និងរបៀបប្រើ)
        ៥. **វិធានការការពារ និងអនាម័យ**
        """
    else:
        prompt = f"""
        អ្នកគឺជាអ្នកជំនាញក្សេត្រសាស្ត្រ និងរោគវិទ្យារុក្ខជាតិ ប្រចាំហាង «ដើមកសិកម្ម»។ 
        សូមធ្វើការវិភាគ៖ ប្រភេទដំណាំ៖ {target_type}, រោគសញ្ញា/អាការៈ៖ {symptoms}

        សូមឆ្លើយតបជារចនាសម្ព័ន្ធច្បាស់លាស់៖
        ១. **ឈ្មោះជំងឺ ឬបញ្ហាសង្ស័យ** (ឧទាហរណ៍៖ ជំងឺផ្សិត, ខ្វះជី, សត្វល្អិតបំផ្លាញ - បញ្ជាក់ភាគរយសង្ស័យ)
        ២. **ការវិភាគពីរូបភាព** (បើមានរូបភាព)
        ៣. **មូលហេតុចម្បង** (តើបណ្តាលមកពីអ្វី?)
        ៤. **វិធីសាស្ត្រសង្គ្រោះ និងព្យាបាល** (ឈ្មោះថ្នាំកសិកម្មប្រភេទអ្វី ជីបំប៉នអ្វី និងរបៀបប្រើប្រាស់/បាញ់ថ្នាំ)
        ៥. **វិធានការការពារ និងថែទាំ** (ការរៀបចំដី ការស្រោចទឹកជាដើម)
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
# ៥. កន្លែងបញ្ចួលទិន្នន័យ និងបង្ហាញលទ្ធផល (ប្តូរតាមម៉ឺនុយ)
# ==========================================

# ៥.១ មុខងារថតរូប/Upload (ប្រើរួមគ្នាបាន)
st.markdown("📸 **បញ្ចួលរូបភាព (ជ្រើសរើសវិធីណាមួយក៏បាន)៖**")
camera_photo = st.camera_input("ឬថតរូបភាពផ្ទាល់ពីកាមេរ៉ា៖")
uploaded_files = st.file_uploader(
    "ឬជ្រើសរើសរូបភាពពីទូរស័ព្ទ (អាចរើសបានច្រើនសន្លឹក)៖", 
    type=['png', 'jpg', 'jpeg', 'jfif', 'webp'], 
    accept_multiple_files=True
)

all_photos = []
if camera_photo:
    all_photos.append(camera_photo)
if uploaded_files:
    all_photos.extend(uploaded_files)

optimized_images = []
if all_photos:
    st.write("🖼️ រូបភាពដែលនឹងត្រូវយកទៅវិភាគ៖")
    cols = st.columns(len(all_photos))
    for idx, file in enumerate(all_photos):
        compressed_img = compress_image(file)
        optimized_images.append(compressed_img)
        with cols[idx]:
            st.image(compressed_img, use_container_width=True)
            
st.write("---")

# ៥.២ ផ្ទាំងបញ្ចូលព័ត៌មាន និងប៊ូតុងវិភាគ (ចែកតាមម៉ឺនុយ)
if app_mode == "🩺 ផ្នែកពេទ្យសត្វ":
    st.subheader("១. បញ្ចូលព័ត៌មាន និងរោគសញ្ញាសត្វ")
    input_type = st.text_input("ប្រភេទសត្វ (ឧទាហរណ៍៖ មាន់, គោ, ជ្រូក...) ៖", key="animal_input")
    symptoms_input = st.text_area("រៀបរាប់ពីរោគសញ្ញា ឬអាការៈសត្វ៖", height=100, key="animal_symptoms")
    btn_text = "🔍 វិភាគជំងឺសត្វ"
    mode_flag = "animal"
    
else:
    st.subheader("១. បញ្ចូលព័ត៌មាន និងរោគសញ្ញាដំណាំ")
    input_type = st.text_input("ប្រភេទដំណាំ (ឧទាហរណ៍៖ ស្រូវ, ស្វាយ, ម្រេច, ស្ពៃក្តោប...) ៖", key="plant_input")
    symptoms_input = st.text_area("រៀបរាប់ពីរោគសញ្ញា (ឧទាហរណ៍៖ ស្លឹកឡើងលឿងប្រឆុះ, មានដង្កូវ, ដើមរលួយ...) ៖", height=100, key="plant_symptoms")
    btn_text = "🔍 វិភាគជំងឺដំណាំ"
    mode_flag = "plant"

if st.button(btn_text, type="primary", use_container_width=True):
    if not api_key:
        st.error("⚠ សូមបញ្ចូល API Key នៅក្នុងផ្ទាំងកំណត់ (Sidebar) ឬកំណត់ក្នុង Secrets!")
    elif not input_type.strip():
        st.warning("⚠ សូមបញ្ជាក់ប្រភេទសត្វ/ដំណាំ!")
    elif not symptoms_input.strip() and not all_photos:
        st.warning("⚠ សូមរៀបរាប់ពីរោគសញ្ញា ឬបញ្ចួលរូបភាពយ៉ាងហោចណាស់មួយ!")
    else:
        with st.spinner("⏳ AI កំពុងវិភាគរោគសញ្ញា និងរូបភាព..."):
            try:
                # ហៅ AI មកវិភាគ
                result = analyze_with_ai(input_type, symptoms_input, optimized_images, api_key, mode_flag)
                
                # រក្សាទុកចូល Database
                save_history(input_type, symptoms_input, result, mode_flag)
                
                st.success("ការវិភាគទទួលបានជោគជ័យ!")
                st.divider()
                st.subheader("២. លទ្ធផលនៃការវិភាគដោយ AI")
                st.markdown(result)
                
                st.divider()
                st.subheader("៣. នាំចេញវេជ្ជបញ្ជា/ឯកសារណែនាំ (Export)")
                
                st.download_button(
                    label="📥 ទាញយកឯកសារ (Text File)",
                    data=f"ប្រភេទ៖ {input_type}\nរោគសញ្ញា៖ {symptoms_input}\n\nលទ្ធផលវិភាគ៖\n{result}",
                    file_name=f"Diagnosis_{input_type}_{datetime.datetime.now().strftime('%Y%m%d')}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            
            except Exception as e:
                error_msg = str(e).lower()
                if "quota" in error_msg or "429" in error_msg:
                    st.error("❌ បរាជ័យ៖ គណនី API របស់អ្នកបានប្រើប្រាស់អស់កូតា (Quota Exceeded)។")
                elif "api key" in error_msg or "401" in error_msg or "403" in error_msg:
                    st.error("❌ បរាជ័យ៖ API Key របស់អ្នកមិនត្រឹមត្រូវទេ។")
                else:
                    st.error(f"❌ មានបញ្ហាមិនប្រក្រតី៖ {e}")
