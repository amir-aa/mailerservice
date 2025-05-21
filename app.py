from flask import Flask, jsonify
from controllers.email_controller import EmailController, email_bp
from controllers.smtp_controller import SmtpController, smtp_bp
from services.email_service import EmailService
from services.queue_service import EmailQueue
from models.smtp_config import initialize_db
from config import get_config
import atexit

def create_app():
    """Create Flask application"""
    app = Flask(__name__)
    
    # Load configuration
    config = get_config()
    app.config.from_object(config)
    
    # Initialize database
    initialize_db()
    
    # Setup queue service
    queue_service = EmailQueue(
        worker_count=app.config['QUEUE_WORKERS'],
        max_retries=app.config['MAX_RETRIES']
    )
    
    # Setup email service with queue
    email_service = EmailService(queue_service)
    
    # Start queue workers
    queue_service.start_workers()
    
    # Register function to stop workers on app shutdown
    atexit.register(queue_service.stop_workers)
    
    # Setup controllers
    email_controller = EmailController(email_service)
    email_controller.register_routes(email_bp)
    
    smtp_controller = SmtpController(email_service)
    smtp_controller.register_routes(smtp_bp)
    
    # Register blueprints
    app.register_blueprint(email_bp, url_prefix='/api')
    app.register_blueprint(smtp_bp, url_prefix='/api')
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(500)
    def server_error(e):
        return jsonify({'error': 'Internal server error'}), 500
    
    # Root route
    @app.route('/')
    def index():
        return jsonify({
            'service': 'Email Service API',
            'status': 'running',
            'queue_workers': app.config['QUEUE_WORKERS']
        })
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=app.config['DEBUG'])