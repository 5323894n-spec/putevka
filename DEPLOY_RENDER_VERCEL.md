# Размещение программы на Render и Vercel

Эта инструкция описывает вариант публикации:

- **GitHub** хранит код: `https://github.com/5323894n-spec/putevka`
- **Render** запускает backend FastAPI и PostgreSQL
- **Vercel** запускает frontend React/Vite

## 1. Что получится

После настройки будут два адреса:

- Backend API на Render: примерно `https://putevka-api.onrender.com`
- Frontend на Vercel: примерно `https://putevka.vercel.app`

Пользователи открывают адрес Vercel. Frontend обращается к backend на Render.

## 2. Подготовка GitHub

Код уже опубликован:

```text
https://github.com/5323894n-spec/putevka
```

Перед деплоем убедитесь, что последние изменения отправлены:

```bash
git status
git push
```

## 3. Создание PostgreSQL на Render

1. Откройте Render: `https://dashboard.render.com`
2. Нажмите **New** -> **Postgres**.
3. Укажите имя, например:

```text
putevka-db
```

4. Region выберите тот же, где будет backend.
5. Создайте базу.
6. После создания откройте страницу базы.
7. Найдите **Internal Database URL**.

Он понадобится для переменной:

```text
DATABASE_URL
```

Render рекомендует использовать internal URL для сервисов Render в том же регионе.

## 4. Размещение backend на Render

1. В Render нажмите **New** -> **Web Service**.
2. Подключите GitHub-репозиторий:

```text
5323894n-spec/putevka
```

3. В настройках сервиса укажите:

```text
Name: putevka-api
Root Directory: backend
Runtime: Python 3
Build Command: pip install -r requirements.txt
Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

4. Добавьте Environment Variables:

```text
DATABASE_URL=<Internal Database URL из Render Postgres>
JWT_SECRET=<любая длинная случайная строка>
```

Пример `JWT_SECRET`:

```text
change-this-to-long-random-secret-2026
```

5. Нажмите **Create Web Service**.
6. Дождитесь окончания deploy.
7. Откройте адрес:

```text
https://ВАШ_BACKEND.onrender.com/health
```

Если все нормально, будет ответ:

```json
{"status":"ok"}
```

## 5. Размещение frontend на Vercel

1. Откройте Vercel: `https://vercel.com`
2. Нажмите **Add New** -> **Project**.
3. Импортируйте GitHub-репозиторий:

```text
5323894n-spec/putevka
```

4. В настройках проекта укажите:

```text
Framework Preset: Vite
Root Directory: frontend
Build Command: npm run build
Output Directory: dist
Install Command: npm install
```

5. Добавьте Environment Variable:

```text
VITE_API_URL=https://ВАШ_BACKEND.onrender.com
```

Важно: без `/` в конце.

6. Нажмите **Deploy**.
7. После сборки откройте адрес Vercel.

## 6. Проверка после публикации

Проверьте по порядку:

1. Backend:

```text
https://ВАШ_BACKEND.onrender.com/health
```

Ожидаемый ответ:

```json
{"status":"ok"}
```

2. Frontend:

```text
https://ВАШ_FRONTEND.vercel.app
```

3. Во frontend откройте **База данных** и попробуйте добавить тестового водителя.
4. Если запись сохранилась и появилась в таблице, связь Vercel -> Render -> PostgreSQL работает.

## 7. Частые ошибки

### Frontend открылся, но данные не загружаются

Проверьте переменную Vercel:

```text
VITE_API_URL=https://ВАШ_BACKEND.onrender.com
```

После изменения переменных на Vercel нужно сделать новый Deploy.

### Backend не запускается на Render

Проверьте:

```text
Root Directory: backend
Build Command: pip install -r requirements.txt
Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### Ошибка подключения к базе

Проверьте переменную Render:

```text
DATABASE_URL=<Internal Database URL>
```

Backend и база должны быть в одном регионе Render.

### После изменения кода сайт не обновился

1. Отправьте изменения в GitHub:

```bash
git add .
git commit -m "Update deployment"
git push
```

2. Render и Vercel обычно сами запускают новый deploy после push.

## 8. Официальные инструкции

- Render FastAPI: `https://render.com/docs/deploy-fastapi`
- Render PostgreSQL: `https://render.com/docs/postgresql-creating-connecting`
- Vercel Vite: `https://vercel.com/docs/frameworks/frontend/vite`
- Vercel Environment Variables: `https://vercel.com/docs/environment-variables`

