#!/usr/bin/env python3
"""
Signal Bolt - Real-time Trading Signal Tracker for Options Trading
Supports platforms like IQ Options and other trading platforms
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, asdict
from enum import Enum
import websockets
import aiohttp
from collections import defaultdict, deque
import threading
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('signal_bolt.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SignalType(Enum):
    """Types of trading signals"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    STRONG_BUY = "STRONG_BUY"
    STRONG_SELL = "STRONG_SELL"

class SignalStrength(Enum):
    """Signal strength levels"""
    WEAK = 1
    MODERATE = 2
    STRONG = 3
    VERY_STRONG = 4
    EXTREME = 5

class TimeFrame(Enum):
    """Trading time frames"""
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    M30 = "30m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"

@dataclass
class TradingSignal:
    """Represents a trading signal"""
    id: str
    symbol: str
    signal_type: SignalType
    strength: SignalStrength
    timeframe: TimeFrame
    price: float
    timestamp: datetime
    expiry_time: datetime
    confidence: float  # 0.0 to 1.0
    platform: str
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['expiry_time'] = self.expiry_time.isoformat()
        data['signal_type'] = self.signal_type.value
        data['strength'] = self.strength.value
        data['timeframe'] = self.timeframe.value
        return data

@dataclass
class SignalFilter:
    """Filter criteria for signals"""
    min_confidence: float = 0.5
    min_strength: int = 2
    max_age_minutes: int = 60
    platforms: List[str] = None
    symbols: List[str] = None
    signal_types: List[SignalType] = None

class SignalAnalyzer:
    """Analyzes market data and generates trading signals"""
    
    def __init__(self):
        self.price_history = defaultdict(lambda: deque(maxlen=1000))
        self.volume_history = defaultdict(lambda: deque(maxlen=1000))
        self.rsi_period = 14
        self.macd_fast = 12
        self.macd_slow = 26
        self.macd_signal = 9
    
    def add_price_data(self, symbol: str, price: float, volume: float, timestamp: datetime):
        """Add new price data for analysis"""
        self.price_history[symbol].append({
            'price': price,
            'volume': volume,
            'timestamp': timestamp
        })
    
    def calculate_rsi(self, symbol: str, period: int = None) -> float:
        """Calculate RSI for a symbol"""
        if period is None:
            period = self.rsi_period
        
        prices = [data['price'] for data in self.price_history[symbol]]
        if len(prices) < period + 1:
            return 50.0  # Neutral RSI
        
        gains = []
        losses = []
        
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        if len(gains) < period:
            return 50.0
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_macd(self, symbol: str) -> Dict[str, float]:
        """Calculate MACD for a symbol"""
        prices = [data['price'] for data in self.price_history[symbol]]
        
        if len(prices) < self.macd_slow:
            return {'macd': 0, 'signal': 0, 'histogram': 0}
        
        # Calculate EMAs
        ema_fast = self._calculate_ema(prices, self.macd_fast)
        ema_slow = self._calculate_ema(prices, self.macd_slow)
        
        macd_line = ema_fast - ema_slow
        
        # Calculate signal line (EMA of MACD)
        macd_values = [macd_line]  # Simplified for this example
        signal_line = self._calculate_ema(macd_values, self.macd_signal)
        
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }
    
    def _calculate_ema(self, prices: List[float], period: int) -> float:
        """Calculate Exponential Moving Average"""
        if len(prices) < period:
            return prices[-1] if prices else 0
        
        multiplier = 2 / (period + 1)
        ema = prices[0]
        
        for price in prices[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return ema
    
    def generate_signal(self, symbol: str, platform: str) -> Optional[TradingSignal]:
        """Generate trading signal based on technical analysis"""
        if len(self.price_history[symbol]) < 50:
            return None
        
        current_price = self.price_history[symbol][-1]['price']
        rsi = self.calculate_rsi(symbol)
        macd_data = self.calculate_macd(symbol)
        
        # Signal generation logic
        signal_type = SignalType.HOLD
        strength = SignalStrength.WEAK
        confidence = 0.5
        
        # RSI-based signals
        if rsi < 30:
            signal_type = SignalType.BUY
            strength = SignalStrength.STRONG
            confidence = 0.8
        elif rsi > 70:
            signal_type = SignalType.SELL
            strength = SignalStrength.STRONG
            confidence = 0.8
        elif 30 <= rsi <= 40:
            signal_type = SignalType.BUY
            strength = SignalStrength.MODERATE
            confidence = 0.6
        elif 60 <= rsi <= 70:
            signal_type = SignalType.SELL
            strength = SignalStrength.MODERATE
            confidence = 0.6
        
        # MACD confirmation
        if macd_data['macd'] > macd_data['signal'] and signal_type == SignalType.BUY:
            confidence = min(confidence + 0.1, 1.0)
            if strength == SignalStrength.MODERATE:
                strength = SignalStrength.STRONG
        elif macd_data['macd'] < macd_data['signal'] and signal_type == SignalType.SELL:
            confidence = min(confidence + 0.1, 1.0)
            if strength == SignalStrength.MODERATE:
                strength = SignalStrength.STRONG
        
        # Volume confirmation
        recent_volume = [data['volume'] for data in list(self.volume_history[symbol])[-10:]]
        if recent_volume:
            avg_volume = sum(recent_volume) / len(recent_volume)
            current_volume = self.volume_history[symbol][-1]['volume']
            if current_volume > avg_volume * 1.5:
                confidence = min(confidence + 0.1, 1.0)
        
        if signal_type == SignalType.HOLD:
            return None
        
        # Create signal
        signal_id = f"{symbol}_{int(time.time())}_{platform}"
        expiry_time = datetime.now() + timedelta(minutes=30)  # 30-minute expiry
        
        return TradingSignal(
            id=signal_id,
            symbol=symbol,
            signal_type=signal_type,
            strength=strength,
            timeframe=TimeFrame.M5,
            price=current_price,
            timestamp=datetime.now(),
            expiry_time=expiry_time,
            confidence=confidence,
            platform=platform,
            metadata={
                'rsi': rsi,
                'macd': macd_data,
                'volume_ratio': current_volume / avg_volume if recent_volume else 1.0
            }
        )

class SignalBolt:
    """Main Signal Bolt class for real-time signal tracking"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.analyzer = SignalAnalyzer()
        self.signals = []
        self.subscribers = []
        self.running = False
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Platform configurations
        self.platforms = {
            'iq_options': {
                'name': 'IQ Options',
                'websocket_url': 'wss://api.iqoption.com/ws/',
                'api_url': 'https://api.iqoption.com/api/',
                'enabled': True
            },
            'demo': {
                'name': 'Demo Platform',
                'websocket_url': None,
                'api_url': None,
                'enabled': True
            }
        }
        
        # Signal filters
        self.filters = SignalFilter()
        
        # Statistics
        self.stats = {
            'signals_generated': 0,
            'signals_expired': 0,
            'active_signals': 0,
            'uptime_start': datetime.now()
        }
    
    def add_subscriber(self, callback: Callable[[TradingSignal], None]):
        """Add a signal subscriber"""
        self.subscribers.append(callback)
        logger.info(f"Added signal subscriber. Total subscribers: {len(self.subscribers)}")
    
    def remove_subscriber(self, callback: Callable[[TradingSignal], None]):
        """Remove a signal subscriber"""
        if callback in self.subscribers:
            self.subscribers.remove(callback)
            logger.info(f"Removed signal subscriber. Total subscribers: {len(self.subscribers)}")
    
    def _notify_subscribers(self, signal: TradingSignal):
        """Notify all subscribers of a new signal"""
        for callback in self.subscribers:
            try:
                callback(signal)
            except Exception as e:
                logger.error(f"Error notifying subscriber: {e}")
    
    def _cleanup_expired_signals(self):
        """Remove expired signals"""
        now = datetime.now()
        expired_count = 0
        
        self.signals = [signal for signal in self.signals if signal.expiry_time > now]
        expired_count = len(self.signals) - len([s for s in self.signals if s.expiry_time > now])
        
        if expired_count > 0:
            self.stats['signals_expired'] += expired_count
            logger.info(f"Cleaned up {expired_count} expired signals")
    
    def _apply_filters(self, signal: TradingSignal) -> bool:
        """Apply filters to determine if signal should be processed"""
        if signal.confidence < self.filters.min_confidence:
            return False
        
        if signal.strength.value < self.filters.min_strength:
            return False
        
        if self.filters.platforms and signal.platform not in self.filters.platforms:
            return False
        
        if self.filters.symbols and signal.symbol not in self.filters.symbols:
            return False
        
        if self.filters.signal_types and signal.signal_type not in self.filters.signal_types:
            return False
        
        # Check age
        age_minutes = (datetime.now() - signal.timestamp).total_seconds() / 60
        if age_minutes > self.filters.max_age_minutes:
            return False
        
        return True
    
    def add_signal(self, signal: TradingSignal):
        """Add a new signal to the system"""
        if not self._apply_filters(signal):
            logger.debug(f"Signal filtered out: {signal.id}")
            return
        
        self.signals.append(signal)
        self.stats['signals_generated'] += 1
        self.stats['active_signals'] = len([s for s in self.signals if s.expiry_time > datetime.now()])
        
        logger.info(f"New signal added: {signal.symbol} {signal.signal_type.value} "
                   f"(confidence: {signal.confidence:.2f}, strength: {signal.strength.name})")
        
        self._notify_subscribers(signal)
    
    def get_active_signals(self, symbol: str = None, platform: str = None) -> List[TradingSignal]:
        """Get active (non-expired) signals"""
        now = datetime.now()
        active_signals = [s for s in self.signals if s.expiry_time > now]
        
        if symbol:
            active_signals = [s for s in active_signals if s.symbol == symbol]
        
        if platform:
            active_signals = [s for s in active_signals if s.platform == platform]
        
        return active_signals
    
    def get_signal_history(self, hours: int = 24) -> List[TradingSignal]:
        """Get signal history for the last N hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [s for s in self.signals if s.timestamp > cutoff_time]
    
    def update_filters(self, filters: SignalFilter):
        """Update signal filters"""
        self.filters = filters
        logger.info("Signal filters updated")
    
    async def _simulate_market_data(self, symbol: str, platform: str):
        """Simulate market data for demo purposes"""
        import random
        
        base_price = 100.0
        price = base_price
        
        while self.running:
            # Simulate price movement
            change = random.uniform(-0.02, 0.02)  # ±2% change
            price *= (1 + change)
            
            volume = random.uniform(1000, 10000)
            timestamp = datetime.now()
            
            # Add data to analyzer
            self.analyzer.add_price_data(symbol, price, volume, timestamp)
            
            # Generate signal
            signal = self.analyzer.generate_signal(symbol, platform)
            if signal:
                self.add_signal(signal)
            
            await asyncio.sleep(5)  # Update every 5 seconds
    
    async def start(self):
        """Start the Signal Bolt"""
        self.running = True
        logger.info("Starting Signal Bolt...")
        
        # Start cleanup task
        cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        # Start market data simulation for demo
        demo_tasks = []
        for platform_name, platform_config in self.platforms.items():
            if platform_config['enabled']:
                if platform_name == 'demo':
                    # Simulate multiple symbols
                    symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD']
                    for symbol in symbols:
                        task = asyncio.create_task(
                            self._simulate_market_data(symbol, platform_name)
                        )
                        demo_tasks.append(task)
        
        try:
            await asyncio.gather(cleanup_task, *demo_tasks)
        except KeyboardInterrupt:
            logger.info("Shutting down Signal Bolt...")
        finally:
            self.running = False
            await self.stop()
    
    async def _cleanup_loop(self):
        """Periodic cleanup of expired signals"""
        while self.running:
            self._cleanup_expired_signals()
            await asyncio.sleep(60)  # Cleanup every minute
    
    async def stop(self):
        """Stop the Signal Bolt"""
        self.running = False
        self.executor.shutdown(wait=True)
        logger.info("Signal Bolt stopped")

# WebSocket server for real-time updates
class SignalWebSocketServer:
    """WebSocket server for real-time signal updates"""
    
    def __init__(self, signal_bolt: SignalBolt, host: str = "localhost", port: int = 8765):
        self.signal_bolt = signal_bolt
        self.host = host
        self.port = port
        self.clients = set()
    
    async def register_client(self, websocket, path):
        """Register a new WebSocket client"""
        self.clients.add(websocket)
        logger.info(f"New WebSocket client connected. Total clients: {len(self.clients)}")
        
        try:
            # Send current active signals
            active_signals = self.signal_bolt.get_active_signals()
            for signal in active_signals:
                await websocket.send(json.dumps(signal.to_dict()))
            
            # Keep connection alive
            await websocket.wait_closed()
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.clients.remove(websocket)
            logger.info(f"WebSocket client disconnected. Total clients: {len(self.clients)}")
    
    async def broadcast_signal(self, signal: TradingSignal):
        """Broadcast signal to all connected clients"""
        if not self.clients:
            return
        
        message = json.dumps(signal.to_dict())
        disconnected = set()
        
        for client in self.clients:
            try:
                await client.send(message)
            except websockets.exceptions.ConnectionClosed:
                disconnected.add(client)
        
        # Remove disconnected clients
        self.clients -= disconnected
    
    async def start_server(self):
        """Start the WebSocket server"""
        logger.info(f"Starting WebSocket server on {self.host}:{self.port}")
        
        # Add signal subscriber
        self.signal_bolt.add_subscriber(self.broadcast_signal)
        
        server = await websockets.serve(
            self.register_client,
            self.host,
            self.port
        )
        
        return server

# Example usage and testing
async def main():
    """Main function to run the Signal Bolt"""
    # Create signal bolt
    signal_bolt = SignalBolt()
    
    # Add a simple subscriber for logging
    def log_signal(signal: TradingSignal):
        logger.info(f"Signal received: {signal.symbol} {signal.signal_type.value} "
                   f"at {signal.price} (confidence: {signal.confidence:.2f})")
    
    signal_bolt.add_subscriber(log_signal)
    
    # Start WebSocket server
    ws_server = SignalWebSocketServer(signal_bolt)
    server = await ws_server.start_server()
    
    # Start signal bolt in background
    signal_task = asyncio.create_task(signal_bolt.start())
    
    try:
        # Keep running
        await asyncio.gather(signal_task, server.wait_closed())
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        await signal_bolt.stop()
        server.close()
        await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())