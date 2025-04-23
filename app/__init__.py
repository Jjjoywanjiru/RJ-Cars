from flask import Flask

def create_app(config_class='config'):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Register blueprints/routes
    from app.routes import bp
    app.register_blueprint(bp)

    return app