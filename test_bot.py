#!/usr/bin/env python3
"""
Diagnostic script to test bot components and identify errors
Run this to see what's actually broken
"""
import sys
import traceback
from pathlib import Path

def test_imports():
    """Test if all imports work"""
    print("=" * 70)
    print("TESTING IMPORTS")
    print("=" * 70)
    
    tests = [
        ("discord", "import discord"),
        ("discord.ext.commands", "from discord.ext import commands"),
        ("yt_dlp", "import yt_dlp"),
        ("core.config", "from core.config import config"),
        ("core.bot_core", "from core.bot_core import MusicBot, create_bot"),
        ("core.service_manager", "from core.service_manager import ServiceManager"),
        ("core.container", "from core.container import get_container"),
        ("services.audio_service", "from services.audio_service import AudioService"),
        ("utils.logger", "from utils.logger import setup_logger"),
        ("cogs.music", "import cogs.music"),
        ("cogs.playlist", "import cogs.playlist"),
        ("cogs.help", "import cogs.help"),
    ]
    
    passed = 0
    failed = 0
    
    for name, import_stmt in tests:
        try:
            exec(import_stmt)
            print(f"✅ {name}")
            passed += 1
        except Exception as e:
            print(f"❌ {name}: {e}")
            failed += 1
    
    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0

def test_config():
    """Test configuration loading"""
    print("\n" + "=" * 70)
    print("TESTING CONFIGURATION")
    print("=" * 70)
    
    try:
        from core.config import config
        
        print(f"✅ Config loaded")
        print(f"   Token: {'*' * 20}...{config.token[-10:] if len(config.token) > 10 else 'NOT SET'}")
        print(f"   Owner ID: {config.owner_id}")
        print(f"   Prefix: {config.command_prefix}")
        print(f"   Playing: {config.playing}")
        
        if not config.token:
            print("⚠️  WARNING: Bot token not set!")
            return False
        
        if not config.owner_id:
            print("⚠️  WARNING: Owner ID not set!")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Config error: {e}")
        traceback.print_exc()
        return False

def test_audio_service():
    """Test audio service initialization"""
    print("\n" + "=" * 70)
    print("TESTING AUDIO SERVICE")
    print("=" * 70)
    
    try:
        from services.audio_service import AudioService
        
        audio = AudioService()
        print(f"✅ AudioService created")
        print(f"   FFmpeg path: {audio.ffmpeg_path}")
        print(f"   FFmpeg validated: {audio._ffmpeg_validated}")
        print(f"   Thread pool: {audio._executor._max_workers} workers")
        
        if not audio.is_ffmpeg_available():
            print("⚠️  WARNING: FFmpeg not available - audio playback will not work!")
            print("   Install FFmpeg:")
            print("   - Windows: https://ffmpeg.org/download.html")
            print("   - Linux: sudo apt install ffmpeg")
            print("   - macOS: brew install ffmpeg")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ AudioService error: {e}")
        traceback.print_exc()
        return False

def test_bot_creation():
    """Test bot instance creation"""
    print("\n" + "=" * 70)
    print("TESTING BOT CREATION")
    print("=" * 70)
    
    try:
        from core.bot_core import create_bot
        
        bot = create_bot()
        print(f"✅ Bot instance created")
        print(f"   Type: {type(bot).__name__}")
        print(f"   Command prefix: {bot.command_prefix}")
        print(f"   Intents: {bot.intents}")
        print(f"   Service manager: {bot.service_manager}")
        print(f"   NLP handler: {bot.nlp_handler}")
        
        return True
        
    except Exception as e:
        print(f"❌ Bot creation error: {e}")
        traceback.print_exc()
        return False

def test_cog_loading():
    """Test if cogs can be loaded"""
    print("\n" + "=" * 70)
    print("TESTING COG LOADING")
    print("=" * 70)
    
    cogs = [
        'cogs.help',
        'cogs.music',
        'cogs.playlist',
        'cogs.queue_manager',
        'cogs.ai_music'
    ]
    
    passed = 0
    failed = 0
    
    for cog in cogs:
        try:
            exec(f"import {cog}")
            print(f"✅ {cog}")
            passed += 1
        except Exception as e:
            print(f"❌ {cog}: {e}")
            failed += 1
    
    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0

def test_dashboard():
    """Test dashboard components"""
    print("\n" + "=" * 70)
    print("TESTING DASHBOARD COMPONENTS")
    print("=" * 70)
    
    try:
        # Test if bot_with_dashboard.py exists
        dashboard_file = Path("bot_with_dashboard.py")
        if not dashboard_file.exists():
            print("❌ bot_with_dashboard.py not found")
            return False
        
        print(f"✅ bot_with_dashboard.py exists")
        
        # Test dashboard imports
        try:
            from web_dashboard.app import app
            print(f"✅ Dashboard app imported")
        except Exception as e:
            print(f"❌ Dashboard app import failed: {e}")
            return False
        
        try:
            from services.dashboard_bridge import DashboardBridge
            print(f"✅ DashboardBridge imported")
        except Exception as e:
            print(f"❌ DashboardBridge import failed: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Dashboard test error: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all diagnostic tests"""
    print("\n" + "=" * 70)
    print("DISCORD MUSIC BOT - DIAGNOSTIC TEST")
    print("=" * 70)
    print()
    
    results = {
        "Imports": test_imports(),
        "Configuration": test_config(),
        "Audio Service": test_audio_service(),
        "Bot Creation": test_bot_creation(),
        "Cog Loading": test_cog_loading(),
        "Dashboard": test_dashboard(),
    }
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    total_passed = sum(results.values())
    total_tests = len(results)
    
    print(f"\nTotal: {total_passed}/{total_tests} tests passed")
    
    if total_passed == total_tests:
        print("\n🎉 All tests passed! Bot should work.")
        print("\nTo start the bot:")
        print("  1. Bot only: python bot.py")
        print("  2. Bot + Dashboard: python bot_with_dashboard.py")
        print("  3. Use launcher: launch.bat (Windows) or ./launch.sh (Linux/Mac)")
        return 0
    else:
        print("\n⚠️  Some tests failed. Fix the errors above before running the bot.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
