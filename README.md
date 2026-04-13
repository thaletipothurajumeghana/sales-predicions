# Sales Predictions Flask App

A Flask application with AI-driven retail forecasting and simple e-commerce flows (login/register/shop/dashboard). This repo includes dataset-backed training, SQLite persistence, and frontend pages.

## ⚙️ What’s included

- `app.py`: Flask server (routes: `/`, `/login`, `/register`, `/shop`, `/buy`, `/dashboard`, `/orders`)
- `retail_model.py`: `RetailAI` class with XGBoost, prophet, risk model, and inventory logic
- `modified_sales_dataset.csv`: primary training dataset
- `database.db`: local SQLite data (users + orders)
- `templates/`: Jinja HTML templates
- `static/style.css`

## 🛠️ Setup

1. Clone repository:

   ```bash
   git clone https://github.com/<your-username>/<repo-name>.git
   cd "sales predicions"
   ```

2. Create virtualenv and install dependencies:

   ```bash
   python -m venv venv
   venv\Scripts\activate   # Windows
   pip install -r requirements.txt
   ```

3. Run the app:

   ```bash
   python app.py
   ```

4. Open browser at http://127.0.0.1:5000

## 🔐 Admin account

- default admin email is now configured via environment variable `ADMIN_EMAIL`
- password storage uses bcrypt hashing for deployment-ready security

## 🚀 Deployment-ready setup

### GitHub repository

- commit and push all files (except `.gitignore` excluded files)

### Deploy options

GitHub Pages does not support backend Flask apps. Use one of these:

- Heroku (free/prototype): `Procfile` provided
- Railway / Render / Replit / PythonAnywhere
- Azure App Service / AWS Elastic Beanstalk

### Environment variables

Create a `.env` file locally or configure env vars in your platform:

```env
SECRET_KEY=your-strong-secret-key
ADMIN_EMAIL=admin@example.com
DATABASE_PATH=database.db
MODEL_DATA_PATH=modified_sales_dataset.csv
DEBUG=False
```

## 🧹 Recommended `.gitignore`

- Excludes `database.db`, dataset, virtualenv, and logs

## 🧩 Improvements

- Use environment variables for `SECRET_KEY`, admin email, database path, and model dataset path
- Secure password flow with hashing + salted auth (`bcrypt`)
- Run with Gunicorn in production via `Procfile`
- Add tests (`pytest`) and CI workflows

## 📝 License

MIT License
