# Flywerk Automation

Десктопное приложение на Python (PyQt6) с тремя независимыми вкладками:

1. **PagesAutoclick** — автокликер: задержка перед стартом, количество кликов, задержка между кликами.
2. **OpenChannels** — тот же движок, но с другими дефолтами под открытие каналов в закреплённой вкладке Chrome (7 сек / 100 / 50 мс).
3. **Progress** — четыре прогресс-бара: Кредит (500 000), Компьютер (300 000), Квартира (1 000 000), Общий (1 800 000). Кнопка «Добавить» прибавляет введённую сумму к выбранной цели. «Отменить» откатывает последнее добавление.

Окно без системной рамки, со своим заголовком, перетаскиванием и растягиванием за края.

---

## 1. Запуск из исходников

```bash
# Создать и активировать виртуальное окружение
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

# Установить зависимости
pip install -r requirements.txt

# Запустить
python main.py
```

> **Важно про автокликер:** библиотека `pyautogui` управляет настоящей мышью. По умолчанию включён «failsafe» — резкий перевод курсора в верхний левый угол прерывает выполнение. Это спасёт, если что-то пойдёт не так.

---

## 2. Сборка `.exe` для Windows

Сборка производится **на Windows** (PyInstaller не делает кросс-сборку из Linux/macOS).

```cmd
:: 1. Установить Python 3.11 или 3.12 с python.org
:: 2. В корне проекта (рядом с main.py):
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install pyinstaller

:: 3. Сборка одним файлом без консоли
pyinstaller build.spec --clean

:: Готовый exe лежит в dist\FlywerkAutomation.exe
```

После сборки папки `build/` и `dist/` можно очистить, в репозиторий они не коммитятся (см. `.gitignore`).

### Тонкости

- **Антивирус.** Свежесобранный exe от PyInstaller часто триггерит Windows Defender / SmartScreen. Чтобы убрать предупреждения, файл нужно подписать сертификатом (Code Signing). Без подписи Windows покажет «Неизвестный издатель» — это нормально для собственной сборки.
- **Иконка.** Если хочешь свою иконку, добавь в `build.spec` параметр `icon='app.ico'` в блок `EXE(...)` и положи `app.ico` рядом.
- **Размер.** `--onefile` упаковывает всё в один файл (~60 МБ из-за PyQt6). Если нужен компактный запуск — используй спецификацию с `--onedir` (быстрее стартует).

---

## 3. Публикация на GitHub

```bash
# В корне проекта (где лежит main.py):
git init
git add .
git commit -m "Flywerk Automation: initial commit"

# Создать репозиторий на github.com через UI, затем:
git branch -M main
git remote add origin https://github.com/<your-username>/<repo-name>.git
git push -u origin main
```

### Опционально: автосборка `.exe` через GitHub Actions

Создать файл `.github/workflows/build.yml`:

Если файлы лежат в подпапке `desktop-app/` (как в этом проекте):

```yaml
name: Build Windows EXE
on:
  push:
    tags: ['v*']
  workflow_dispatch:

jobs:
  build:
    runs-on: windows-latest
    defaults:
      run:
        working-directory: desktop-app
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: |
          pip install -r requirements.txt
          pip install pyinstaller
          pyinstaller build.spec --clean
      - uses: actions/upload-artifact@v4
        with:
          name: FlywerkAutomation-windows
          path: desktop-app/dist/FlywerkAutomation.exe
```

Если же `main.py`, `build.spec` и `requirements.txt` лежат в корне репозитория — убери блок `defaults: run: working-directory` и измени `path` на `dist/FlywerkAutomation.exe`.

После пуша тега `v1.0.0` GitHub сам соберёт exe. Готовый файл появится в разделе **Actions → нужный прогон → Artifacts → FlywerkAutomation-windows**.

---

## 4. Структура проекта

```
desktop-app/
├── main.py             # вся логика и UI
├── requirements.txt    # зависимости для pip install
├── build.spec          # PyInstaller spec
├── .gitignore
└── README.md
```
