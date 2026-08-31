import streamlit as st
from db import init_db, get_session, Region, School, Teacher
from auth import require_login, logout_button

st.set_page_config(page_title="Xodimlar tizimi", page_icon="🏫", layout="wide")

init_db()

user = require_login()
logout_button()

st.title("🏫 Toshkent viloyati maktabgacha va maktab ta'limi boshqarmasi")
st.caption("Xodimlar boshqaruv tizimi — sinov versiyasi (Streamlit)")

session = get_session()
try:
    regions_count = session.query(Region).count()
    schools_count = session.query(School).count()
    teachers_count = session.query(Teacher).filter(Teacher.is_archived == False).count()  # noqa: E712
finally:
    session.close()

col1, col2, col3 = st.columns(3)
col1.metric("Hududlar", regions_count)
col2.metric("Maktablar", schools_count)
col3.metric("O'qituvchilar", teachers_count)

st.divider()
st.markdown(
    """
    Chap tarafdagi menyudan bo'limlarni tanlang:
    - **Hududlar** — tuman/shaharlar ro'yxati
    - **Maktablar** — maktab/bog'chalar ro'yxati va tahrirlash
    - **O'qituvchilar** — o'qituvchilar ro'yxati, qo'shish, arxivlash
    """
)

if user["role"] == "superadmin":
    st.info("Siz Bosh administrator sifatida kirdingiz — barcha bo'limlarga to'liq huquqingiz bor.")
