import streamlit as st
from google import genai
from google.genai import types
from PIL import Image
import io
import sqlite3
import datetime

# ==========================================
# ១. ការកំណត់ Database (SQLite) រក្សាទុកប្រវត្តិ
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
    conn.commit()
    conn.close()

def save_history(animal, symptoms, diagnosis):
    conn = sqlite3.connect("vet_clinic.db")
    c = conn.cursor()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO medical_history (date, animal_type, symptoms, diagnosis) VALUES (?, ?, ?, ?)",
              (now, animal, symptoms, diagnosis))
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
# ៣. ការរៀបចំទំព័រ UI និង ការគ្រប់គ្រង API Key (Secrets)
# ==========================================
st.set_page_config(page_title="ប្រព័ន្ធវិភាគជំងឺ ដើមកសិកម្ម", page_icon="🩺", layout="centered")

st.title("🩺 ប្រព័ន្ធវិភាគជំងឺ ដើមកសិកម្ម")
st.markdown("**ប្រព័ន្ធស្តង់ដារ៖ ប្រើប្រាស់បញ្ញាសិប្បនិម្មិត (AI) ដើម្បីវិភាគ និងចេញសេចក្តីណែនាំព្យាបាល។**")
st.divider()

# ទាញយក API Key ពី Streamlit Secrets ដោយស្វ័យប្រវត្តិ
api_key = st.secrets.get("GEMINI_API_KEY")

with st.sidebar:
    st.header("⚙ ការកំណត់ប្រព័ន្ធ")
    # ប្រសិនបើមិនទាន់បានដាក់កូដសម្ងាត់ក្នុង Server ទេ វានឹងលោតប្រអប់ឱ្យវាយ (ទុកសម្រាប់ពេលសាកល្បងលើកុំព្យូទ័រ)
    if not api_key:
        api_key = st.text_input("បញ្ចូល Google Gemini API Key របស់អ្នក៖", type="password")
        st.caption("គន្លឹះ៖ សូមកំណត់ GEMINI_API_KEY នៅក្នុង Streamlit Secrets ដើម្បីលាក់ប្រអប់នេះ។")
    else:
        st.success("✅ ប្រព័ន្ធបានភ្ជាប់ API Key ស្វ័យប្រវត្តិរួចរាល់។")
    
    st.divider()
    st.markdown("### 📊 ប្រវត្តិវិភាគថ្មីៗ")
    try:
        conn = sqlite3.connect("vet_clinic.db")
        c = conn.cursor()
        c.execute("SELECT date, animal_type FROM medical_history ORDER BY id DESC LIMIT 3")
        history = c.fetchall()
        for row in history:
            st.caption(f"🕒 {row[0]} - **{row[1]}**")
        conn.close()
    except Exception as e:
        st.caption("មិនទាន់មានប្រវត្តិទេ")

# ==========================================
# ៤. កន្លែងបញ្ចូលព័ត៌មាន កាមេរ៉ា និងរូបភាព
# ==========================================
st.subheader("១. បញ្ចូលព័ត៌មាន និងរោគសញ្ញា")
animal_type = st.text_input("ប្រភេទសត្វ (ឧទាហរណ៍៖ មាន់, គោ, ជ្រូក...) ៖", placeholder="វាយបញ្ចូលទីនេះ...")
symptoms_input = st.text_area("រៀបរាប់ពីរោគសញ្ញា ឬអាការៈ៖", height=100)

st.write("---")
st.markdown("📸 **បញ្ចូលរូបភាពសត្វឈឺ (ជ្រើសរើសវិធីណាមួយក៏បាន)៖**")

# ៤.១ មុខងារថតរូបផ្ទាល់ពីទូរស័ព្ទ (Camera Input)
camera_photo = st.camera_input("ឬថតរូបភាពផ្ទាល់ពីកាមេរ៉ា៖")

# ៤.២ មុខងារ Upload រូបភាព (មានស្រាប់)
uploaded_files = st.file_uploader(
    "ឬជ្រើសរើសរូបភាពពីទូរស័ព្ទ (អាចរើសបានច្រើនសន្លឹក)៖", 
    type=['png', 'jpg', 'jpeg', 'jfif', 'webp'], 
    accept_multiple_files=True
)

# ប្រមូលរូបភាពទាំងអស់ចូលគ្នា (ទាំងថតផ្ទាល់ និង Upload)
all_photos = []
if camera_photo:
    all_photos.append(camera_photo)
if uploaded_files:
    all_photos.extend(uploaded_files)

# បង្ហាញរូបភាព និង បង្រួមទំហំ (Optimize)
optimized_images = []
if all_photos:
    st.write("🖼️ រូបភាពដែលនឹងត្រូវយកទៅវិភាគ៖")
    cols = st.columns(len(all_photos))
    for idx, file in enumerate(all_photos):
        compressed_img = compress_image(file)
        optimized_images.append(compressed_img)
        with cols[idx]:
            st.image(compressed_img, use_container_width=True)

# ==========================================
# ៥. អនុគមន៍វិភាគ
# ==========================================
def analyze_with_ai(animal, symptoms, images, key):
    client = genai.Client(api_key=key)
    
    prompt = f"""
    អ្នកគឺជាពេទ្យសត្វជំនាញប្រចាំហាង «ដើមកសិកម្ម»។ 
    សូមធ្វើការវិភាគ៖ ប្រភេទសត្វ៖ {animal}, រោគសញ្ញា៖ {symptoms}

    សូមឆ្លើយតបជារចនាសម្ព័ន្ធច្បាស់លាស់៖
    ១. **ឈ្មោះជំងឺសង្ស័យ** (ខ្មែរ/អង់គ្លេស និងភាគរយសង្ស័យ)
    ២. **ការវិភាគពីរូបភាព** (បើមានរូបភាព)
    ៣. **មូលហេតុចម្បង**
    ៤. **វិធីសាស្ត្រព្យាបាល និងសង្គ្រោះបន្ទាន់** (ឈ្មោះថ្នាំ និងរបៀបប្រើ)
    ៥. **វិធានការការពារ និងអនាម័យ**
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
# ៦. ការដំណើរការ និងលទ្ធផល (Output & Export)
# ==========================================
st.write("") 
if st.button("🔍 វិភាគរោគសញ្ញា និងរូបភាព", type="primary", use_container_width=True):
    if not api_key:
        st.error("⚠ សូមបញ្ចូល API Key នៅក្នុងផ្ទាំងកំណត់ (Sidebar) ឬកំណត់ក្នុង Secrets!")
    elif not animal_type.strip():
        st.warning("⚠ សូមបញ្ជាក់ប្រភេទសត្វ!")
    elif not symptoms_input.strip() and not all_photos:
        st.warning("⚠ សូមរៀបរាប់ពីរោគសញ្ញា ឬបញ្ចួលរូបភាពសត្វយ៉ាងហោចណាស់មួយ!")
    else:
        with st.spinner("⏳ AI កំពុងវិភាគរោគសញ្ញា និងរូបភាព..."):
            try:
                # ហៅ AI មកវិភាគ
                result = analyze_with_ai(animal_type, symptoms_input, optimized_images, api_key)
                
                # រក្សាទុកចូល Database
                save_history(animal_type, symptoms_input, result)
                
                st.success("ការវិភាគទទួលបានជោគជ័យ!")
                st.divider()
                st.subheader("២. លទ្ធផលនៃវេជ្ជបញ្ជា (ការវិភាគដោយ AI)")
                st.markdown(result)
                
                st.divider()
                st.subheader("៣. នាំចេញវេជ្ជបញ្ជា (Export Prescription)")
                
                st.download_button(
                    label="📥 ទាញយកវេជ្ជបញ្ជា (Text File)",
                    data=f"ប្រភេទសត្វ៖ {animal_type}\nរោគសញ្ញា៖ {symptoms_input}\n\nលទ្ធផលវិភាគ៖\n{result}",
                    file_name=f"Prescription_{animal_type}_{datetime.datetime.now().strftime('%Y%m%d')}.txt",
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
