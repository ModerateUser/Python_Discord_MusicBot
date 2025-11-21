"""
Discord Music Bot - Main Entry Point (Refactored)
A feature-rich music bot with security, playlist management, and advanced AI features
Includes AI music synthesis capabilities

REFACTORED: Now uses modular architecture with dependency injection
- No global state variables
- Clean separation of concerns
- Service lifecycle management
- Comprehensive error handling
"""
from core.bot_core import main

if __name__ == '__main__':
    import asyncio
    import sys
    from utils.logger import setup_logger
    
    logger = setup_logger()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info('Bot stopped by user')
    except Exception as e:
        logger.error(f'Fatal error: {e}', exc_info=True)
        sys.exit(1)
