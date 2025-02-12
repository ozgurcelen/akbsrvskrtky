import streamlit as st
import json
import os
import time
import threading
from datetime import datetime
import folium
from streamlit_folium import st_folium
import pandas as pd

# 📌 Dosya yolları
JSON_FILE = "kullanicilar.json"
DURUM_FILE = "durumlar.json"

# 📌 Eğer dosyalar yoksa oluştur
if not os.path.exists(JSON_FILE):
    with open(JSON_FILE, "w") as f:
        json.dump([], f)

if not os.path.exists(DURUM_FILE):
    with open(DURUM_FILE, "w") as f:
        json.dump({}, f)

# 📌 Kullanıcıları yükle
def load_users():
    with open(JSON_FILE, "r") as f:
        return json.load(f)

def load_durumlar():
    with open(DURUM_FILE, "r") as f:
        return json.load(f)

# 📌 Kullanıcıları pasif hale getiren fonksiyon
def reset_durumlar():
    try:
        with open(DURUM_FILE, "r") as f:
            durumlar = json.load(f)
        
        for key in durumlar.keys():
            durumlar[key] = False

        with open(DURUM_FILE, "w") as f:
            json.dump(durumlar, f, indent=4)

        print("✅ Tüm kullanıcılar pasif hale getirildi.")
    except Exception as e:
        print(f"❌ Hata oluştu: {e}")

# 📌 Sidebar Menüsü
st.sidebar.title("📌 Menü")
sayfa = st.sidebar.radio("Seçenekler:", ["Haritayı Göster", "Kayıt Ol", "Durum Güncelle", "Aktif Kullanıcılar", "Kullanıcı Düzenle", "Sistem Ayarları"])

# **Haritayı Göster Sayfası**
if sayfa == "Haritayı Göster":
    st.title("📍 Bugün Servis Kullanacaklar (Sadece Bugün Kullanıcılar)")

    kullanicilar = load_users()
    durumlar = load_durumlar()

    # Sadece aktif olanları filtrele
    aktif_kullanicilar = [k for k in kullanicilar if durumlar.get(k["ad"], False)]

    m = folium.Map(location=[40.934444429879434, 29.32820863673836], zoom_start=13)

    for k in aktif_kullanicilar:
        folium.Marker(
            location=[k["lat"], k["lon"]],
            popup=f"{k['ad']} {k['soyad']}",
            icon=folium.Icon(color="green")  # Aktif olanları yeşil gösterelim
        ).add_to(m)

    st_folium(m, width=800, height=500)

    if not aktif_kullanicilar:
        st.warning("❗ Şu anda aktif olan kullanıcı bulunmamaktadır.")


# **Kayıt Ol Sayfası**
# **Kayıt Ol Sayfası**
elif sayfa == "Kayıt Ol":
    st.title("📝 Kayıt Ol")

    # **Session State Kullanımı**
    if "ad" not in st.session_state:
        st.session_state.ad = ""
    if "soyad" not in st.session_state:
        st.session_state.soyad = ""
    if "telefon" not in st.session_state:
        st.session_state.telefon = ""
    if "koordinat" not in st.session_state:
        st.session_state.koordinat = "40.934444429879434, 29.32820863673836"

    ad = st.text_input("Adınız", st.session_state.ad)
    soyad = st.text_input("Soyadınız", st.session_state.soyad)
    telefon = st.text_input("Telefon Numaranız", st.session_state.telefon)
    koordinat = st.text_input("Koordinatlar (Enlem, Boylam)", st.session_state.koordinat)

    if st.button("Kaydol"):
        try:
            lat, lon = map(float, koordinat.split(","))

            # Kullanıcıları yükle ve ekle
            users = load_users()
            users.append({"ad": ad, "soyad": soyad, "telefon": telefon, "lat": lat, "lon": lon})
            with open(JSON_FILE, "w") as f:
                json.dump(users, f, indent=4)

            # Kullanıcının durumunu varsayılan olarak pasif ekle
            durumlar = load_durumlar()
            durumlar[ad] = False  
            with open(DURUM_FILE, "w") as f:
                json.dump(durumlar, f, indent=4)

            # **Kayıt Başarılı! Formu Sıfırla**
            st.session_state.ad = ""
            st.session_state.soyad = ""
            st.session_state.telefon = ""
            st.session_state.koordinat = "40.934444429879434, 29.32820863673836"

            st.success(f"✅ {ad} {soyad}, başarıyla kayıt oldunuz!")
        except ValueError:
            st.error("❌ Hatalı koordinat formatı!")


# **Durum Güncelleme Sayfası**
elif sayfa == "Durum Güncelle":
    st.title("🔴🟢 Kullanıcı Durumu Güncelle")

    kullanicilar = load_users()
    durumlar = load_durumlar()

    if not kullanicilar:
        st.warning("Henüz kayıtlı kimse yok.")
    else:
        for k in kullanicilar:
            ad = k["ad"]
            mevcut_durum = durumlar.get(ad, False)

            if st.button(f"{ad} - {'🟢 Aktif' if mevcut_durum else '🔴 Pasif'}", key=f"durum_{ad}"):
                durumlar[ad] = not mevcut_durum
                with open(DURUM_FILE, "w") as f:
                    json.dump(durumlar, f, indent=4)
                st.rerun()

# **Aktif Kullanıcıları Listeleme Sayfası**
elif sayfa == "Aktif Kullanıcılar":
    st.title("🟢 Aktif Kullanıcılar")

    kullanicilar = load_users()
    durumlar = load_durumlar()

     # 🔥 **Aktif kullanıcıları filtreleme**
    aktif_kullanicilar = [k for k in kullanicilar if durumlar.get(k["ad"], False)]
    aktif_kullanicilar = sorted(aktif_kullanicilar, key=lambda k: k['lat'])


    
    if not aktif_kullanicilar:
        st.warning("Henüz aktif olan kullanıcı yok.")
    else:
        df = pd.DataFrame(aktif_kullanicilar)
        st.write(df)

        # **Google Haritalar yönlendirme**
        if len(aktif_kullanicilar) > 1:
            baslangic = f"{aktif_kullanicilar[0]['lat']},{aktif_kullanicilar[0]['lon']}"  # Güneydeki en küçük enlem
            destination = f"{aktif_kullanicilar[-1]['lat']},{aktif_kullanicilar[-1]['lon']}"  # Kuzeydeki en büyük enlem
            waypoints = "|".join([f"{k['lat']},{k['lon']}" for k in aktif_kullanicilar[1:-1]])  # Başlangıç ve varış hariç
            maps_url = f"https://www.google.com/maps/dir/?api=1&origin={baslangic}&destination={destination}&waypoints={waypoints}"
            st.markdown(f"[📍 Google Haritalar'da Aç]({maps_url})", unsafe_allow_html=True)

# **Kullanıcı Düzenleme Sayfası**
elif sayfa == "Kullanıcı Düzenle":
    st.title("📝 Kullanıcı Düzenleme")

    kullanicilar = load_users()

    if not kullanicilar:
        st.warning("Henüz kayıtlı kimse yok.")
    else:
        for k in kullanicilar:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"**{k['ad']} {k['soyad']}** - {k['telefon']}")
            with col2:
                if st.button("Düzenle", key=f"edit_{k['ad']}"):
                    st.session_state["edit_user"] = k
            with col3:
                if st.button("Sil", key=f"delete_{k['ad']}"):
                    kullanicilar = [u for u in kullanicilar if u["ad"] != k["ad"]]
                    with open(JSON_FILE, "w") as f:
                        json.dump(kullanicilar, f, indent=4)
                    st.rerun()

        if "edit_user" in st.session_state:
            st.subheader("🔄 Kullanıcı Bilgilerini Güncelle")
            edit_data = st.session_state["edit_user"]
            ad = st.text_input("Adınız", edit_data["ad"])
            soyad = st.text_input("Soyadınız", edit_data["soyad"])
            telefon = st.text_input("Telefon Numaranız", edit_data["telefon"])
            koordinat = st.text_input("Koordinatlar (Enlem, Boylam)", f"{edit_data['lat']}, {edit_data['lon']}")

            if st.button("Güncelle"):
                lat, lon = map(float, koordinat.split(","))
                for user in kullanicilar:
                    if user["ad"] == edit_data["ad"]:
                        user["ad"] = ad
                        user["soyad"] = soyad
                        user["telefon"] = telefon
                        user["lat"] = lat
                        user["lon"] = lon
                        break
                
                with open(JSON_FILE, "w") as f:
                    json.dump(kullanicilar, f, indent=4)

                del st.session_state["edit_user"]
                st.success("Kullanıcı bilgileri güncellendi!")
                st.rerun()

# ⚙ **Sistem Ayarları**
elif sayfa == "Sistem Ayarları":
    st.title("⚙ Sistem Ayarları")

    st.write("⏰ **Her gün saat 03:00’te kullanıcılar otomatik olarak pasif yapılır.**")

    if st.button("🔄 Kullanıcıları Şimdi Pasif Yap"):
        reset_durumlar()
        st.success("✅ Tüm kullanıcılar pasif hale getirildi.")
