#!/usr/bin/env python3
"""
Signal Bolt Demo Script
Demonstrates the key features of Signal Bolt
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import List

from signal_bolt import SignalBolt, TradingSignal, SignalType, SignalStrength, TimeFrame
from client import SignalBoltClient, SignalBoltConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SignalBoltDemo:
    """Demo class for Signal Bolt features"""
    
    def __init__(self):
        self.signal_bolt = SignalBolt()
        self.received_signals = []
        self.setup_demo()
    
    def setup_demo(self):
        """Set up demo environment"""
        logger.info("Setting up Signal Bolt Demo...")
        
        # Add signal subscriber
        self.signal_bolt.add_subscriber(self.on_signal)
        
        # Configure demo filters
        from signal_bolt import SignalFilter
        filters = SignalFilter(
            min_confidence=0.6,
            min_strength=2,
            max_age_minutes=60,
            platforms=['demo'],
            symbols=['EURUSD', 'GBPUSD', 'USDJPY']
        )
        self.signal_bolt.update_filters(filters)
        
        logger.info("Demo setup complete!")
    
    def on_signal(self, signal: TradingSignal):
        """Handle incoming signals"""
        self.received_signals.append(signal)
        logger.info(f"📊 NEW SIGNAL: {signal.symbol} {signal.signal_type.value} "
                   f"at {signal.price:.4f} (confidence: {signal.confidence:.2f}, "
                   f"strength: {signal.strength.name})")
    
    async def simulate_market_data(self, symbol: str, duration: int = 60):
        """Simulate market data for a symbol"""
        logger.info(f"Simulating market data for {symbol}...")
        
        base_price = 1.1000 if 'USD' in symbol else 100.0
        price = base_price
        
        for i in range(duration):
            # Simulate price movement
            import random
            change = random.uniform(-0.01, 0.01)  # ±1% change
            price *= (1 + change)
            
            volume = random.uniform(1000, 5000)
            timestamp = datetime.now()
            
            # Add data to analyzer
            self.signal_bolt.analyzer.add_price_data(symbol, price, volume, timestamp)
            
            # Generate signal
            signal = self.signal_bolt.analyzer.generate_signal(symbol, 'demo')
            if signal:
                self.signal_bolt.add_signal(signal)
            
            await asyncio.sleep(1)  # Update every second
    
    async def run_demo(self):
        """Run the complete demo"""
        logger.info("🚀 Starting Signal Bolt Demo...")
        
        # Start market data simulation for multiple symbols
        symbols = ['EURUSD', 'GBPUSD', 'USDJPY']
        tasks = []
        
        for symbol in symbols:
            task = asyncio.create_task(self.simulate_market_data(symbol, 30))
            tasks.append(task)
        
        # Start demo tasks
        demo_task = asyncio.create_task(self.demo_features())
        
        try:
            # Run for 30 seconds
            await asyncio.gather(*tasks, demo_task)
        except KeyboardInterrupt:
            logger.info("Demo interrupted by user")
        finally:
            await self.show_results()
    
    async def demo_features(self):
        """Demonstrate various features"""
        await asyncio.sleep(5)  # Wait for some signals to be generated
        
        # Demo 1: Show active signals
        logger.info("\n" + "="*50)
        logger.info("DEMO 1: Active Signals")
        logger.info("="*50)
        active_signals = self.signal_bolt.get_active_signals()
        logger.info(f"Active signals: {len(active_signals)}")
        for signal in active_signals[:5]:  # Show first 5
            logger.info(f"  - {signal.symbol} {signal.signal_type.value} "
                       f"(confidence: {signal.confidence:.2f})")
        
        await asyncio.sleep(5)
        
        # Demo 2: Show signal history
        logger.info("\n" + "="*50)
        logger.info("DEMO 2: Signal History")
        logger.info("="*50)
        history = self.signal_bolt.get_signal_history(hours=1)
        logger.info(f"Signals in last hour: {len(history)}")
        
        # Group by symbol
        by_symbol = {}
        for signal in history:
            if signal.symbol not in by_symbol:
                by_symbol[signal.symbol] = []
            by_symbol[signal.symbol].append(signal)
        
        for symbol, signals in by_symbol.items():
            logger.info(f"  {symbol}: {len(signals)} signals")
        
        await asyncio.sleep(5)
        
        # Demo 3: Show statistics
        logger.info("\n" + "="*50)
        logger.info("DEMO 3: System Statistics")
        logger.info("="*50)
        stats = self.signal_bolt.stats
        logger.info(f"Signals generated: {stats['signals_generated']}")
        logger.info(f"Signals expired: {stats['expired_signals']}")
        logger.info(f"Active signals: {stats['active_signals']}")
        logger.info(f"Subscribers: {len(self.signal_bolt.subscribers)}")
        
        await asyncio.sleep(5)
        
        # Demo 4: Show signal filtering
        logger.info("\n" + "="*50)
        logger.info("DEMO 4: Signal Filtering")
        logger.info("="*50)
        filters = self.signal_bolt.filters
        logger.info(f"Min confidence: {filters.min_confidence}")
        logger.info(f"Min strength: {filters.min_strength}")
        logger.info(f"Max age: {filters.max_age_minutes} minutes")
        logger.info(f"Platforms: {filters.platforms}")
        logger.info(f"Symbols: {filters.symbols}")
        
        await asyncio.sleep(5)
        
        # Demo 5: Show signal analysis
        logger.info("\n" + "="*50)
        logger.info("DEMO 5: Technical Analysis")
        logger.info("="*50)
        
        for symbol in ['EURUSD', 'GBPUSD', 'USDJPY']:
            if len(self.signal_bolt.analyzer.price_history[symbol]) > 20:
                rsi = self.signal_bolt.analyzer.calculate_rsi(symbol)
                macd = self.signal_bolt.analyzer.calculate_macd(symbol)
                
                logger.info(f"{symbol}:")
                logger.info(f"  RSI: {rsi:.2f}")
                logger.info(f"  MACD: {macd['macd']:.4f}")
                logger.info(f"  Signal: {macd['signal']:.4f}")
                logger.info(f"  Histogram: {macd['histogram']:.4f}")
    
    async def show_results(self):
        """Show final demo results"""
        logger.info("\n" + "="*60)
        logger.info("DEMO RESULTS")
        logger.info("="*60)
        
        # Total signals received
        logger.info(f"Total signals received: {len(self.received_signals)}")
        
        # Signals by type
        by_type = {}
        for signal in self.received_signals:
            signal_type = signal.signal_type.value
            if signal_type not in by_type:
                by_type[signal_type] = 0
            by_type[signal_type] += 1
        
        logger.info("Signals by type:")
        for signal_type, count in by_type.items():
            logger.info(f"  {signal_type}: {count}")
        
        # Signals by symbol
        by_symbol = {}
        for signal in self.received_signals:
            if signal.symbol not in by_symbol:
                by_symbol[signal.symbol] = 0
            by_symbol[signal.symbol] += 1
        
        logger.info("Signals by symbol:")
        for symbol, count in by_symbol.items():
            logger.info(f"  {symbol}: {count}")
        
        # Average confidence
        if self.received_signals:
            avg_confidence = sum(s.confidence for s in self.received_signals) / len(self.received_signals)
            logger.info(f"Average confidence: {avg_confidence:.2f}")
        
        # Signal strength distribution
        by_strength = {}
        for signal in self.received_signals:
            strength = signal.strength.name
            if strength not in by_strength:
                by_strength[strength] = 0
            by_strength[strength] += 1
        
        logger.info("Signals by strength:")
        for strength, count in by_strength.items():
            logger.info(f"  {strength}: {count}")
        
        logger.info("\n🎉 Demo completed successfully!")
        logger.info("Signal Bolt is ready for production use!")

async def demo_client_usage():
    """Demo client library usage"""
    logger.info("\n" + "="*60)
    logger.info("CLIENT LIBRARY DEMO")
    logger.info("="*60)
    
    config = SignalBoltConfig(
        api_url="http://localhost:8000",
        ws_url="ws://localhost:8765"
    )
    
    try:
        async with SignalBoltClient(config) as client:
            logger.info("Connected to Signal Bolt API")
            
            # Add signal callback
            def on_signal(signal):
                logger.info(f"Client received: {signal.symbol} {signal.signal_type.value}")
            
            client.add_signal_callback(on_signal)
            
            # Get active signals
            try:
                active_signals = await client.get_active_signals()
                logger.info(f"Active signals via client: {len(active_signals)}")
            except Exception as e:
                logger.warning(f"Could not get active signals: {e}")
            
            # Get stats
            try:
                stats = await client.get_stats()
                logger.info(f"System stats: {stats}")
            except Exception as e:
                logger.warning(f"Could not get stats: {e}")
            
            # Simulate a signal
            try:
                simulated_signal = await client.simulate_signal(
                    symbol="DEMO",
                    signal_type="BUY",
                    confidence=0.9,
                    strength=4
                )
                logger.info(f"Simulated signal: {simulated_signal.id}")
            except Exception as e:
                logger.warning(f"Could not simulate signal: {e}")
            
            logger.info("Client demo completed")
    
    except Exception as e:
        logger.warning(f"Client demo failed (API server not running): {e}")

async def main():
    """Main demo function"""
    print("🎯 Signal Bolt Demo")
    print("==================")
    print("This demo showcases the key features of Signal Bolt:")
    print("- Real-time signal generation")
    print("- Technical analysis (RSI, MACD)")
    print("- Signal filtering and management")
    print("- WebSocket and REST API")
    print("- Client library integration")
    print()
    
    # Run core demo
    demo = SignalBoltDemo()
    await demo.run_demo()
    
    # Run client demo
    await demo_client_usage()
    
    print("\n📚 Next Steps:")
    print("1. Start the API server: python api.py")
    print("2. Run the trading bot: python example_trading_bot.py")
    print("3. Check the API documentation: http://localhost:8000/docs")
    print("4. Connect via WebSocket: ws://localhost:8765/ws")

if __name__ == "__main__":
    asyncio.run(main())