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

# ដំណើរការបង្កើត Database ពេលបើកកម្មវិធី
init_db()

# ==========================================
# ២. ការគ្រប់គ្រងទំហំរូបភាព (Image Optimization)
# ==========================================
def compress_image(uploaded_file):
    img = Image.open(uploaded_file)
    # បម្លែងទៅជា RGB ការពារ Error ពេលរូបភាពមានទម្រង់ RGBA (PNG ថ្លា)
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # បង្រួមទំហំ (Resize) ត្រឹម 1024px ដើម្បីរក្សាគុណភាព តែទំហំតូច (ជួយឱ្យ Upload លឿន)
    img.thumbnail((1024, 1024))
    
    # សង្កត់ទំហំ (Compress) និងបម្លែងជា Bytes វិញ
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=80)
    buf.seek(0)
    return Image.open(buf)

# ==========================================
# ៣. ការរៀបចំទំព័រ UI
# ==========================================
st.set_page_config(page_title="ប្រព័ន្ធវិភាគជំងឺ ដើមកសិកម្ម", page_icon="🩺", layout="centered")

st.title("🩺 ប្រព័ន្ធវិភាគជំងឺ ដើមកសិកម្ម")
st.markdown("**ប្រព័ន្ធស្តង់ដារ៖ ប្រើប្រាស់បញ្ញាសិប្បនិម្មិត (AI) ដើម្បីវិភាគ និងចេញសេចក្តីណែនាំព្យាបាល។**")
st.divider()

# លាក់ API Key (ដើម្បីសុវត្ថិភាព អាចដកចេញពី Sidebar ហើយដាក់ក្នុង st.secrets បាននៅពេលអនាគត)
with st.sidebar:
    st.header("⚙ ការកំណត់ប្រព័ន្ធ")
    api_key = st.text_input("បញ្ចូល Google Gemini API Key:", type="password")
    
    st.divider()
    st.markdown("### 📊 ប្រវត្តិវិភាគថ្មីៗ")
    # បង្ហាញប្រវត្តិពី Database បន្តិចបន្តួច
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
# ៤. កន្លែងបញ្ចូលព័ត៌មានសត្វ និងរូបភាព
# ==========================================
st.subheader("១. បញ្ចូលព័ត៌មាន និងរោគសញ្ញា")
animal_type = st.text_input("ប្រភេទសត្វ (ឧទាហរណ៍៖ មាន់, គោ, ជ្រូក...) ៖", placeholder="វាយបញ្ចូលទីនេះ...")
symptoms_input = st.text_area("រៀបរាប់ពីរោគសញ្ញា ឬអាការៈ៖", height=100)

# កន្លែងដែលបានអាប់ដេតបន្ថែមប្រភេទរូបភាព '.jfif' និង '.webp'
uploaded_files = st.file_uploader(
    "បញ្ចូលរូបភាពសត្វឈឺ (អាចជ្រើសរើសបានច្រើនសន្លឹក)៖", 
    type=['png', 'jpg', 'jpeg', 'jfif', 'webp'], 
    accept_multiple_files=True
)

# បង្ហាញរូបភាព និង បង្រួមទំហំ (Optimize)
optimized_images = []
if uploaded_files:
    st.write("🖼️ រូបភាពដែលបានបង្រួមទំហំួច៖")
    cols = st.columns(len(uploaded_files))
    for idx, file in enumerate(uploaded_files):
        compressed_img = compress_image(file)
        optimized_images.append(compressed_img)
        with cols[idx]:
            st.image(compressed_img, use_container_width=True)

# ==========================================
# ៥. អនុគមន៍វិភាគ និង ការគ្រប់គ្រងកំហុស (Error Handling)
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
    contents_list.extend(images) # បញ្ចូលរូបភាពដែល Optimize រួច
    
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
        st.error("⚠ សូមបញ្ចូល API Key នៅក្នុងផ្ទាំងកំណត់ (Sidebar)!")
    elif not animal_type.strip():
        st.warning("⚠ សូមបញ្ជាក់ប្រភេទសត្វ!")
    elif not symptoms_input.strip() and not uploaded_files:
        st.warning("⚠ សូមរៀបរាប់ពីរោគសញ្ញា ឬបញ្ចួលរូបភាពសត្វយ៉ាងហោចណាស់មួយ!")
    else:
        with st.spinner("⏳ AI កំពុងវិភាគរោគសញ្ញា និងរូបភាព..."):
            try:
                # ហៅ AI មកវិភាគ
                result = analyze_with_ai(animal_type, symptoms_input, optimized_images, api_key)
                
                # រក្សាទុកចូល Database (History)
                save_history(animal_type, symptoms_input, result)
                
                st.success("ការវិភាគទទួលបានជោគជ័យ និងបានរក្សាទុកក្នុងប្រព័ន្ធរួចរាល់!")
                st.divider()
                st.subheader("២. លទ្ធផលនៃវេជ្ជបញ្ជា (ការវិភាគដោយ AI)")
                st.markdown(result)
                
                st.divider()
                st.subheader("៣. នាំចេញវេជ្ជបញ្ជា (Export Prescription)")
                
                # មុខងារទាញយកឯកសារជា Text សម្រាប់ផ្ញើតាម Telegram ឬ រក្សាទុក
                st.download_button(
                    label="📥 ទាញយកវេជ្ជបញ្ជា (Text File)",
                    data=f"ប្រភេទសត្វ៖ {animal_type}\nរោគសញ្ញា៖ {symptoms_input}\n\nលទ្ធផលវិភាគ៖\n{result}",
                    file_name=f"Prescription_{animal_type}_{datetime.datetime.now().strftime('%Y%m%d')}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
                
                st.info("💡 គន្លឹះ៖ លោកអ្នកអាចចុច `Ctrl + P` (ឬ Cmd + P លើ Mac) នៅលើ Browser ដើម្បី Print វេជ្ជបញ្ជានេះជា PDF ឬបោះពុម្ពចេញម៉ាស៊ីនផ្ទាល់តែម្តង។")

            # ការចាប់ Error ច្បាស់លាស់ជាភាសាខ្មែរ (Robust Error Handling)
            except Exception as e:
                error_msg = str(e).lower()
                if "quota" in error_msg or "429" in error_msg:
                    st.error("❌ បរាជ័យ៖ គណនី API របស់អ្នកបានប្រើប្រាស់អស់កូតា (Quota Exceeded) ឬមានអ្នកប្រើច្រើនពេក។ សូមរង់ចាំបន្តិច រួចសាកល្បងម្តងទៀត។")
                elif "api key" in error_msg or "401" in error_msg or "403" in error_msg:
                    st.error("❌ បរាជ័យ៖ API Key របស់អ្នកមិនត្រឹមត្រូវទេ។ សូមពិនិត្យមើលអក្ខរាវិរុទ្ធឡើងវិញ។")
                elif "network" in error_msg or "connection" in error_msg:
                    st.error("❌ បរាជ័យ៖ ដាច់អ៊ីនធឺណិត ឬមិនអាចភ្ជាប់ទៅកាន់ប្រព័ន្ធ AI បានទេ។ សូមពិនិត្យប្រព័ន្ធ WiFi។")
                else:
                    st.error(f"❌ មានបញ្ហាមិនប្រក្រតី៖ {e}")