# ================================
# APLIKASI ABSENSI & JADWAL LATIHAN
# SESUAI USE CASE (USER & ADMIN)
# STREAMLIT + DATABASE CLOUD (POSTGRESQL)
# ================================

import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import date
import pandas as pd
from hashlib import sha256

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Sistem Absensi Online", layout="wide")

DB_CONFIG = {
    "host": st.secrets["DB_HOST"],
    "dbname": st.secrets["DB_NAME"],
    "user": st.secrets["DB_USER"],
    "password": st.secrets["DB_PASSWORD"],
    "port": st.secrets["DB_PORT"],
}

# ---------------- DATABASE ----------------
def get_conn():
    return psycopg2.connect(**DB_CONFIG)

# ---------------- SECURITY ----------------
def hash_password(password):
    return sha256(password.encode()).hexdigest()

# ---------------- AUTH ----------------
def login(username, password):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM users WHERE username=%s AND password=%s",
                (username, hash_password(password)))
    user = cur.fetchone()
    conn.close()
    return user

# ---------------- SESSION ----------------
if "user" not in st.session_state:
    st.session_state.user = None

# ---------------- LOGIN PAGE ----------------
def login_page():
    st.title("🔐 Login Sistem Absensi")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = login(username, password)
        if user:
            st.session_state.user = user
            st.rerun()
        else:
            st.error("Login gagal")

# ---------------- USER DASHBOARD ----------------
def user_dashboard():
    st.subheader("👤 Dashboard User")

    menu = st.sidebar.radio("Menu", [
        "Lihat Jadwal Latihan",
        "Mengelola Absensi",
        "Daftar Absensi",
        "Ekspor PDF",
        "Logout"
    ])

    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    if menu == "Lihat Jadwal Latihan":
        st.header("📅 Jadwal Latihan")
        cur.execute("SELECT * FROM jadwal ORDER BY tanggal")
        st.dataframe(pd.DataFrame(cur.fetchall()))

    elif menu == "Mengelola Absensi":
        st.header("📝 Input Absensi")
        status = st.selectbox("Status", ["Hadir", "Izin", "Sakit", "Alfa"])
        if st.button("Simpan Absensi"):
            cur.execute("INSERT INTO absensi(user_id, tanggal, status) VALUES(%s,%s,%s)",
                        (st.session_state.user['id'], date.today(), status))
            conn.commit()
            st.success("Absensi tersimpan")

    elif menu == "Daftar Absensi":
        st.header("📋 Riwayat Absensi")
        cur.execute("SELECT tanggal, status FROM absensi WHERE user_id=%s",
                    (st.session_state.user['id'],))
        st.dataframe(pd.DataFrame(cur.fetchall()))

    elif menu == "Ekspor PDF":
        st.info("Fitur ekspor PDF bisa ditambahkan dengan reportlab")

    elif menu == "Logout":
        st.session_state.user = None
        st.rerun()

    conn.close()

# ---------------- ADMIN DASHBOARD ----------------
def admin_dashboard():
    st.subheader("🛠 Dashboard Admin")

    menu = st.sidebar.radio("Menu Admin", [
        "Monitoring Sistem",
        "Kelola Jadwal",
        "Cari & Filter Absensi",
        "Backup / Restore",
        "Logout"
    ])

    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    if menu == "Monitoring Sistem":
        st.success("Server Aktif")

    elif menu == "Kelola Jadwal":
        st.header("📅 Tambah Jadwal")
        tgl = st.date_input("Tanggal")
        ket = st.text_input("Keterangan")
        if st.button("Simpan Jadwal"):
            cur.execute("INSERT INTO jadwal(tanggal, keterangan) VALUES(%s,%s)", (tgl, ket))
            conn.commit()
            st.success("Jadwal tersimpan")

        st.divider()
        cur.execute("SELECT * FROM jadwal")
        st.dataframe(pd.DataFrame(cur.fetchall()))

    elif menu == "Cari & Filter Absensi":
        st.header("🔎 Filter Absensi")
        tgl = st.date_input("Tanggal")
        cur.execute("SELECT * FROM absensi WHERE tanggal=%s", (tgl,))
        st.dataframe(pd.DataFrame(cur.fetchall()))

    elif menu == "Backup / Restore":
        st.info("Backup & restore database dilakukan via server (Railway/Supabase)")

    elif menu == "Logout":
        st.session_state.user = None
        st.rerun()

    conn.close()

# ---------------- ROUTER ----------------
if not st.session_state.user:
    login_page()
else:
    if st.session_state.user['role'] == 'admin':
        admin_dashboard()
    else:
        user_dashboard()

# ================================
# DATABASE TABLES (POSTGRESQL)
# users(id, username, password, role)
# jadwal(id, tanggal, keterangan)
# absensi(id, user_id, tanggal, status)
# ================================
