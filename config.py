"""
Configuration file for Signal Bolt
"""

import os
from typing import Dict, Any

class Config:
    """Configuration class for Signal Bolt"""
    
    # General settings
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # WebSocket settings
    WS_HOST = os.getenv('WS_HOST', 'localhost')
    WS_PORT = int(os.getenv('WS_PORT', '8765'))
    
    # API settings
    API_HOST = os.getenv('API_HOST', 'localhost')
    API_PORT = int(os.getenv('API_PORT', '8000'))
    
    # Redis settings (for distributed signal sharing)
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
    REDIS_DB = int(os.getenv('REDIS_DB', '0'))
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)
    
    # Signal settings
    DEFAULT_SIGNAL_EXPIRY_MINUTES = int(os.getenv('SIGNAL_EXPIRY_MINUTES', '30'))
    MAX_ACTIVE_SIGNALS = int(os.getenv('MAX_ACTIVE_SIGNALS', '1000'))
    CLEANUP_INTERVAL_SECONDS = int(os.getenv('CLEANUP_INTERVAL_SECONDS', '60'))
    
    # Platform configurations
    PLATFORMS = {
        'iq_options': {
            'name': 'IQ Options',
            'enabled': os.getenv('IQ_OPTIONS_ENABLED', 'True').lower() == 'true',
            'websocket_url': os.getenv('IQ_OPTIONS_WS_URL', 'wss://api.iqoption.com/ws/'),
            'api_url': os.getenv('IQ_OPTIONS_API_URL', 'https://api.iqoption.com/api/'),
            'api_key': os.getenv('IQ_OPTIONS_API_KEY', ''),
            'username': os.getenv('IQ_OPTIONS_USERNAME', ''),
            'password': os.getenv('IQ_OPTIONS_PASSWORD', ''),
        },
        'binary_options': {
            'name': 'Binary Options',
            'enabled': os.getenv('BINARY_OPTIONS_ENABLED', 'True').lower() == 'true',
            'websocket_url': os.getenv('BINARY_OPTIONS_WS_URL', ''),
            'api_url': os.getenv('BINARY_OPTIONS_API_URL', ''),
        },
        'demo': {
            'name': 'Demo Platform',
            'enabled': os.getenv('DEMO_ENABLED', 'True').lower() == 'true',
            'websocket_url': None,
            'api_url': None,
        }
    }
    
    # Trading symbols configuration
    SYMBOLS = {
        'forex': ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD', 'NZDUSD', 'USDCHF'],
        'crypto': ['BTCUSD', 'ETHUSD', 'LTCUSD', 'XRPUSD', 'ADAUSD'],
        'stocks': ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA'],
        'commodities': ['GOLD', 'SILVER', 'OIL', 'GAS'],
        'indices': ['SPX500', 'NAS100', 'DOW30', 'FTSE100', 'DAX30']
    }
    
    # Signal filtering defaults
    DEFAULT_FILTERS = {
        'min_confidence': 0.6,
        'min_strength': 2,
        'max_age_minutes': 30,
        'platforms': ['iq_options', 'demo'],
        'symbols': None,  # All symbols
        'signal_types': None  # All signal types
    }
    
    # Technical analysis settings
    TECHNICAL_ANALYSIS = {
        'rsi_period': 14,
        'macd_fast': 12,
        'macd_slow': 26,
        'macd_signal': 9,
        'bollinger_period': 20,
        'bollinger_std': 2,
        'sma_periods': [5, 10, 20, 50, 200],
        'ema_periods': [5, 10, 20, 50, 200]
    }
    
    # Notification settings
    NOTIFICATIONS = {
        'email_enabled': os.getenv('EMAIL_ENABLED', 'False').lower() == 'true',
        'email_smtp_server': os.getenv('EMAIL_SMTP_SERVER', ''),
        'email_smtp_port': int(os.getenv('EMAIL_SMTP_PORT', '587')),
        'email_username': os.getenv('EMAIL_USERNAME', ''),
        'email_password': os.getenv('EMAIL_PASSWORD', ''),
        'email_recipients': os.getenv('EMAIL_RECIPIENTS', '').split(','),
        
        'telegram_enabled': os.getenv('TELEGRAM_ENABLED', 'False').lower() == 'true',
        'telegram_bot_token': os.getenv('TELEGRAM_BOT_TOKEN', ''),
        'telegram_chat_id': os.getenv('TELEGRAM_CHAT_ID', ''),
        
        'webhook_enabled': os.getenv('WEBHOOK_ENABLED', 'False').lower() == 'true',
        'webhook_url': os.getenv('WEBHOOK_URL', ''),
        'webhook_secret': os.getenv('WEBHOOK_SECRET', ''),
    }
    
    # Database settings (for signal history)
    DATABASE = {
        'type': os.getenv('DB_TYPE', 'sqlite'),  # sqlite, postgresql, mysql
        'url': os.getenv('DATABASE_URL', 'sqlite:///signal_bolt.db'),
        'echo': DEBUG
    }
    
    # Rate limiting
    RATE_LIMITS = {
        'signals_per_minute': 100,
        'api_requests_per_minute': 1000,
        'websocket_connections': 100
    }
    
    @classmethod
    def get_platform_config(cls, platform_name: str) -> Dict[str, Any]:
        """Get configuration for a specific platform"""
        return cls.PLATFORMS.get(platform_name, {})
    
    @classmethod
    def is_platform_enabled(cls, platform_name: str) -> bool:
        """Check if a platform is enabled"""
        platform_config = cls.get_platform_config(platform_name)
        return platform_config.get('enabled', False)
    
    @classmethod
    def get_all_symbols(cls) -> list:
        """Get all configured symbols"""
        all_symbols = []
        for category, symbols in cls.SYMBOLS.items():
            all_symbols.extend(symbols)
        return all_symbols