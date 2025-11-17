from flask import Flask, redirect, url_for, session
from config import Config
from src.models.database import init_db

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Inicializar base de datos
    with app.app_context():
        init_db()
    
    # Registrar blueprints
    from src.auth.routes import auth_bp
    from src.traffic.routes import traffic_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(traffic_bp)
    
    @app.route('/')
    def index():
        if 'user_id' in session:
            return redirect(url_for('traffic.dashboard'))
        return redirect(url_for('auth.login'))
    
    return app

if __name__ == '__main__':
    app = create_app()
    print("Servidor iniciado en http://127.0.0.1:5000")
    app.run(host='0.0.0.0', port='5000', debug=False, threaded=True)