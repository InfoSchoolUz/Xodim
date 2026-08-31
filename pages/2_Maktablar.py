import streamlit as st
import pandas as pd
from db import get_session, Region, School, Teacher
from auth import require_login, logout_button, log_audit

st.set_page_config(page_title="Maktablar", page_icon="🏫", layout="wide")
user = require_login()
logout_button()

st.title("🏫 Maktablar")

session = get_session()
try:
    query = session.query(School)

    # Rolga qarab cheklash
    if user["role"] == "hudud_admin" and user["region_id"]:
        query = query.filter(School.region_id == user["region_id"])
    elif user["role"] == "maktab" and user["school_id"]:
        query = query.filter(School.id == user["school_id"])

    regions = {r.id: r.name for r in session.query(Region).all()}

    # Boshqarma/superadmin uchun hudud bo'yicha filtr
    if user["role"] in ("superadmin", "boshqarma"):
        region_names = ["Barchasi"] + sorted(regions.values())
        selected = st.selectbox("Hudud bo'yicha filtr", region_names)
        if selected != "Barchasi":
            region_id = [rid for rid, name in regions.items() if name == selected][0]
            query = query.filter(School.region_id == region_id)

    schools = query.all()
    rows = []
    for s in schools:
        teachers_count = session.query(Teacher).filter(
            Teacher.school_id == s.id, Teacher.is_archived == False  # noqa: E712
        ).count()
        rows.append({
            "Nomi": s.name,
            "Hudud": regions.get(s.region_id, "-"),
            "Manzil": s.address or "-",
            "Direktor": s.director or "-",
            "Telefon": s.phone or "-",
            "O'quvchilar": s.students_count,
            "Holat": "Faol" if s.status == "active" else "To'xtatilgan",
            "O'qituvchilar soni": teachers_count,
        })

    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("Maktablar topilmadi.")

    can_add = user["role"] in ("superadmin", "boshqarma", "hudud_admin")
    if can_add and regions:
        st.divider()
        st.subheader("Yangi maktab qo'shish")
        with st.form("add_school", clear_on_submit=True):
            if user["role"] == "hudud_admin":
                region_id = user["region_id"]
                st.text_input("Hudud", value=regions.get(region_id, "-"), disabled=True)
            else:
                region_name = st.selectbox("Hudud", sorted(regions.values()))
                region_id = [rid for rid, name in regions.items() if name == region_name][0]

            name = st.text_input("Maktab nomi")
            address = st.text_input("Manzil")
            director = st.text_input("Direktor")
            phone = st.text_input("Telefon")
            students_count = st.number_input("O'quvchilar soni", min_value=0, step=1)
            submitted = st.form_submit_button("Qo'shish")

        if submitted:
            if not name.strip():
                st.error("Maktab nomini kiriting.")
            else:
                new_school = School(
                    region_id=region_id, name=name.strip(), address=address,
                    director=director, phone=phone, students_count=int(students_count),
                )
                session.add(new_school)
                session.commit()
                log_audit(session, user["id"], "create_school", name.strip())
                st.success(f'"{name.strip()}" qo\'shildi.')
                st.rerun()
finally:
    session.close()
