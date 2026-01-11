import os
# --- BAGIAN PERBAIKAN IMAGEMAGICK (JANGAN DIHAPUS) ---
from moviepy.config import change_settings
# Pastikan jalur ini sesuai dengan lokasi instalasi di laptop Anda
# Jika error lagi, cek folder C:\Program Files\ImageMagick... Anda
change_settings({"IMAGEMAGICK_BINARY": r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"}) 
# -----------------------------------------------------

import yt_dlp
import whisper
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, concatenate_videoclips
from moviepy.video.fx.all import crop, resize
import textwrap

# --- PENGATURAN PENGGUNA (EDIT DI SINI) ---
PAKAI_SUBTITLE = True        # Ubah ke False jika ingin video bersih
GAYA_VERTIKAL = True         # True = 9:16 (TikTok)
MAX_DURASI_DETIK = 58        # Stop otomatis di 58 detik
NAMA_FILE_HASIL = "video_tiktok_viral.mp4"

# --- PENGATURAN TAMPILAN (Modern Style) ---
FONT_UKURAN = 60
FONT_WARNA = 'yellow'
FONT_STROKE_WARNA = 'black'
FONT_STROKE_TEBAL = 3

def download_video(url):
    print("\n[1/4] 📥 Sedang mendownload video...")
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': 'bahan_mentah.%(ext)s',
        'overwrites': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return "bahan_mentah.mp4"

def transkripsi_audio():
    print("\n[2/4] 🤖 AI sedang mendengarkan & mencari momen penting...")
    model = whisper.load_model("base") 
    result = model.transcribe("bahan_mentah.mp4")
    return result['segments']

def buat_klip_vertikal(clip):
    # Logika crop 9:16
    w, h = clip.size
    clip_resized = clip.resize(height=1920)
    new_w, new_h = clip_resized.size
    center_x = new_w / 2
    crop_width = 1080 
    
    clip_cropped = clip_resized.crop(
        x1=center_x - (crop_width / 2),
        y1=0,
        width=crop_width,
        height=new_h
    )
    return clip_cropped

def proses_video_tiktok(segments):
    print("\n[3/4] ✂️ Memotong, Mengedit & Menambah Efek Modern...")
    
    video = VideoFileClip("bahan_mentah.mp4")
    clips_final = []
    durasi_total_saat_ini = 0
    
    for segment in segments:
        start = segment['start']
        end = segment['end']
        text = segment['text'].strip()
        durasi_segmen = end - start
        
        if durasi_total_saat_ini + durasi_segmen > MAX_DURASI_DETIK:
            print(f"   ⚠️ Batas durasi tercapai ({int(durasi_total_saat_ini)} detik).")
            break
        
        # Potong Video
        subclip = video.subclip(start, end)
        
        if GAYA_VERTIKAL:
            subclip = buat_klip_vertikal(subclip)
            
        # Tambah Subtitle
        if PAKAI_SUBTITLE and len(text) > 0:
            wrapper = textwrap.TextWrapper(width=20) 
            text_wrapped = "\n".join(wrapper.wrap(text))
            
            # TextClip MoviePy 1.0.3 (Parameter agak beda dgn versi baru)
            txt_clip = (TextClip(text_wrapped, fontsize=FONT_UKURAN, color=FONT_WARNA, 
                                font='Arial-Bold', stroke_color=FONT_STROKE_WARNA, stroke_width=FONT_STROKE_TEBAL, 
                                method='caption', size=(subclip.w*0.9, None))
                        .set_position(('center', 0.75), relative=True)
                        .set_duration(subclip.duration))
            
            subclip = CompositeVideoClip([subclip, txt_clip])
            
        clips_final.append(subclip)
        durasi_total_saat_ini += durasi_segmen
        print(f"   ✅ Ambil segmen: {text[:20]}...")

    if len(clips_final) > 0:
        print("\n[4/4] 🚀 Merender Video Final (Sabar ya, ini proses berat)...")
        final_video = concatenate_videoclips(clips_final)
        # Tambahkan audio_codec='aac' agar suara keluar di HP
        final_video.write_videofile(NAMA_FILE_HASIL, codec='libx264', audio_codec='aac', fps=24)
        print(f"\n🎉 SUKSES BESAR! Video Anda siap: {NAMA_FILE_HASIL}")
    else:
        print("❌ Tidak ada segmen suara yang ditemukan.")

    video.close()

if __name__ == "__main__":
    # --- GANTI LINK DI SINI YA ---
    URL_TARGET = "https://youtu.be/tNQ3URZ9hF4?si=7m9qMohmJOVm8CIg" 
    
    download_video(URL_TARGET)
    hasil_transkripsi = transkripsi_audio()
    proses_video_tiktok(hasil_transkripsi)