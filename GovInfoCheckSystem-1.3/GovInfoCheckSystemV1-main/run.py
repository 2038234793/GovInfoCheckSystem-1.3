from app import create_app, socketio

app = create_app()

if __name__ == '__main__':
    print("Starting server...")
    try:
        socketio.run(app, debug=True, host='127.0.0.1', port=5000, allow_unsafe_werkzeug=True)
    except Exception as e:
        print(f"Error starting server: {e}")
