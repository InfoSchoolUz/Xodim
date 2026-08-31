import streamlit as st
import pandas as pd
from db import get_session, Region, School, Teacher, User
from auth import require_role, logout_button, hash_password, log_audit

user = require_role("superadmin", "boshqarma")
logout_button()

st.title("👤 Foydalanuvchilar (loginlar)")
st.caption("Har bir hudud, maktab yoki o'qituvchi uchun alohida login/parol shu yerda yaratiladi.")

session = get_session()
try:
    regions = session.query(Region).order_by(Region.name).all()
    schools = session.query(School).order_by(School.name).all()
    teachers = session.query(Teacher).filter(Teacher.is_archived == False).order_by(Teacher.last_name).all()  # noqa: E712

    # ---------- Mavjud foydalanuvchilar ro'yxati ----------
    users = session.query(User).order_by(User.role, User.login).all()
    region_names = {r.id: r.name for r in regions}
    school_names = {s.id: s.name for s in schools}
    teacher_names = {t.id: f"{t.last_name} {t.first_name}" for t in teachers}

    rows = []
    for u in users:
        bog_langan = "-"
        if u.region_id:
            bog_langan = region_names.get(u.region_id, "-")
        elif u.school_id:
            bog_langan = school_names.get(u.school_id, "-")
        elif u.teacher_id:
            bog_langan = teacher_names.get(u.teacher_id, "-")
        rows.append({
            "Login": u.login,
            "Rol": u.role,
            "Bog'langan": bog_langan,
            "Holat": "Faol" if u.is_active else "O'chirilgan",
        })
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("Hozircha hech qanday foydalanuvchi yo'q.")

    st.divider()
    st.subheader("Yangi login yaratish")

    role_labels = {
        "boshqarma": "Boshqarma xodimi (barcha hududlarni ko'radi)",
        "hudud_admin": "Hudud admini (faqat bitta hudud)",
        "maktab": "Maktab admini (faqat bitta maktab)",
        "oqituvchi": "O'qituvchi (faqat o'z profili)",
    }

    with st.form("add_user", clear_on_submit=True):
        role_display = st.selectbox("Rol", list(role_labels.values()))
        role_key = [k for k, v in role_labels.items() if v == role_display][0]

        region_id = school_id = teacher_id = None

        if role_key == "hudud_admin":
            if not regions:
                st.warning("Avval kamida bitta hudud qo'shing (Hududlar sahifasida).")
            else:
                region_choice = st.selectbox("Qaysi hudud uchun?", [r.name for r in regions])
                region_id = [r.id for r in regions if r.name == region_choice][0]

        elif role_key == "maktab":
            if not schools:
                st.warning("Avval kamida bitta maktab qo'shing (Maktablar sahifasida).")
            else:
                school_choice = st.selectbox(
                    "Qaysi maktab uchun?",
                    [f"{s.name} ({region_names.get(s.region_id, '-')})" for s in schools],
                )
                idx = [f"{s.name} ({region_names.get(s.region_id, '-')})" for s in schools].index(school_choice)
                school_id = schools[idx].id

        elif role_key == "oqituvchi":
            if not teachers:
                st.warning("Avval kamida bitta o'qituvchi qo'shing (O'qituvchilar sahifasida).")
            else:
                teacher_choice = st.selectbox(
                    "Qaysi o'qituvchi uchun?",
                    [f"{t.last_name} {t.first_name}" for t in teachers],
                )
                idx = [f"{t.last_name} {t.first_name}" for t in teachers].index(teacher_choice)
                teacher_id = teachers[idx].id

        full_name = st.text_input("To'liq ism (ixtiyoriy, masalan direktor ismi)")
        login_val = st.text_input("Login")
        password_val = st.text_input("Parol (kamida 8 belgi)", type="password")

        submitted = st.form_submit_button("Login yaratish")

    if submitted:
        if not login_val.strip():
            st.error("Login kiriting.")
        elif len(password_val) < 8:
            st.error("Parol kamida 8 belgidan iborat bo'lishi kerak.")
        elif session.query(User).filter(User.login == login_val.strip()).first():
            st.error("Bu login allaqachon band. Boshqa login tanlang.")
        elif role_key == "hudud_admin" and not region_id:
            st.error("Hudud tanlanmadi.")
        elif role_key == "maktab" and not school_id:
            st.error("Maktab tanlanmadi.")
        elif role_key == "oqituvchi" and not teacher_id:
            st.error("O'qituvchi tanlanmadi.")
        else:
            new_user = User(
                login=login_val.strip(),
                password_hash=hash_password(password_val),
                role=role_key,
                full_name=full_name or None,
                region_id=region_id,
                school_id=school_id,
                teacher_id=teacher_id,
            )
            session.add(new_user)
            session.commit()
            log_audit(session, user["id"], "create_user", login_val.strip())
            st.success(f'✅ "{login_val.strip()}" uchun login yaratildi. Bu ma\'lumotni tegishli shaxsga bering.')
            st.rerun()

    # ---------- Login o'chirish / faollikni o'zgartirish ----------
    if users:
        st.divider()
        st.subheader("Loginni faollashtirish / o'chirish")
        other_users = [u for u in users if u.id != user["id"]]  # o'zini o'zi bloklamasin
        if other_users:
            chosen_login = st.selectbox("Foydalanuvchini tanlang", [u.login for u in other_users])
            chosen = [u for u in other_users if u.login == chosen_login][0]
            col1, col2 = st.columns(2)
            if chosen.is_active:
                if col1.button("🚫 Faolsizlantirish"):
                    chosen.is_active = False
                    session.commit()
                    log_audit(session, user["id"], "deactivate_user", chosen.login)
                    st.rerun()
            else:
                if col1.button("✅ Qayta faollashtirish"):
                    chosen.is_active = True
                    session.commit()
                    log_audit(session, user["id"], "activate_user", chosen.login)
                    st.rerun()
        else:
            st.caption("Boshqa foydalanuvchi yo'q.")
finally:
    session.close()
