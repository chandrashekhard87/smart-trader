"""
Setup and validation script for NSE Option Chain Trading Bot
Run this first to ensure everything is properly installed
"""

import sys
import subprocess
import os

def check_python_version():
    """Check if Python version is >= 3.8"""
    print("Checking Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"Python {version.major}.{version.minor}.{version.micro} OK")
        return True
    else:
        print(f"ERROR Python 3.8+ required. Current: {version.major}.{version.minor}")
        return False

def check_dependencies():
    """Check if all required packages are installed"""
    print("\nChecking dependencies...")
    
    required_packages = {
        'requests': 'requests',
        'pandas': 'pandas',
        'numpy': 'numpy',
        'dotenv': 'python-dotenv',
        'pytz': 'pytz',
        'schedule': 'schedule',
        'ta': 'ta'
    }
    
    missing_packages = []
    
    for import_name, package_name in required_packages.items():
        try:
            __import__(import_name)
            print(f"{package_name} installed")
        except ImportError:
            print(f"ERROR {package_name} NOT installed")
            missing_packages.append(package_name)
    
    return missing_packages

def install_dependencies(packages):
    """Install missing packages"""
    if not packages:
        print("\nAll dependencies installed!")
        return True
    
    print(f"\nInstalling {len(packages)} missing package(s)...")
    try:
        for package in packages:
            print(f"  Installing {package}...")
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", package
            ])
        print("All dependencies installed successfully!")
        return True
    except Exception as e:
        print(f"ERROR Error installing dependencies: {str(e)}")
        return False

def check_configuration():
    """Check if configuration file exists and is valid"""
    print("\nChecking configuration...")
    
    if not os.path.exists('config.py'):
print("ERROR config.py not found")
    return False
    
    print("config.py exists")
    
    # Check for required configuration variables
    try:
        with open('config.py', 'r') as f:
            content = f.read()
            
        required_configs = [
            'UPSTOX_API_KEY',
            'UPSTOX_API_SECRET',
            'INDICES',
            'OPTION_CHAIN_INTERVALS'
        ]
        
        for config in required_configs:
            if config in content:
                print(f"OK {config} configured")
            else:
                print(f"WARNING {config} not found in config.py")
        
        return True
    except Exception as e:
        print(f"ERROR Error reading config.py: {str(e)}")

def check_api_credentials():
    """Check if API credentials are set"""
    print("\nChecking API credentials...")
    
    try:
        from config import UPSTOX_API_KEY, UPSTOX_API_SECRET
        
        if UPSTOX_API_KEY == "YOUR_API_KEY_HERE":
            print("WARNING UPSTOX_API_KEY not configured in config.py")
            print("  - Add your API key from https://upstox.com/developer/api/")
            return False
        
        if UPSTOX_API_SECRET == "YOUR_API_SECRET_HERE":
            print("WARNING UPSTOX_API_SECRET not configured in config.py")
            print("  - Add your API secret from https://upstox.com/developer/api/")
            return False
        
        print("API credentials configured")
        return True
        
    except ImportError as e:
        print(f"ERROR Error importing config: {str(e)}")
        return False

def check_access_token():
    """Check if access token is available"""
    print("\nChecking access token...")
    
    if os.path.exists('access_token.txt'):
        print("Access token file exists")
        try:
            with open('access_token.txt', 'r') as f:
                token = f.read().strip()
            if token:
                print(f"Access token present ({len(token)} chars)")
                return True
        except:
            pass
    
    print("WARNING Access token not found")
    print("  - Run: python auth.py")
    return False

def test_imports():
    """Test if all modules can be imported"""
    print("\nTesting module imports...")
    
    modules = [
        'config',
        'upstox_api',
        'trend_analyzer',
        'order_manager',
        'trading_bot',
        'auth'
    ]
    
    success = True
    for module in modules:
        try:
            __import__(module)
            print(f"{module} imported successfully")
        except ImportError as e:
            print(f"ERROR Error importing {module}: {str(e)}")
            success = False
    
    return success

def create_env_template():
    """Create .env template if it doesn't exist"""
    print("\nChecking .env template...")
    
    env_template = """.env
UPSTOX_API_KEY=your_api_key_here
UPSTOX_API_SECRET=your_api_secret_here
UPSTOX_ACCESS_TOKEN=your_access_token_here
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
"""
    
    if not os.path.exists('.env.example'):
        try:
            with open('.env.example', 'w') as f:
                f.write(env_template)
            print("Created .env.example template")
        except Exception as e:
            print(f"WARNING Could not create .env.example: {str(e)}")
    else:
        print(".env.example already exists")

def print_summary(results):
    """Print validation summary"""
    print("\n" + "="*60)
    print("VALIDATION SUMMARY")
    print("="*60)
    
    for check_name, passed in results.items():
        status = "OK" if passed else "ERROR"
        print(f"{status} {check_name}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\nAll checks passed! You're ready to go.")
        print("\nNext steps:")
        print("  1. Configure API credentials in config.py")
        print("  2. Run: python auth.py (for access token)")
        print("  3. Run: python examples.py (test the system)")
        print("  4. Run: python trading_bot.py (start trading)")
    else:
        print("\nSome checks failed. Please fix the issues above.")
    
    print("="*60 + "\n")
    
    return all_passed

def main():
    """Run all validation checks"""
    print("="*60)
    print("NSE OPTION CHAIN TRADING BOT - SETUP VALIDATION")
    print("="*60 + "\n")
    
    # Run checks
    results = {
        "Python Version": check_python_version()
    }
    
    # Check dependencies
    missing_packages = check_dependencies()
    if missing_packages:
        print(f"\nInstalling missing packages: {missing_packages}")
        install_dependencies(missing_packages)
    
    results["Configuration File"] = check_configuration()
    results["API Credentials"] = check_api_credentials()
    results["Access Token"] = check_access_token()
    results["Module Imports"] = test_imports()
    
    # Create .env template
    create_env_template()
    
    # Print summary
    all_good = print_summary(results)
    
    return 0 if all_good else 1

if __name__ == "__main__":
    sys.exit(main())
