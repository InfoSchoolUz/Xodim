"""
Autentifikatsiya yordamchi funksiyalari.
Parollar bcrypt bilan hash qilinadi — bazada hech qachon ochiq matnda saqlanmaydi.
"""
import bcrypt
import streamlit as st
from db import get_session, User, AuditLog


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except Exception:
        return False


def log_audit(session, user_id, action, details=None):
    session.add(AuditLog(user_id=user_id, action=action, details=details))
    session.commit()


def attempt_login(login: str, password: str):
    """Login/parolni tekshiradi. Muvaffaqiyatli bo'lsa User obyektini, aks holda None qaytaradi."""
    session = get_session()
    try:
        user = session.query(User).filter(User.login.ilike(login)).first()
        # Foydalanuvchi topilmasa ham bcrypt.checkpw chaqiramiz — timing attack'dan himoya.
        dummy_hash = "$2b$12$abcdefghijklmnopqrstuuC8n2E1r6z6qk9x9r0v0d0f0g0h0i0j0k"
        ok = verify_password(password, user.password_hash if user else dummy_hash)

        if not user or not ok or not user.is_active:
            log_audit(session, user.id if user else None, "login_failed", login)
            return None

        import datetime
        user.last_login_at = datetime.datetime.utcnow()
        session.commit()
        log_audit(session, user.id, "login")

        # Streamlit sessiyasida saqlash uchun oddiy dict qaytaramiz (ORM obyekt emas)
        return {
            "id": user.id,
            "login": user.login,
            "role": user.role,
            "full_name": user.full_name,
            "region_id": user.region_id,
            "school_id": user.school_id,
            "teacher_id": user.teacher_id,
        }
    finally:
        session.close()


def current_user():
    return st.session_state.get("user")


def _any_user_exists() -> bool:
    session = get_session()
    try:
        return session.query(User).first() is not None
    finally:
        session.close()


def _first_time_setup():
    """Bazada hech qanday foydalanuvchi yo'q bo'lsa (masalan, Streamlit Cloud'da
    terminal orqali seed.py ishlatib bo'lmagani uchun), birinchi Bosh administratorni
    to'g'ridan-to'g'ri sayt orqali yaratish imkonini beradi."""
    st.title("🛠️ Birinchi sozlash")
    st.caption("Bazada hali hech qanday foydalanuvchi yo'q. Birinchi Bosh administratorni yarating.")
    with st.form("setup_form"):
        login_val = st.text_input("Yangi login (masalan: admin)")
        password_val = st.text_input("Yangi parol (kamida 8 belgi)", type="password")
        password_confirm = st.text_input("Parolni takrorlang", type="password")
        submitted = st.form_submit_button("Administrator yaratish")

    if submitted:
        if not login_val.strip():
            st.error("Login kiriting.")
            return
        if len(password_val) < 8:
            st.error("Parol kamida 8 belgidan iborat bo'lishi kerak.")
            return
        if password_val != password_confirm:
            st.error("Parollar mos kelmadi.")
            return

        session = get_session()
        try:
            # Ikkinchi tekshiruv — shu payt orasida boshqa birov allaqachon yaratgan bo'lishi mumkin.
            if session.query(User).first() is not None:
                st.warning("Boshqa foydalanuvchi allaqachon yaratildi. Sahifani yangilang va tizimga kiring.")
                return
            session.add(User(
                login=login_val.strip(),
                password_hash=hash_password(password_val),
                role="superadmin",
                full_name="Bosh administrator",
            ))
            session.commit()
            st.success("✅ Administrator yaratildi! Endi shu login/parol bilan tizimga kiring.")
            st.rerun()
        finally:
            session.close()
    st.stop()


def require_login():
    """Sahifa boshida chaqiriladi — tizimga kirmagan bo'lsa, login formasini ko'rsatib to'xtaydi."""
    if "user" not in st.session_state or st.session_state["user"] is None:
        if not _any_user_exists():
            _first_time_setup()

        st.title("🔐 Tizimga kirish")
        st.caption("Toshkent viloyati maktabgacha va maktab ta'limi boshqarmasi")
        with st.form("login_form"):
            login_val = st.text_input("Login")
            password_val = st.text_input("Parol", type="password")
            submitted = st.form_submit_button("Kirish")
        if submitted:
            user = attempt_login(login_val.strip(), password_val)
            if user:
                st.session_state["user"] = user
                st.rerun()
            else:
                st.error("Login yoki parol noto'g'ri.")
        st.stop()
    return st.session_state["user"]


def require_role(*allowed_roles):
    user = require_login()
    if user["role"] not in allowed_roles:
        st.error("Bu sahifani ko'rish uchun ruxsatingiz yo'q.")
        st.stop()
    return user


def logout_button():
    user = current_user()
    if user:
        with st.sidebar:
            st.markdown(f"**{user.get('full_name') or user['login']}**")
            st.caption(f"Rol: {user['role']}")
            if st.button("Chiqish"):
                st.session_state["user"] = None
                st.rerun()
