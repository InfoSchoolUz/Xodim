"""
Birinchi Bosh administrator va sinov uchun namunaviy ma'lumotlarni yaratadi.
Ishlatish:  python seed.py
"""
import getpass
from db import init_db, get_session, User, Region, School
from auth import hash_password

init_db()
session = get_session()

try:
    login = input("Bosh administrator login (masalan: admin): ").strip() or "admin"
    password = getpass.getpass("Bosh administrator paroli (kamida 8 belgi): ")

    if len(password) < 8:
        print("❌ Parol kamida 8 belgidan iborat bo'lishi kerak.")
        raise SystemExit(1)

    existing = session.query(User).filter(User.login == login).first()
    if existing:
        existing.password_hash = hash_password(password)
        existing.role = "superadmin"
        existing.is_active = True
        session.commit()
        print(f'✅ Mavjud foydalanuvchi "{login}" Bosh administrator sifatida yangilandi.')
    else:
        session.add(User(
            login=login,
            password_hash=hash_password(password),
            role="superadmin",
            full_name="Bosh administrator",
        ))
        session.commit()
        print(f'✅ Bosh administrator "{login}" yaratildi.')

    # Ixtiyoriy: sinov uchun bir nechta namunaviy hudud/maktab qo'shish
    if session.query(Region).count() == 0:
        add_sample = input("Sinov uchun namunaviy hudud va maktab qo'shilsinmi? (ha/yo'q): ").strip().lower()
        if add_sample in ("ha", "h", "y", "yes"):
            r1 = Region(name="Chirchiq shahri")
            r2 = Region(name="Zangiota tumani")
            session.add_all([r1, r2])
            session.commit()
            session.add_all([
                School(region_id=r1.id, name="1-maktab", address="Chirchiq sh.", director="A. Aliyev", students_count=450),
                School(region_id=r2.id, name="5-bog'cha", address="Zangiota t.", director="M. Mahmudova", students_count=120),
            ])
            session.commit()
            print("✅ Namunaviy ma'lumotlar qo'shildi.")
finally:
    session.close()
