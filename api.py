"""
FastAPI REST API for Signal Bolt
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncio
import json
from datetime import datetime, timedelta
import logging

from signal_bolt import SignalBolt, TradingSignal, SignalType, SignalStrength, TimeFrame, SignalFilter
from config import Config

# Configure logging
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Signal Bolt API",
    description="Real-time trading signal tracking API for options trading platforms",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global signal bolt instance
signal_bolt: Optional[SignalBolt] = None

# Pydantic models for API
class SignalResponse(BaseModel):
    id: str
    symbol: str
    signal_type: str
    strength: int
    timeframe: str
    price: float
    timestamp: str
    expiry_time: str
    confidence: float
    platform: str
    metadata: Optional[Dict[str, Any]] = None

class SignalFilterRequest(BaseModel):
    min_confidence: Optional[float] = None
    min_strength: Optional[int] = None
    max_age_minutes: Optional[int] = None
    platforms: Optional[List[str]] = None
    symbols: Optional[List[str]] = None
    signal_types: Optional[List[str]] = None

class StatsResponse(BaseModel):
    signals_generated: int
    signals_expired: int
    active_signals: int
    uptime_hours: float
    subscribers_count: int

class WebSocketManager:
    """Manages WebSocket connections"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_signal(self, signal: TradingSignal):
        """Send signal to all connected WebSocket clients"""
        if not self.active_connections:
            return
        
        signal_data = signal.to_dict()
        message = json.dumps(signal_data)
        
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                disconnected.append(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection)

# WebSocket manager instance
websocket_manager = WebSocketManager()

def get_signal_bolt() -> SignalBolt:
    """Dependency to get signal bolt instance"""
    if signal_bolt is None:
        raise HTTPException(status_code=503, detail="Signal Bolt not initialized")
    return signal_bolt

@app.on_event("startup")
async def startup_event():
    """Initialize Signal Bolt on startup"""
    global signal_bolt
    signal_bolt = SignalBolt(Config.__dict__)
    
    # Add WebSocket manager as subscriber
    signal_bolt.add_subscriber(websocket_manager.send_signal)
    
    # Start signal bolt in background
    asyncio.create_task(signal_bolt.start())
    
    logger.info("Signal Bolt API started")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global signal_bolt
    if signal_bolt:
        await signal_bolt.stop()
    logger.info("Signal Bolt API stopped")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Signal Bolt API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "signals": "/signals",
            "active_signals": "/signals/active",
            "history": "/signals/history",
            "stats": "/stats",
            "websocket": "/ws",
            "filters": "/filters"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "signal_bolt_running": signal_bolt is not None and signal_bolt.running
    }

@app.get("/signals/active", response_model=List[SignalResponse])
async def get_active_signals(
    symbol: Optional[str] = None,
    platform: Optional[str] = None,
    signal_bolt: SignalBolt = Depends(get_signal_bolt)
):
    """Get active (non-expired) signals"""
    try:
        signals = signal_bolt.get_active_signals(symbol=symbol, platform=platform)
        return [SignalResponse(**signal.to_dict()) for signal in signals]
    except Exception as e:
        logger.error(f"Error getting active signals: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/signals/history", response_model=List[SignalResponse])
async def get_signal_history(
    hours: int = 24,
    symbol: Optional[str] = None,
    platform: Optional[str] = None,
    signal_bolt: SignalBolt = Depends(get_signal_bolt)
):
    """Get signal history for the last N hours"""
    try:
        signals = signal_bolt.get_signal_history(hours=hours)
        
        # Apply filters
        if symbol:
            signals = [s for s in signals if s.symbol == symbol]
        if platform:
            signals = [s for s in signals if s.platform == platform]
        
        return [SignalResponse(**signal.to_dict()) for signal in signals]
    except Exception as e:
        logger.error(f"Error getting signal history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/signals/{signal_id}", response_model=SignalResponse)
async def get_signal(
    signal_id: str,
    signal_bolt: SignalBolt = Depends(get_signal_bolt)
):
    """Get a specific signal by ID"""
    try:
        # Search in active signals first
        active_signals = signal_bolt.get_active_signals()
        signal = next((s for s in active_signals if s.id == signal_id), None)
        
        if not signal:
            # Search in history
            history_signals = signal_bolt.get_signal_history(hours=24)
            signal = next((s for s in history_signals if s.id == signal_id), None)
        
        if not signal:
            raise HTTPException(status_code=404, detail="Signal not found")
        
        return SignalResponse(**signal.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting signal {signal_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats", response_model=StatsResponse)
async def get_stats(signal_bolt: SignalBolt = Depends(get_signal_bolt)):
    """Get system statistics"""
    try:
        uptime = datetime.now() - signal_bolt.stats['uptime_start']
        uptime_hours = uptime.total_seconds() / 3600
        
        return StatsResponse(
            signals_generated=signal_bolt.stats['signals_generated'],
            signals_expired=signal_bolt.stats['signals_expired'],
            active_signals=signal_bolt.stats['active_signals'],
            uptime_hours=uptime_hours,
            subscribers_count=len(signal_bolt.subscribers)
        )
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/platforms")
async def get_platforms():
    """Get available trading platforms"""
    return {
        "platforms": Config.PLATFORMS,
        "enabled_platforms": [
            name for name, config in Config.PLATFORMS.items() 
            if config.get('enabled', False)
        ]
    }

@app.get("/symbols")
async def get_symbols():
    """Get available trading symbols"""
    return {
        "symbols": Config.SYMBOLS,
        "all_symbols": Config.get_all_symbols()
    }

@app.post("/filters")
async def update_filters(
    filters: SignalFilterRequest,
    signal_bolt: SignalBolt = Depends(get_signal_bolt)
):
    """Update signal filters"""
    try:
        # Convert string signal types to enum
        signal_types = None
        if filters.signal_types:
            signal_types = [SignalType(st) for st in filters.signal_types]
        
        # Create new filter
        new_filter = SignalFilter(
            min_confidence=filters.min_confidence or signal_bolt.filters.min_confidence,
            min_strength=filters.min_strength or signal_bolt.filters.min_strength,
            max_age_minutes=filters.max_age_minutes or signal_bolt.filters.max_age_minutes,
            platforms=filters.platforms or signal_bolt.filters.platforms,
            symbols=filters.symbols or signal_bolt.filters.symbols,
            signal_types=signal_types or signal_bolt.filters.signal_types
        )
        
        signal_bolt.update_filters(new_filter)
        
        return {"message": "Filters updated successfully", "filters": filters.dict()}
    except Exception as e:
        logger.error(f"Error updating filters: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/filters")
async def get_filters(signal_bolt: SignalBolt = Depends(get_signal_bolt)):
    """Get current signal filters"""
    try:
        return {
            "min_confidence": signal_bolt.filters.min_confidence,
            "min_strength": signal_bolt.filters.min_strength,
            "max_age_minutes": signal_bolt.filters.max_age_minutes,
            "platforms": signal_bolt.filters.platforms,
            "symbols": signal_bolt.filters.symbols,
            "signal_types": [st.value for st in signal_bolt.filters.signal_types] if signal_bolt.filters.signal_types else None
        }
    except Exception as e:
        logger.error(f"Error getting filters: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time signal updates"""
    await websocket_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            # Echo back for ping/pong
            await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)

@app.post("/signals/simulate")
async def simulate_signal(
    symbol: str,
    signal_type: str,
    confidence: float = 0.8,
    strength: int = 3,
    platform: str = "demo",
    signal_bolt: SignalBolt = Depends(get_signal_bolt)
):
    """Simulate a trading signal for testing purposes"""
    try:
        # Create a simulated signal
        signal = TradingSignal(
            id=f"sim_{int(datetime.now().timestamp())}",
            symbol=symbol,
            signal_type=SignalType(signal_type),
            strength=SignalStrength(strength),
            timeframe=TimeFrame.M5,
            price=100.0,  # Simulated price
            timestamp=datetime.now(),
            expiry_time=datetime.now() + timedelta(minutes=30),
            confidence=confidence,
            platform=platform,
            metadata={"simulated": True}
        )
        
        signal_bolt.add_signal(signal)
        
        return {
            "message": "Signal simulated successfully",
            "signal": SignalResponse(**signal.to_dict())
        }
    except Exception as e:
        logger.error(f"Error simulating signal: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api:app",
        host=Config.API_HOST,
        port=Config.API_PORT,
        reload=Config.DEBUG,
        log_level=Config.LOG_LEVEL.lower()
    )