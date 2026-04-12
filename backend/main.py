from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from app.api import routes
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Global orchestrator and executor instances
orchestrator = None
executor = None

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered autonomous trading platform with local Claude AI, real-time analysis, and automated reporting",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(routes.router)

@app.on_event("startup")
async def startup_event():
    """Initialize all services on app startup"""
    global orchestrator, executor
    
    try:
        logger.info("=" * 60)
        logger.info("AI TRADING PLATFORM - STARTUP SEQUENCE")
        logger.info("=" * 60)
        
        # Import services
        from app.services.orchestrator import get_orchestrator, get_executor
        from app.services.paper_trading_advanced import paper_trader
        from app.services.groww_api_enhanced import groww_client
        from app.services.ai_analysis_advanced import ai_engine
        from app.services.explainable_ai import explainable_logger
        from app.models.database import Base
        from app.core.database import engine
        
        # Initialize database
        logger.info("Initializing database...")
        Base.metadata.create_all(bind=engine)
        logger.info("✓ Database initialized")
        
        # Initialize orchestrator
        logger.info("Starting Trade Execution Orchestrator...")
        orchestrator = await get_orchestrator()
        
        # Initialize executor
        logger.info("Initializing Trade Executor...")
        executor = await get_executor(
            paper_trader,
            groww_client,
            ai_engine,
            explainable_logger
        )
        
        # Start scheduler
        logger.info("Starting Scheduler (EOD reports @ 3:30 PM IST)...")
        orchestrator.start()
        logger.info("✓ Scheduler started")
        
        # Register callbacks
        from app.services.report_generator import report_generator
        
        async def generate_eod_report():
            """EOD report callback"""
            try:
                logger.info("GENERATING END-OF-DAY REPORT (3:30 PM IST)")
                report = await report_generator.generate_daily_report()
                html = await report_generator.export_report_as_html(report)
                logger.info(f"✓ EOD Report generated successfully")
                return report
            except Exception as e:
                logger.error(f"Error generating EOD report: {e}")
        
        orchestrator.register_eod_callback(generate_eod_report)
        logger.info("✓ EOD Report callback registered")
        
        logger.info("=" * 60)
        logger.info("✓ AI TRADING PLATFORM READY")
        logger.info("=" * 60)
        logger.info(f"Paper Trading Capital: ₹{settings.PAPER_TRADING_INITIAL_CAPITAL:,.2f}")
        logger.info(f"Live Trading Enabled: {settings.LIVE_TRADING_ENABLED}")
        logger.info(f"Claude Model: {settings.CLAUDE_MODEL}")
        logger.info(f"Market Timezone: Asia/Kolkata (IST)")
        logger.info(f"API Documentation: http://localhost:8000/docs")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up services on app shutdown"""
    global orchestrator
    
    try:
        logger.info("=" * 60)
        logger.info("SHUTDOWN SEQUENCE - AI TRADING PLATFORM")
        logger.info("=" * 60)
        
        if orchestrator:
            logger.info("Stopping Scheduler...")
            orchestrator.stop()
            logger.info("✓ Scheduler stopped")
        
        logger.info("✓ All services stopped cleanly")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

@app.get("/")
async def root():
    """Root endpoint with platform status"""
    try:
        from app.services.paper_trading_advanced import paper_trader
        
        portfolio = paper_trader.get_portfolio_value()
        
        return {
            "message": f"Welcome to {settings.APP_NAME}",
            "version": settings.APP_VERSION,
            "status": "operational",
            "docs": "/docs",
            "api": {
                "v1": "/api/v1",
                "v2": "/api/advanced"
            },
            "portfolio": {
                "total_value": portfolio.get("total"),
                "stock_value": portfolio.get("stock_value"),
                "cash": portfolio.get("cash")
            },
            "features": [
                "Local Claude AI Analysis",
                "Real-time Groww API Integration",
                "Automated Trade Execution",
                "Options Strategy Selection",
                "Mutual Fund Recommendations",
                "Paper Trading Simulator",
                "Explainable AI Logging",
                "End-of-Day Reports (3:30 PM IST)"
            ]
        }
    except Exception as e:
        logger.error(f"Error in root endpoint: {e}")
        return {
            "message": settings.APP_NAME,
            "status": "initializing",
            "docs": "/docs"
        }

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)}
    )

if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting {settings.APP_NAME} on http://0.0.0.0:8000")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False
    )
