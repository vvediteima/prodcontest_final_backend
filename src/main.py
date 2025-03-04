from src.app import app
from werkzeug.middleware.dispatcher import DispatcherMiddleware

def default_app(environ, start_response):
    start_response("404 Not Found", [("Content-Type", "text/plain")])
    return [b"Page not found"]

# Монтируем ваше приложение (app) по префиксу /api
application = DispatcherMiddleware(default_app, {
    '/api': app,
})

if __name__ == "__main__":
    # При прямом запуске запускаем приложение обычным способом (без middleware)
    app.run()
