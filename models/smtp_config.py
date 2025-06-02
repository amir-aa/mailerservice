from peewee import *
from datetime import datetime
from models.email_model import BaseModel, db,EmailMessage

class SmtpConfig(BaseModel):
    name = CharField(unique=True)  # Friendly name for this SMTP configuration
    email_address = CharField()  # Email address for this SMTP account
    display_name = CharField(null=True)  # Display name for this email address
    smtp_host = CharField()
    smtp_port = IntegerField()
    username = CharField()
    password = CharField()  # Consider encryption in production
    use_tls = BooleanField(default=True)
    use_ssl = BooleanField(default=False)
    active = BooleanField(default=True)  # Is this config active?
    daily_limit = IntegerField(default=2000)  # Daily sending limit
    hourly_limit = IntegerField(default=100)  # Hourly sending limit
    sent_count_today = IntegerField(default=0)  # Count of emails sent today
    sent_count_hour = IntegerField(default=0)  # Count of emails sent this hour
    last_sent = DateTimeField(null=True)  # Last time an email was sent
    last_reset_daily = DateTimeField(default=datetime.now)  # Last daily counter reset
    last_reset_hourly = DateTimeField(default=datetime.now)  # Last hourly counter reset
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)
    
    def can_send(self):
        """Check if this SMTP config can send more emails"""
        now = datetime.now()
        
        # Reset counters if needed
        self._reset_counters(now)
        
        # Check if active and under limits
        return (
            self.active and 
            self.sent_count_today < self.daily_limit and 
            self.sent_count_hour < self.hourly_limit
        )
    
    def increment_sent_count(self):
        """Increment sent counters"""
        now = datetime.now()
        
        # Reset counters if needed
        self._reset_counters(now)
        
        # Increment counters
        self.sent_count_today += 1
        self.sent_count_hour += 1
        self.last_sent = now
        self.updated_at = now
        self.save()
    
    def _reset_counters(self, now):
        """Reset counters if needed"""
        # Check if we need to reset daily counter
        if now.date() > self.last_reset_daily.date():
            self.sent_count_today = 0
            self.last_reset_daily = now
            self.save()
        
        # Check if we need to reset hourly counter
        hour_diff = (now - self.last_reset_hourly).total_seconds() / 3600
        if hour_diff >= 1:
            self.sent_count_hour = 0
            self.last_reset_hourly = now
            self.save()

# Initialize database and create tables
def initialize_db():
    db.connect()
    db.create_tables([EmailMessage, SmtpConfig], safe=True)
    db.close()
initialize_db()