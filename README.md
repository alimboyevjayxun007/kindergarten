# Bog'cha CRM (Django)

Bog'cha uchun oddiy full-stack Django 5.x + Bootstrap 5 ilovasi. Ilova guruhlar, bolalar, vasiylar, davomat, tariflar va soddalashtirilgan oylik to'lovlarni boshqaradi.

## Talablar

- Python 3.11+ (repo 3.11/3.12 bilan ishlaydi)
- PostgreSQL ixtiyoriy; SQLite standart holatda ishlaydi

## Lokal ishga tushirish

### 1) Virtual muhit yaratish

macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2) Kutubxonalarni o'rnatish

```bash
pip install -r requirements.txt
```

### 3) Muhit sozlamalari

```bash
cp .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

`.env` ichida kamida `SECRET_KEY` ni o'rnating.

### 4) Migratsiyalar

```bash
python manage.py migrate
```

### 5) Superadmin yaratish

Admin panelga kirish uchun superuser yarating:

```bash
python manage.py createsuperuser
```

Kiritgan login/parolingiz bilan `/admin/` ga kira olasiz.

### 6) Demo ma'lumotlar

```bash
python manage.py seed_demo_data
```

Demo rolli foydalanuvchilar kerak bo'lsa:

```bash
python manage.py setup_role_users
```

Bu buyruq quyidagi demo foydalanuvchilarni yaratadi:

- `adminuser` / `Adminuser@12345`
- `educator` / `Educator@12345`
- `accountant` / `Accountant@12345`

### 7) Serverni ishga tushirish

```bash
python manage.py runserver
```

Ochish:

- http://127.0.0.1:8000/ - ommaviy bosh sahifa
- http://127.0.0.1:8000/classrooms/ - CRUD, kirish talab qilinadi
- http://127.0.0.1:8000/admin/ - admin panel

## Render deploy

Repo ichida `render.yaml` va `build.sh` bor. Render deploy paytida `build.sh` quyidagilarni bajaradi:

```bash
pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
```

Start command:

```bash
gunicorn kindergarten_crm.wsgi:application
```

Render environment variables:

```env
DEBUG=0
SECRET_KEY=<Render generate value yoki uzun random qiymat>
ALLOWED_HOSTS=.onrender.com
CSRF_TRUSTED_ORIGINS=https://*.onrender.com
TIME_ZONE=Asia/Tashkent
WEB_CONCURRENCY=1
```

Agar o'z domeningiz bo'lsa:

```env
ALLOWED_HOSTS=your-domain.com,.onrender.com
CSRF_TRUSTED_ORIGINS=https://your-domain.com,https://*.onrender.com
```

### Render'da login qilib bo'lmasa

Deploy bo'lgan yangi production bazada lokal kompyuterdagi `db.sqlite3` va lokal superuser bo'lmaydi. Shuning uchun Render'dagi database ichida alohida user yaratish kerak.

Render Shell orqali superuser yaratish:

```bash
python manage.py createsuperuser
```

Yoki no-interactive usul:

```bash
DJANGO_SUPERUSER_USERNAME=admin DJANGO_SUPERUSER_EMAIL=admin@example.com DJANGO_SUPERUSER_PASSWORD='KuchliParol123!' python manage.py createsuperuser --noinput
```

Demo rolli userlar bilan kirish kerak bo'lsa Render Shell'da:

```bash
python manage.py setup_role_users
```

Keyin quyidagi sahifadan kiring:

```text
/accounts/login/
```

Eslatma: `setup_role_users` demo login/parollarni yaratadi. Production uchun kuchli parolli alohida superuser ishlating.

## PostgreSQL

`.env` yoki Render environment variables ichida `DATABASE_URL` ni sozlang:

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/kindergarten_crm
```

So'ng:

```bash
python manage.py migrate
python manage.py runserver
```

Render'da PostgreSQL ishlatish tavsiya qilinadi. SQLite Render'da production uchun qulay emas, chunki disk doimiy saqlanmasligi mumkin.

## Avtorizatsiya

Loyiha Django'ning standart autentifikatsiyasidan foydalanadi:

- Kirish: `/accounts/login/`
- Chiqish: `/accounts/logout/`
- Parolni tiklash: `/accounts/password_reset/`

Parolni tiklash xabarlari development rejimida console email backend orqali terminalga chiqariladi.

## Davomat

- Davomat ro'yxati: `/attendance/`
- Sanani tanlang va xohlasangiz guruh/holat bo'yicha filter qiling.
- Agar tanlangan sanada davomat yozuvlari bo'lmasa, ilova barcha faol bolalar uchun avtomatik `Expected` yozuvlarini yaratadi.
- Qator tugmalari orqali `Keldi`, `Kechikdi`, `Kelmagan`, `Yarim kun` holatini belgilang.
- Guruhni ommaviy `Keldi` deb belgilash uchun avval guruh filterini tanlang, so'ng `Bulk mark Present` tugmasidan foydalaning.

## To'lov

### Oylik to'lov

- Oylik to'lov sahifasi: `/billing/monthly/`
- Oyni tanlang (`YYYY-MM`) va xohlasangiz filter/qidiruvdan foydalaning.
- Oy ochilganda barcha faol bolalar uchun yozuvlar avtomatik yaratiladi.
- Avtomatik summa bolaning biriktirilgan tarifi bo'yicha olinadi; tarif bo'lmasa `0`.
- `Mark Paid` / `Mark Unpaid` tugmalari orqali holatni o'zgartiring.

### Tariflar

- Tariflarni boshqarish: `/tariffs/`
- Bolaga tarif biriktirish: bola qo'shish/tahrirlash formasi orqali.

Ilova soddalashtirilgan oylik to'lov oqimidan foydalanadi: har bir bola va har bir oy uchun bitta yozuv.

## Eslatmalar

- Maxfiy ma'lumotlarni repoga kiritmang; `.env` yoki environment variables orqali sozlang.
- Static fayllar production'da WhiteNoise orqali serve qilinadi.
- Media fayllar development uchun lokal papkada saqlanadi; production'da alohida storage ishlatish tavsiya qilinadi.
