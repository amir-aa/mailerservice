from peewee import *
from datetime import datetime
import json

# Database instance
db = SqliteDatabase('emails.db')

class BaseModel(Model):
    class Meta:
        database = db

class EmailMessage(BaseModel):
    subject = CharField()
    sender = CharField()
    sender_name = CharField(null=True)  # Optional sender name
    recipients = CharField()  # JSON string of recipients
    cc = CharField(null=True)  # JSON string of CC recipients
    bcc = CharField(null=True)  # JSON string of BCC recipients
    html_content = TextField()
    status = CharField(default='queued')  # queued, sending, sent, failed
    error_message = TextField(null=True)
    smtp_config_id = IntegerField()  # Reference to SMTP configuration
    priority = IntegerField(default=1)  # Priority: 1 (highest) to 5 (lowest)
    retry_count = IntegerField(default=0)  # Number of retry attempts
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)
    sent_at = DateTimeField(null=True)
    
    def get_recipients_list(self):
        """Convert recipients JSON string to list"""
        return json.loads(self.recipients)
    
    def get_cc_list(self):
        """Convert CC JSON string to list"""
        return json.loads(self.cc) if self.cc else []
    
    def get_bcc_list(self):
        """Convert BCC JSON string to list"""
        return json.loads(self.bcc) if self.bcc else []
    
    def update_status(self, status, error_message=None):
        """Update email status"""
        self.status = status
        self.updated_at = datetime.now()
        
        if status == 'sent':
            self.sent_at = datetime.now()
        
        if error_message:
            self.error_message = error_message
            
        self.save()
    
    def increment_retry(self):
        """Increment retry count"""
        self.retry_count += 1
        self.save()