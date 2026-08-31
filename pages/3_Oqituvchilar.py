import json
import streamlit as st
import pandas as pd
from db import get_session, School, Teacher, ArchiveTeacher, Region
from auth import require_login, logout_button, log_audit

st.set_page_config(page_title="O'qituvchilar", page_icon="🧑‍🏫", layout="wide")
user = require_login()
logout_button()

st.title("🧑‍🏫 O'qituvchilar")

session = get_session()
try:
    query = session.query(Teacher).filter(Teacher.is_archived == False)  # noqa: E712

    if user["role"] == "oqituvchi" and user["teacher_id"]:
        query = query.filter(Teacher.id == user["teacher_id"])
    elif user["role"] == "maktab" and user["school_id"]:
        query = query.filter(Teacher.school_id == user["school_id"])
    elif user["role"] == "hudud_admin" and user["region_id"]:
        school_ids = [s.id for s in session.query(School).filter(School.region_id == user["region_id"])]
        query = query.filter(Teacher.school_id.in_(school_ids))

    teachers = query.all()
    schools = {s.id: s for s in session.query(School).all()}
    regions = {r.id: r.name for r in session.query(Region).all()}

    rows = []
    for t in teachers:
        sch = schools.get(t.school_id)
        rows.append({
            "F.I.Sh.": f"{t.last_name or ''} {t.first_name or ''} {t.middle_name or ''}".strip(),
            "Maktab": sch.name if sch else "-",
            "Hudud": regions.get(sch.region_id, "-") if sch else "-",
            "Jinsi": t.gender or "-",
            "Telefon": t.phone or "-",
            "Ma'lumoti": t.education or "-",
            "Toifasi": t.category or "-",
            "Ish turi": t.work_type or "-",
            "id": t.id,
        })

    if rows:
        df = pd.DataFrame(rows)
        st.dataframe(df.drop(columns=["id"]), use_container_width=True, hide_index=True)
    else:
        st.info("O'qituvchilar topilmadi.")

    can_manage = user["role"] in ("superadmin", "boshqarma", "hudud_admin", "maktab")

    if can_manage and schools:
        st.divider()
        st.subheader("Yangi o'qituvchi qo'shish")
        with st.form("add_teacher", clear_on_submit=True):
            if user["role"] == "maktab":
                school_id = user["school_id"]
                st.text_input("Maktab", value=schools[school_id].name if school_id in schools else "-", disabled=True)
            else:
                school_options = {f"{s.name} ({regions.get(s.region_id, '-')})": sid for sid, s in schools.items()}
                chosen = st.selectbox("Maktab", sorted(school_options.keys()))
                school_id = school_options[chosen]

            c1, c2, c3 = st.columns(3)
            last_name = c1.text_input("Familiya")
            first_name = c2.text_input("Ism")
            middle_name = c3.text_input("Sharif")

            c4, c5 = st.columns(2)
            gender = c4.selectbox("Jinsi", ["Erkak", "Ayol"])
            phone = c5.text_input("Telefon")

            c6, c7, c8 = st.columns(3)
            education = c6.text_input("Ma'lumoti")
            category = c7.text_input("Toifasi")
            work_type = c8.selectbox("Ish turi", ["asosiy", "ichki", "tashqi"])

            submitted = st.form_submit_button("Qo'shish")

        if submitted:
            if not last_name.strip() or not first_name.strip():
                st.error("Familiya va ism kiritilishi shart.")
            else:
                new_teacher = Teacher(
                    school_id=school_id, last_name=last_name, first_name=first_name,
                    middle_name=middle_name, gender=gender, phone=phone,
                    education=education, category=category, work_type=work_type,
                )
                session.add(new_teacher)
                session.commit()
                log_audit(session, user["id"], "create_teacher", f"{last_name} {first_name}")
                st.success("O'qituvchi qo'shildi.")
                st.rerun()

    if can_manage and rows:
        st.divider()
        st.subheader("O'qituvchini arxivlash (ishdan bo'shatish)")
        name_to_id = {r["F.I.Sh."]: r["id"] for r in rows}
        chosen_name = st.selectbox("O'qituvchini tanlang", list(name_to_id.keys()))
        if st.button("Arxivga o'tkazish", type="secondary"):
            teacher = session.query(Teacher).filter(Teacher.id == name_to_id[chosen_name]).first()
            if teacher:
                snapshot = {
                    "id": teacher.id, "school_id": teacher.school_id,
                    "last_name": teacher.last_name, "first_name": teacher.first_name,
                    "middle_name": teacher.middle_name, "gender": teacher.gender,
                    "phone": teacher.phone, "education": teacher.education,
                    "category": teacher.category, "work_type": teacher.work_type,
                }
                session.add(ArchiveTeacher(
                    original_teacher_id=teacher.id, school_id=teacher.school_id,
                    full_name=f"{teacher.last_name} {teacher.first_name}",
                    data_snapshot=json.dumps(snapshot, ensure_ascii=False),
                    archived_by=user["id"],
                ))
                teacher.is_archived = True
                session.commit()
                log_audit(session, user["id"], "archive_teacher", chosen_name)
                st.success(f'"{chosen_name}" arxivga o\'tkazildi.')
                st.rerun()
finally:
    session.close()
