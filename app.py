import streamlit as st
import os
import time
import yt_dlp
import whisper
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, CompositeAudioClip, concatenate_videoclips, afx
from moviepy.config import change_settings
import textwrap

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Clipper MSR", page_icon="🎬", layout="wide")

# CSS Modern (Neon & Glassmorphism)
st.markdown("""
    <style>
    .stApp { background: linear-gradient(to right, #00CED1, #141E30); color: yellow; }
    .stButton>button {
        background: linear-gradient(90deg, #00d2ff 0%, #3a7bd5 100%);
        color: yellow; border: none; height: 3em; border-radius: 8px; font-weight: bold;
    }
    .stButton>button:hover { transform: scale(1.02); box-shadow: 0 0 15px rgba(0, 210, 255, 0.6); }
    h1 { text-align: center; color: #00d2ff; text-shadow: 0 0 10px rgba(0,210,255,0.5); }
    .history-card { background: rgba(255,255,255,0.1); padding: 10px; border-radius: 10px; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SETTING IMAGEMAGICK (WAJIB WINDOWS) ---
change_settings({"IMAGEMAGICK_BINARY": r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"}) 

# --- 3. SIDEBAR (RIWAYAT & SETTING) ---
with st.sidebar:
    st.header("⚙️ Setting")
    
    # --- FITUR RIWAYAT (BARU) ---
    with st.expander("📂 Riwayat Video", expanded=True):
        # Scan folder untuk file hasil
        files = [f for f in os.listdir('.') if f.endswith('.mp4') and "Hasil_Part" in f]
        files.sort(key=lambda x: os.path.getmtime(x), reverse=True) # Urutkan dari yang terbaru
        
        if not files:
            st.caption("Belum ada riwayat.")
        else:
            st.write(f"Terdeteksi {len(files)} video:")
            for f in files:
                st.markdown(f"<div class='history-card'>🎥 {f}</div>", unsafe_allow_html=True)
                with open(f, "rb") as vid_file:
                    st.download_button(f"⬇️ {f}", data=vid_file, file_name=f, key=f"dl_{f}")
            
            st.markdown("---")
            if st.button("🗑️ Hapus Semua Riwayat"):
                for f in files:
                    try:
                        os.remove(f)
                    except: pass
                st.experimental_rerun()

    st.markdown("---")
    st.caption("Edit ")
    pakai_subs = st.checkbox("Pakai Subtitle", value=True)
    font_color = st.color_picker("Warna Font", "#FFFF00")
    
    st.caption("🧠 AI Model")
    bahasa_ai = st.selectbox("Bahasa", ["id", "en"])

# --- 4. ENGINE ---
def process_video(source, duration, parts, bg_music_file, vol_music):
    st.info("🔮 AI sedang bekerja... Mohon tunggu.")
    
    # 1. Transkrip
    model = whisper.load_model("base")
    result = model.transcribe(source, language=bahasa_ai)
    
    full_video = VideoFileClip(source)
    
    # 2. Audio Background
    bg_audio = None
    if bg_music_file:
        with open("temp_music.mp3", "wb") as f:
            f.write(bg_music_file.getbuffer())
        bg_audio = AudioFileClip("temp_music.mp3").fx(afx.volumex, vol_music)

    # 3. Cutting Logic
    bucket = []
    bucket_dur = 0
    part_idx = 1
    generated = []

    for seg in result['segments']:
        seg_dur = seg['end'] - seg['start']
        
        if bucket_dur + seg_dur > duration:
            if bucket:
                fname = render(full_video, bucket, part_idx, bg_audio)
                generated.append(fname)
                part_idx += 1
                bucket = []
                bucket_dur = 0
                if part_idx > parts: break
        
        bucket.append(seg)
        bucket_dur += seg_dur

    if bucket and part_idx <= parts:
        fname = render(full_video, bucket, part_idx, bg_audio)
        generated.append(fname)
        
    full_video.close()
    return generated

def render(video, segments, idx, bg_audio):
    clips = []
    font_size = 55
    
    for s in segments:
        sub = video.subclip(s['start'], s['end'])
        # 9:16 Crop
        sub = sub.resize(height=1920)
        sub = sub.crop(x1=sub.w/2 - 540, y1=0, width=1080, height=1920)
        
        if pakai_subs:
            txt = "\n".join(textwrap.wrap(s['text'].strip(), 20))
            txt_clip = (TextClip(txt, fontsize=font_size, color=font_color, font='Arial-Bold', 
                                 stroke_color='black', stroke_width=3, method='caption', size=(900, None))
                        .set_position(('center', 0.7), relative=True).set_duration(sub.duration))
            sub = CompositeVideoClip([sub, txt_clip])
        clips.append(sub)
        
    final = concatenate_videoclips(clips)
    if bg_audio:
        loop_bg = afx.audio_loop(bg_audio, duration=final.duration)
        final = final.set_audio(CompositeAudioClip([final.audio, loop_bg]))
        
    name = f"Hasil_Part_{idx}_{int(time.time())}.mp4" # Pakai timestamp biar unik
    final.write_videofile(name, codec='libx264', audio_codec='aac', fps=24, preset='ultrafast')
    return name

# --- 5. UI UTAMA ---
st.title("🎬 MSR AI CLIPPER")

tab1, tab2 = st.tabs(["YouTube", "Upload File"])
src = ""
is_yt = False

with tab1:
    url = st.text_input("Link YouTube")
    if url: is_yt = True
with tab2:
    upl = st.file_uploader("Upload MP4", type='mp4')
    if upl:
        with open("temp_src.mp4", "wb") as f: f.write(upl.getbuffer())
        src = "temp_src.mp4"

col1, col2 = st.columns(2)
durn = col1.slider("Durasi per Part (detik)", 15, 60, 55)
max_p = col2.number_input("Max Part", 1, 10, 3)

bg_music = st.sidebar.file_uploader("Musik Latar (MP3)", type='mp3')
vol = st.sidebar.slider("Volume Musik", 0.1, 1.0, 0.2)

if st.button("🚀 PROSES SEKARANG"):
    if is_yt:
        st.info("Downloading...")
        with yt_dlp.YoutubeDL({'format': 'best[ext=mp4]', 'outtmpl': 'temp_yt.%(ext)s', 'overwrites':True}) as ydl:
            ydl.download([url])
        src = "temp_yt.mp4"
    
    if src:
        res = process_video(src, durn, max_p, bg_music, vol)
        st.success("Selesai!")
        st.experimental_rerun() # Refresh biar riwayat muncul
    else:
        st.error("Input kosong!")