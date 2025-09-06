#!/usr/bin/env python3
"""
Comprehensive test suite for Signal Bolt
"""

import asyncio
import json
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import unittest
from unittest.mock import Mock, patch

# Import Signal Bolt modules
from signal_bolt import (
    SignalBolt, TradingSignal, SignalType, SignalStrength, TimeFrame, 
    SignalFilter, SignalAnalyzer
)
from client import SignalBoltClient, SignalBoltConfig
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestTradingSignal(unittest.TestCase):
    """Test TradingSignal class"""
    
    def test_signal_creation(self):
        """Test signal creation"""
        signal = TradingSignal(
            id="test_123",
            symbol="EURUSD",
            signal_type=SignalType.BUY,
            strength=SignalStrength.STRONG,
            timeframe=TimeFrame.M5,
            price=1.1000,
            timestamp=datetime.now(),
            expiry_time=datetime.now() + timedelta(minutes=30),
            confidence=0.8,
            platform="demo"
        )
        
        self.assertEqual(signal.symbol, "EURUSD")
        self.assertEqual(signal.signal_type, SignalType.BUY)
        self.assertEqual(signal.strength, SignalStrength.STRONG)
        self.assertEqual(signal.confidence, 0.8)
    
    def test_signal_to_dict(self):
        """Test signal serialization"""
        signal = TradingSignal(
            id="test_123",
            symbol="EURUSD",
            signal_type=SignalType.BUY,
            strength=SignalStrength.STRONG,
            timeframe=TimeFrame.M5,
            price=1.1000,
            timestamp=datetime.now(),
            expiry_time=datetime.now() + timedelta(minutes=30),
            confidence=0.8,
            platform="demo"
        )
        
        signal_dict = signal.to_dict()
        
        self.assertIsInstance(signal_dict, dict)
        self.assertEqual(signal_dict['symbol'], "EURUSD")
        self.assertEqual(signal_dict['signal_type'], "BUY")
        self.assertEqual(signal_dict['strength'], 3)

class TestSignalAnalyzer(unittest.TestCase):
    """Test SignalAnalyzer class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.analyzer = SignalAnalyzer()
    
    def test_add_price_data(self):
        """Test adding price data"""
        symbol = "EURUSD"
        price = 1.1000
        volume = 1000
        timestamp = datetime.now()
        
        self.analyzer.add_price_data(symbol, price, volume, timestamp)
        
        self.assertEqual(len(self.analyzer.price_history[symbol]), 1)
        self.assertEqual(self.analyzer.price_history[symbol][0]['price'], price)
    
    def test_calculate_rsi(self):
        """Test RSI calculation"""
        symbol = "EURUSD"
        
        # Add price data for RSI calculation
        base_price = 100.0
        for i in range(20):
            price = base_price + (i * 0.1)  # Slight upward trend
            volume = 1000 + i
            timestamp = datetime.now() + timedelta(seconds=i)
            self.analyzer.add_price_data(symbol, price, volume, timestamp)
        
        rsi = self.analyzer.calculate_rsi(symbol)
        
        self.assertIsInstance(rsi, float)
        self.assertGreaterEqual(rsi, 0)
        self.assertLessEqual(rsi, 100)
    
    def test_calculate_macd(self):
        """Test MACD calculation"""
        symbol = "EURUSD"
        
        # Add price data for MACD calculation
        base_price = 100.0
        for i in range(30):
            price = base_price + (i * 0.1)  # Slight upward trend
            volume = 1000 + i
            timestamp = datetime.now() + timedelta(seconds=i)
            self.analyzer.add_price_data(symbol, price, volume, timestamp)
        
        macd_data = self.analyzer.calculate_macd(symbol)
        
        self.assertIsInstance(macd_data, dict)
        self.assertIn('macd', macd_data)
        self.assertIn('signal', macd_data)
        self.assertIn('histogram', macd_data)
    
    def test_generate_signal(self):
        """Test signal generation"""
        symbol = "EURUSD"
        platform = "demo"
        
        # Add enough price data for signal generation
        base_price = 100.0
        for i in range(60):
            # Create a pattern that should generate a signal
            if i < 30:
                price = base_price - (i * 0.5)  # Downward trend
            else:
                price = base_price - 15 + ((i - 30) * 0.3)  # Recovery
            
            volume = 1000 + i
            timestamp = datetime.now() + timedelta(seconds=i)
            self.analyzer.add_price_data(symbol, price, volume, timestamp)
        
        signal = self.analyzer.generate_signal(symbol, platform)
        
        if signal:  # Signal may or may not be generated depending on data
            self.assertIsInstance(signal, TradingSignal)
            self.assertEqual(signal.symbol, symbol)
            self.assertEqual(signal.platform, platform)

class TestSignalBolt(unittest.TestCase):
    """Test SignalBolt class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.signal_bolt = SignalBolt()
    
    def test_add_subscriber(self):
        """Test adding subscribers"""
        callback = Mock()
        
        self.signal_bolt.add_subscriber(callback)
        
        self.assertIn(callback, self.signal_bolt.subscribers)
    
    def test_remove_subscriber(self):
        """Test removing subscribers"""
        callback = Mock()
        
        self.signal_bolt.add_subscriber(callback)
        self.signal_bolt.remove_subscriber(callback)
        
        self.assertNotIn(callback, self.signal_bolt.subscribers)
    
    def test_add_signal(self):
        """Test adding signals"""
        signal = TradingSignal(
            id="test_123",
            symbol="EURUSD",
            signal_type=SignalType.BUY,
            strength=SignalStrength.STRONG,
            timeframe=TimeFrame.M5,
            price=1.1000,
            timestamp=datetime.now(),
            expiry_time=datetime.now() + timedelta(minutes=30),
            confidence=0.8,
            platform="demo"
        )
        
        initial_count = len(self.signal_bolt.signals)
        self.signal_bolt.add_signal(signal)
        
        self.assertEqual(len(self.signal_bolt.signals), initial_count + 1)
        self.assertEqual(self.signal_bolt.stats['signals_generated'], 1)
    
    def test_get_active_signals(self):
        """Test getting active signals"""
        # Add an active signal
        active_signal = TradingSignal(
            id="active_123",
            symbol="EURUSD",
            signal_type=SignalType.BUY,
            strength=SignalStrength.STRONG,
            timeframe=TimeFrame.M5,
            price=1.1000,
            timestamp=datetime.now(),
            expiry_time=datetime.now() + timedelta(minutes=30),
            confidence=0.8,
            platform="demo"
        )
        
        # Add an expired signal
        expired_signal = TradingSignal(
            id="expired_123",
            symbol="GBPUSD",
            signal_type=SignalType.SELL,
            strength=SignalStrength.MODERATE,
            timeframe=TimeFrame.M5,
            price=1.2500,
            timestamp=datetime.now() - timedelta(hours=1),
            expiry_time=datetime.now() - timedelta(minutes=30),
            confidence=0.7,
            platform="demo"
        )
        
        self.signal_bolt.add_signal(active_signal)
        self.signal_bolt.add_signal(expired_signal)
        
        active_signals = self.signal_bolt.get_active_signals()
        
        self.assertEqual(len(active_signals), 1)
        self.assertEqual(active_signals[0].id, "active_123")
    
    def test_signal_filtering(self):
        """Test signal filtering"""
        # Create a filter
        filter_config = SignalFilter(
            min_confidence=0.8,
            min_strength=3,
            platforms=['demo'],
            symbols=['EURUSD']
        )
        
        self.signal_bolt.update_filters(filter_config)
        
        # Test signal that should pass filter
        good_signal = TradingSignal(
            id="good_123",
            symbol="EURUSD",
            signal_type=SignalType.BUY,
            strength=SignalStrength.STRONG,
            timeframe=TimeFrame.M5,
            price=1.1000,
            timestamp=datetime.now(),
            expiry_time=datetime.now() + timedelta(minutes=30),
            confidence=0.9,
            platform="demo"
        )
        
        # Test signal that should be filtered out
        bad_signal = TradingSignal(
            id="bad_123",
            symbol="GBPUSD",  # Wrong symbol
            signal_type=SignalType.BUY,
            strength=SignalStrength.WEAK,  # Too weak
            timeframe=TimeFrame.M5,
            price=1.2500,
            timestamp=datetime.now(),
            expiry_time=datetime.now() + timedelta(minutes=30),
            confidence=0.5,  # Too low confidence
            platform="demo"
        )
        
        initial_count = len(self.signal_bolt.signals)
        
        self.signal_bolt.add_signal(good_signal)
        self.signal_bolt.add_signal(bad_signal)
        
        # Only the good signal should be added
        self.assertEqual(len(self.signal_bolt.signals), initial_count + 1)
        self.assertEqual(self.signal_bolt.signals[-1].id, "good_123")

class TestSignalBoltClient(unittest.TestCase):
    """Test SignalBoltClient class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = SignalBoltConfig(
            api_url="http://localhost:8000",
            ws_url="ws://localhost:8765"
        )
        self.client = SignalBoltClient(self.config)
    
    def test_config_creation(self):
        """Test client configuration"""
        self.assertEqual(self.client.config.api_url, "http://localhost:8000")
        self.assertEqual(self.client.config.ws_url, "ws://localhost:8765")
    
    def test_add_signal_callback(self):
        """Test adding signal callbacks"""
        callback = Mock()
        
        self.client.add_signal_callback(callback)
        
        self.assertIn(callback, self.client.signal_callbacks)
    
    def test_remove_signal_callback(self):
        """Test removing signal callbacks"""
        callback = Mock()
        
        self.client.add_signal_callback(callback)
        self.client.remove_signal_callback(callback)
        
        self.assertNotIn(callback, self.client.signal_callbacks)

class TestIntegration(unittest.TestCase):
    """Integration tests"""
    
    def test_signal_flow(self):
        """Test complete signal flow"""
        signal_bolt = SignalBolt()
        
        # Add a subscriber
        received_signals = []
        def signal_handler(signal):
            received_signals.append(signal)
        
        signal_bolt.add_subscriber(signal_handler)
        
        # Generate a signal
        signal = TradingSignal(
            id="integration_test",
            symbol="EURUSD",
            signal_type=SignalType.BUY,
            strength=SignalStrength.STRONG,
            timeframe=TimeFrame.M5,
            price=1.1000,
            timestamp=datetime.now(),
            expiry_time=datetime.now() + timedelta(minutes=30),
            confidence=0.8,
            platform="demo"
        )
        
        signal_bolt.add_signal(signal)
        
        # Check that signal was received
        self.assertEqual(len(received_signals), 1)
        self.assertEqual(received_signals[0].id, "integration_test")

async def test_async_functionality():
    """Test async functionality"""
    logger.info("Testing async functionality...")
    
    signal_bolt = SignalBolt()
    
    # Test signal generation with market data
    symbol = "EURUSD"
    platform = "demo"
    
    # Add market data
    base_price = 100.0
    for i in range(100):
        # Create a pattern that should generate signals
        if i < 50:
            price = base_price - (i * 0.2)  # Downward trend
        else:
            price = base_price - 10 + ((i - 50) * 0.1)  # Recovery
        
        volume = 1000 + i
        timestamp = datetime.now() + timedelta(seconds=i)
        signal_bolt.analyzer.add_price_data(symbol, price, volume, timestamp)
    
    # Generate signals
    signals_generated = 0
    for i in range(10):
        signal = signal_bolt.analyzer.generate_signal(symbol, platform)
        if signal:
            signal_bolt.add_signal(signal)
            signals_generated += 1
            logger.info(f"Generated signal: {signal.symbol} {signal.signal_type.value} "
                       f"(confidence: {signal.confidence:.2f})")
    
    logger.info(f"Generated {signals_generated} signals")
    
    # Test active signals
    active_signals = signal_bolt.get_active_signals()
    logger.info(f"Active signals: {len(active_signals)}")
    
    # Test signal history
    history = signal_bolt.get_signal_history(hours=1)
    logger.info(f"Signal history (1 hour): {len(history)}")
    
    return signals_generated > 0

def run_performance_test():
    """Run performance tests"""
    logger.info("Running performance tests...")
    
    signal_bolt = SignalBolt()
    
    # Test signal generation performance
    start_time = time.time()
    
    # Generate many signals
    for i in range(1000):
        signal = TradingSignal(
            id=f"perf_test_{i}",
            symbol="EURUSD",
            signal_type=SignalType.BUY,
            strength=SignalStrength.STRONG,
            timeframe=TimeFrame.M5,
            price=1.1000 + (i * 0.001),
            timestamp=datetime.now(),
            expiry_time=datetime.now() + timedelta(minutes=30),
            confidence=0.8,
            platform="demo"
        )
        signal_bolt.add_signal(signal)
    
    end_time = time.time()
    duration = end_time - start_time
    
    logger.info(f"Generated 1000 signals in {duration:.2f} seconds")
    logger.info(f"Rate: {1000/duration:.2f} signals/second")
    
    # Test filtering performance
    start_time = time.time()
    active_signals = signal_bolt.get_active_signals()
    end_time = time.time()
    
    logger.info(f"Filtered {len(active_signals)} active signals in {end_time - start_time:.4f} seconds")
    
    return duration < 1.0  # Should complete in less than 1 second

def main():
    """Run all tests"""
    logger.info("Starting Signal Bolt test suite...")
    
    # Run unit tests
    logger.info("Running unit tests...")
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    # Run async tests
    logger.info("Running async tests...")
    async_result = asyncio.run(test_async_functionality())
    logger.info(f"Async tests: {'PASSED' if async_result else 'FAILED'}")
    
    # Run performance tests
    logger.info("Running performance tests...")
    perf_result = run_performance_test()
    logger.info(f"Performance tests: {'PASSED' if perf_result else 'FAILED'}")
    
    logger.info("Test suite completed!")

if __name__ == "__main__":
    main()