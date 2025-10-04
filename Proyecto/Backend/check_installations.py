import subprocess
import sys

def check_python():
    try:
        version = sys.version
        print(f"✅ Python: {version.split()[0]}")
        return True
    except Exception as e:
        print(f"❌ Python no encontrado: {e}")
        return False

def check_flask():
    try:
        import flask
        print(f"✅ Flask: {flask.__version__}")
        return True
    except ImportError:
        print("❌ Flask no instalado")
        return False

def check_adb():
    try:
        result = subprocess.run(['adb', 'version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ ADB: {result.stdout.splitlines()[0]}")
            return True
        else:
            print("❌ ADB no encontrado")
            return False
    except Exception as e:
        print(f"❌ Error con ADB: {e}")
        return False

def check_sqlite():
    try:
        import sqlite3
        print(f"✅ SQLite3: {sqlite3.version}")
        return True
    except ImportError:
        print("❌ SQLite3 no disponible")
        return False

if __name__ == "__main__":
    print("🔍 Verificando instalaciones...")
    check_python()
    check_flask()
    check_adb()
    check_sqlite()