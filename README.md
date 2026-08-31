# Xodimlar tizimi — Streamlit versiyasi (sinov uchun)

Python + Streamlit + SQLAlchemy asosida qurilgan. Standart holatda **SQLite**
(alohida baza o'rnatishsiz ishlaydi), xohlasangiz PostgreSQL'ga ham ulanadi.

## 1. Lokal kompyuterda sinash

```bash
cd streamlit-app
pip install -r requirements.txt
python seed.py          # Bosh administrator yaratadi, login/parol so'raladi
streamlit run app.py
```

Brauzerda `http://localhost:8501` ochiladi. `seed.py`da kiritgan login/parol bilan kiring.

## 2. GitHub'ga joylash

Loyiha papkasida (`streamlit-app/`) terminal orqali:

```bash
git init
git add .
git commit -m "Xodimlar tizimi - Streamlit versiyasi"
git branch -M main
git remote add origin https://github.com/<sizning-username>/<repo-nomi>.git
git push -u origin main
```

`<sizning-username>` va `<repo-nomi>`ni GitHub'da avval yaratgan repo'ingizga
moslang. Push qilishda GitHub login/parolingiz yoki shaxsiy token (PAT)
so'raladi.

**Muhim:** `xodimlar.db` (SQLite fayli, agar lokal yaratilgan bo'lsa) va
`.env` kabi maxfiy fayllarni GitHub'ga yuklamang — quyidagi `.gitignore`
faylidan foydalaning (loyihaga qo'shib qo'yilgan).

## 3. Streamlit Community Cloud'da sinash (bepul)

1. https://streamlit.io/cloud ga o'zingizning GitHub hisobingiz bilan kiring
2. "New app" tugmasini bosing
3. Yuqorida yaratgan GitHub repo'ingizni tanlang
4. Main file path: `app.py`
5. "Deploy" tugmasini bosing — bir necha daqiqada tayyor bo'ladi

**Diqqat — SQLite haqida muhim eslatma:** Streamlit Cloud'da fayl tizimi
doimiy emas — ilova qayta ishga tushganda (masalan, uxlab qolgach
uyg'onganda) SQLite fayli **tozalanishi mumkin** va barcha ma'lumot
yo'qoladi. Bu faqat **UI'ni sinash** uchun yaxshi, lekin **haqiqiy
xodimlar ma'lumotlarini saqlash uchun mos emas**.

Haqiqiy ma'lumotlarni doimiy saqlash uchun bepul PostgreSQL bazasi oling
(masalan, [Supabase](https://supabase.com) yoki [Neon](https://neon.tech) —
ikkalasi ham bepul tarif beradi) va Streamlit Cloud'ning "Secrets"
bo'limida quyidagini qo'shing:

```toml
DATABASE_URL = "postgresql+psycopg2://user:password@host:5432/dbname"
```

Bundan keyin ilova avtomatik ravishda SQLite o'rniga shu bazadan foydalanadi
(`db.py` buni `os.environ.get("DATABASE_URL", ...)` orqali o'zi aniqlaydi).

## Loyiha tuzilishi

```
streamlit-app/
├── app.py                  <- bosh sahifa (dashboard)
├── auth.py                 <- login, bcrypt parol tekshiruvi, sessiya
├── db.py                   <- SQLAlchemy modellar (SQLite/Postgres)
├── seed.py                 <- birinchi admin va namunaviy ma'lumot yaratish
├── requirements.txt
├── .gitignore
└── pages/
    ├── 1_Hududlar.py
    ├── 2_Maktablar.py
    └── 3_Oqituvchilar.py
```

## Eslatma: bu Node.js versiyasining o'rnini bosadimi?

Yo'q — bu **alohida, sinov uchun soddalashtirilgan** versiya. Avval
tayyorlangan Node.js/Express + PostgreSQL backend ancha to'liqroq (JWT,
rate-limiting, kengroq API). Streamlit versiyasi tezroq va osonroq sinab
ko'rish uchun qulay, lekin katta miqyosda, ko'p foydalanuvchi bir vaqtda
ishlaydigan production tizim uchun Node.js versiyasi (yoki shunga o'xshash
to'liq backend) tavsiya etiladi.
