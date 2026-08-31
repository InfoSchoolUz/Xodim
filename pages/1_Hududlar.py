import streamlit as st
import pandas as pd
from db import get_session, Region, School
from auth import require_login, logout_button, log_audit

st.set_page_config(page_title="Hududlar", page_icon="🗺️", layout="wide")
user = require_login()
logout_button()

st.title("🗺️ Hududlar")

session = get_session()
try:
    regions = session.query(Region).order_by(Region.name).all()
    rows = []
    for r in regions:
        schools_count = session.query(School).filter(School.region_id == r.id).count()
        rows.append({"Nomi": r.name, "Maktablar soni": schools_count, "id": r.id})

    if rows:
        df = pd.DataFrame(rows).drop(columns=["id"])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Hozircha hech qanday hudud qo'shilmagan.")

    if user["role"] in ("superadmin", "boshqarma"):
        st.divider()
        st.subheader("Yangi hudud qo'shish")
        with st.form("add_region", clear_on_submit=True):
            name = st.text_input("Hudud nomi (masalan: Chirchiq shahri)")
            submitted = st.form_submit_button("Qo'shish")
        if submitted:
            if not name.strip():
                st.error("Hudud nomini kiriting.")
            elif session.query(Region).filter(Region.name == name.strip()).first():
                st.error("Bu nomdagi hudud allaqachon mavjud.")
            else:
                new_region = Region(name=name.strip())
                session.add(new_region)
                session.commit()
                log_audit(session, user["id"], "create_region", name.strip())
                st.success(f'"{name.strip()}" hududi qo\'shildi.')
                st.rerun()
finally:
    session.close()
