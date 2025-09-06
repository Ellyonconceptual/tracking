"""
Signal Bolt Client Library
Easy integration for trading applications
"""

import asyncio
import json
import logging
from typing import Callable, List, Optional, Dict, Any
from datetime import datetime, timedelta
import websockets
import aiohttp
from dataclasses import dataclass

from signal_bolt import TradingSignal, SignalType, SignalStrength, TimeFrame

logger = logging.getLogger(__name__)

@dataclass
class SignalBoltConfig:
    """Configuration for Signal Bolt client"""
    api_url: str = "http://localhost:8000"
    ws_url: str = "ws://localhost:8765"
    timeout: int = 30
    retry_attempts: int = 3
    retry_delay: float = 1.0

class SignalBoltClient:
    """Client for connecting to Signal Bolt API and WebSocket"""
    
    def __init__(self, config: SignalBoltConfig = None):
        self.config = config or SignalBoltConfig()
        self.session: Optional[aiohttp.ClientSession] = None
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.signal_callbacks: List[Callable[[TradingSignal], None]] = []
        self.running = False
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()
    
    async def connect(self):
        """Connect to Signal Bolt services"""
        try:
            # Create HTTP session
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            )
            
            # Test API connection
            async with self.session.get(f"{self.config.api_url}/health") as response:
                if response.status == 200:
                    logger.info("Connected to Signal Bolt API")
                else:
                    raise ConnectionError(f"API health check failed: {response.status}")
            
            # Connect to WebSocket
            await self._connect_websocket()
            
            self.running = True
            logger.info("Signal Bolt client connected successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect to Signal Bolt: {e}")
            await self.disconnect()
            raise
    
    async def disconnect(self):
        """Disconnect from Signal Bolt services"""
        self.running = False
        
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
        
        if self.session:
            await self.session.close()
            self.session = None
        
        logger.info("Signal Bolt client disconnected")
    
    async def _connect_websocket(self):
        """Connect to WebSocket for real-time signals"""
        try:
            self.websocket = await websockets.connect(
                self.config.ws_url,
                ping_interval=20,
                ping_timeout=10
            )
            
            # Start message handler
            asyncio.create_task(self._handle_websocket_messages())
            
            logger.info("Connected to Signal Bolt WebSocket")
            
        except Exception as e:
            logger.error(f"Failed to connect to WebSocket: {e}")
            raise
    
    async def _handle_websocket_messages(self):
        """Handle incoming WebSocket messages"""
        try:
            async for message in self.websocket:
                try:
                    signal_data = json.loads(message)
                    signal = self._parse_signal(signal_data)
                    
                    # Notify callbacks
                    for callback in self.signal_callbacks:
                        try:
                            await self._safe_callback(callback, signal)
                        except Exception as e:
                            logger.error(f"Error in signal callback: {e}")
                
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse WebSocket message: {e}")
                except Exception as e:
                    logger.error(f"Error handling WebSocket message: {e}")
        
        except websockets.exceptions.ConnectionClosed:
            logger.warning("WebSocket connection closed")
            if self.running:
                # Attempt to reconnect
                await asyncio.sleep(self.config.retry_delay)
                try:
                    await self._connect_websocket()
                except Exception as e:
                    logger.error(f"Failed to reconnect WebSocket: {e}")
    
    def _parse_signal(self, data: Dict[str, Any]) -> TradingSignal:
        """Parse signal data from API response"""
        return TradingSignal(
            id=data['id'],
            symbol=data['symbol'],
            signal_type=SignalType(data['signal_type']),
            strength=SignalStrength(data['strength']),
            timeframe=TimeFrame(data['timeframe']),
            price=data['price'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            expiry_time=datetime.fromisoformat(data['expiry_time']),
            confidence=data['confidence'],
            platform=data['platform'],
            metadata=data.get('metadata', {})
        )
    
    async def _safe_callback(self, callback: Callable, signal: TradingSignal):
        """Safely execute callback"""
        if asyncio.iscoroutinefunction(callback):
            await callback(signal)
        else:
            callback(signal)
    
    def add_signal_callback(self, callback: Callable[[TradingSignal], None]):
        """Add a callback for new signals"""
        self.signal_callbacks.append(callback)
        logger.info(f"Added signal callback. Total callbacks: {len(self.signal_callbacks)}")
    
    def remove_signal_callback(self, callback: Callable[[TradingSignal], None]):
        """Remove a signal callback"""
        if callback in self.signal_callbacks:
            self.signal_callbacks.remove(callback)
            logger.info(f"Removed signal callback. Total callbacks: {len(self.signal_callbacks)}")
    
    async def get_active_signals(
        self, 
        symbol: Optional[str] = None, 
        platform: Optional[str] = None
    ) -> List[TradingSignal]:
        """Get active signals from API"""
        if not self.session:
            raise ConnectionError("Not connected to API")
        
        params = {}
        if symbol:
            params['symbol'] = symbol
        if platform:
            params['platform'] = platform
        
        async with self.session.get(
            f"{self.config.api_url}/signals/active",
            params=params
        ) as response:
            if response.status == 200:
                data = await response.json()
                return [self._parse_signal(signal_data) for signal_data in data]
            else:
                raise Exception(f"API request failed: {response.status}")
    
    async def get_signal_history(
        self,
        hours: int = 24,
        symbol: Optional[str] = None,
        platform: Optional[str] = None
    ) -> List[TradingSignal]:
        """Get signal history from API"""
        if not self.session:
            raise ConnectionError("Not connected to API")
        
        params = {'hours': hours}
        if symbol:
            params['symbol'] = symbol
        if platform:
            params['platform'] = platform
        
        async with self.session.get(
            f"{self.config.api_url}/signals/history",
            params=params
        ) as response:
            if response.status == 200:
                data = await response.json()
                return [self._parse_signal(signal_data) for signal_data in data]
            else:
                raise Exception(f"API request failed: {response.status}")
    
    async def get_signal(self, signal_id: str) -> Optional[TradingSignal]:
        """Get a specific signal by ID"""
        if not self.session:
            raise ConnectionError("Not connected to API")
        
        async with self.session.get(f"{self.config.api_url}/signals/{signal_id}") as response:
            if response.status == 200:
                data = await response.json()
                return self._parse_signal(data)
            elif response.status == 404:
                return None
            else:
                raise Exception(f"API request failed: {response.status}")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        if not self.session:
            raise ConnectionError("Not connected to API")
        
        async with self.session.get(f"{self.config.api_url}/stats") as response:
            if response.status == 200:
                return await response.json()
            else:
                raise Exception(f"API request failed: {response.status}")
    
    async def get_platforms(self) -> Dict[str, Any]:
        """Get available trading platforms"""
        if not self.session:
            raise ConnectionError("Not connected to API")
        
        async with self.session.get(f"{self.config.api_url}/platforms") as response:
            if response.status == 200:
                return await response.json()
            else:
                raise Exception(f"API request failed: {response.status}")
    
    async def get_symbols(self) -> Dict[str, Any]:
        """Get available trading symbols"""
        if not self.session:
            raise ConnectionError("Not connected to API")
        
        async with self.session.get(f"{self.config.api_url}/symbols") as response:
            if response.status == 200:
                return await response.json()
            else:
                raise Exception(f"API request failed: {response.status}")
    
    async def simulate_signal(
        self,
        symbol: str,
        signal_type: str,
        confidence: float = 0.8,
        strength: int = 3,
        platform: str = "demo"
    ) -> TradingSignal:
        """Simulate a trading signal for testing"""
        if not self.session:
            raise ConnectionError("Not connected to API")
        
        data = {
            'symbol': symbol,
            'signal_type': signal_type,
            'confidence': confidence,
            'strength': strength,
            'platform': platform
        }
        
        async with self.session.post(
            f"{self.config.api_url}/signals/simulate",
            json=data
        ) as response:
            if response.status == 200:
                result = await response.json()
                return self._parse_signal(result['signal'])
            else:
                raise Exception(f"API request failed: {response.status}")

# Example usage and testing
async def example_usage():
    """Example of how to use the Signal Bolt client"""
    
    # Configure client
    config = SignalBoltConfig(
        api_url="http://localhost:8000",
        ws_url="ws://localhost:8765"
    )
    
    # Define signal handler
    async def on_signal(signal: TradingSignal):
        print(f"New signal: {signal.symbol} {signal.signal_type.value} "
              f"at {signal.price} (confidence: {signal.confidence:.2f})")
    
    # Use client
    async with SignalBoltClient(config) as client:
        # Add signal callback
        client.add_signal_callback(on_signal)
        
        # Get active signals
        active_signals = await client.get_active_signals()
        print(f"Active signals: {len(active_signals)}")
        
        # Get signal history
        history = await client.get_signal_history(hours=1)
        print(f"Signals in last hour: {len(history)}")
        
        # Get stats
        stats = await client.get_stats()
        print(f"System stats: {stats}")
        
        # Simulate a signal
        simulated_signal = await client.simulate_signal(
            symbol="EURUSD",
            signal_type="BUY",
            confidence=0.85,
            strength=4
        )
        print(f"Simulated signal: {simulated_signal.id}")
        
        # Keep running to receive real-time signals
        print("Listening for real-time signals... Press Ctrl+C to stop")
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("Stopping...")

if __name__ == "__main__":
    # Run example
    asyncio.run(example_usage())