# 📧 Email Service API

A robust, scalable email sending service with queue management, multiple SMTP accounts support, and congestion control.

## 🌟 Features
- ✉️ **Multiple SMTP Account Support**: Configure and use multiple email accounts with different credentials
- 🔄 **Queue Management**: Built-in queue system for congestion control using Python’s queue library
- 📊 **Priority-based Sending**: Send emails with different priority levels (1-5)
- 📁 **Database Storage**: Store emails and configurations in SQLite using Peewee ORM
- 📝 **HTML Email Support**: Send rich HTML emails
- 🔁 **Automatic Retries**: Configurable retry mechanism for failed emails
- ⚖️ **Rate Limiting**: Configurable daily and hourly sending limits per SMTP account
- 🔍 **Email Status Tracking**: Track email status (queued, sending, sent, failed)

## 📋 Requirements
- Python 3.7+
- Flask
- Peewee ORM
- SQLite

## 🚀 Installation
```bash
# Clone the repository
git clone https://github.com/yourusername/email-service-api.git
cd email-service-api

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize the database
python -c "from models import initialize_db; initialize_db()"

# Run the application
python app.py
```

## 📝 Configuration
Create a `.env` file in the project root:

```ini
SECRET_KEY=your-secret-key-here
FLASK_ENV=development  # or production
QUEUE_WORKERS=2
MAX_RETRIES=3
```

## 📚 API Documentation

### SMTP Configuration Endpoints

#### 🔹 Create SMTP Configuration
```bash
curl -X POST http://localhost:5000/api/smtp-configs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Gmail Account",
    "email_address": "your-email@gmail.com",
    "display_name": "Your Name",
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 587,
    "username": "your-email@gmail.com",
    "password": "your-password-or-app-password",
    "use_tls": true,
    "daily_limit": 500,
    "hourly_limit": 50
  }'
```

**Response:**
```json
{
  "message": "SMTP configuration created successfully",
  "config_id": 1
}
```

#### 🔹 List SMTP Configurations
```bash
curl -X GET http://localhost:5000/api/smtp-configs
```

**Response:**
```json
[
  {
    "id": 1,
    "name": "Gmail Account",
    "email_address": "your-email@gmail.com",
    "active": true,
    "daily_limit": 500,
    "sent_count_today": 0,
    "sent_count_hour": 0
  }
]
```

#### 🔹 Get SMTP Configuration Details
```bash
curl -X GET http://localhost:5000/api/smtp-configs/1
```

**Response:**
```json
{
  "id": 1,
  "name": "Gmail Account",
  "email_address": "your-email@gmail.com",
  "display_name": "Your Name",
  "smtp_host": "smtp.gmail.com",
  "smtp_port": 587,
  "username": "your-email@gmail.com",
  "active": true,
  "daily_limit": 500,
  "hourly_limit": 50,
  "sent_count_today": 0,
  "sent_count_hour": 0,
  "last_sent": null,
  "created_at": "2023-05-24T10:30:00.000000"
}
```

#### 🔹 Update SMTP Configuration
```bash
curl -X PUT http://localhost:5000/api/smtp-configs/1 \
  -H "Content-Type: application/json" \
  -d '{
    "active": false,
    "daily_limit": 1000
  }'
```

**Response:**
```json
{
  "message": "SMTP configuration updated successfully"
}
```

### Email Endpoints

#### 🔹 Create and Queue Email
```bash
curl -X POST http://localhost:5000/api/emails \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Test Email",
    "recipients": ["recipient1@example.com", "recipient2@example.com"],
    "html_content": "<html><body><h1>Hello!</h1><p>This is a test email.</p></body></html>",
    "cc": ["cc1@example.com"],
    "bcc": ["bcc1@example.com"],
    "priority": 1,
    "smtp_config_id": 1
  }'
```

**Response:**
```json
{
  "message": "Email created and queued successfully",
  "email_id": 1
}
```

#### 🔹 Get Email Details
```bash
curl -X GET http://localhost:5000/api/emails/1
```

**Response:**
```json
{
  "id": 1,
  "subject": "Test Email",
  "sender": "your-email@gmail.com",
  "sender_name": "Your Name",
  "recipients": ["recipient1@example.com", "recipient2@example.com"],
  "cc": ["cc1@example.com"],
  "bcc": ["bcc1@example.com"],
  "status": "queued",
  "priority": 1,
  "retry_count": 0,
  "smtp_config": "Gmail Account",
  "created_at": "2023-05-24T10:35:00.000000",
  "updated_at": "2023-05-24T10:35:00.000000",
  "sent_at": null,
  "error_message": null
}
```

#### 🔹 Get Emails by Status
```bash
curl -X GET "http://localhost:5000/api/emails/status/queued?limit=50"
```

**Response:**
```json
[
  {
    "id": 1,
    "subject": "Test Email",
    "status": "queued",
    "priority": 1,
    "retry_count": 0,
    "created_at": "2023-05-24T10:35:00.000000"
  }
]
```

## 📊 Email Status Flow
```
┌─────────┐     ┌─────────┐     ┌─────────┐
│ queued  │ ──▶ │ sending │ ──▶ │  sent   │
└─────────┘     └─────────┘     └─────────┘
     │                │
     ▼                ▼
┌─────────┐     ┌─────────┐
│  retry  │ ◀── │ failed  │
└─────────┘     └─────────┘
```

## 🧪 Testing
```bash
# Install test dependencies
pip install pytest pytest-cov

# Run tests with coverage report
pytest -v --cov=.
```

## 🔧 Architecture

The project follows clean architecture principles:

```
email_service/
├── app.py                # Flask application entry point
├── config.py             # Configuration settings
├── models/               # Peewee models
├── services/             # Service layer
├── controllers/          # API controllers
└── utils/                # Utility functions
```

## 📝 Models

### EmailMessage
- subject: Email subject
- sender: Sender email address
- recipients: JSON string of recipients
- cc: JSON string of CC recipients (optional)
- bcc: JSON string of BCC recipients (optional)
- html_content: HTML content of the email
- status: Email status (queued, sending, sent, failed)
- smtp_config_id: Reference to SMTP configuration
- priority: Priority level (1-5, 1 is highest)
- retry_count: Number of retry attempts

### SmtpConfig
- name: Friendly name for this SMTP configuration
- email_address: Email address for this SMTP account
- display_name: Display name for this email address
- smtp_host: SMTP server hostname
- smtp_port: SMTP server port
- username: SMTP username
- password: SMTP password
- use_tls: Whether to use TLS
- use_ssl: Whether to use SSL
- active: Is this config active?
- daily_limit: Daily sending limit
- hourly_limit: Hourly sending limit

## 🔒 Security Considerations
- Store passwords securely (consider encryption in production)
- Use environment variables for sensitive configuration
- Implement rate limiting to prevent abuse
- Consider implementing authentication for API endpoints

## 🚀 Deployment

For production deployment:

Set `FLASK_ENV=production` in your environment and use a production WSGI server like Gunicorn:

```bash
pip install gunicorn
gunicorn app:create_app()
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

Made with ❤️ by [Amir](https://linkedin.com/in/amir-ahmadabadiha-259113175)

[Report Bug](mailto:amirdev2024@gmail.com) • [Request Feature](mailto:amirdev2024@gmail.com)

Please check my Online storage as well
[Please check my Online storage as well](https://filesaver.ir)