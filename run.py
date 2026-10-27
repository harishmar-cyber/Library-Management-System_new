import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() in ('true', '1')
    print("=" * 65)
    print("  Lavender Library Management System - DSA Powered")
    print(f"  Starting local server on http://127.0.0.1:{port}")
    print("=" * 65)
    app.run(host='127.0.0.1', port=port, debug=debug)
