from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import time

from app.config import settings
from app.database import init_db, create_initial_data, SessionLocal
from app.routes import auth, tasks, users, skills, ai_recommendations

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerenciamento do ciclo de vida da aplicação"""
    logger.info("Iniciando IdeiaTech SmartLeader API...")
    logger.info(f"Versão: {settings.API_VERSION}")
    logger.info(f"Debug Mode: {settings.DEBUG}")
    
    try:
        init_db()
        db = SessionLocal()
        create_initial_data(db)
        db.close()
    except Exception as e:
        logger.error(f"Erro na inicialização: {str(e)}")
    
    yield
    logger.info("Encerrando IdeiaTech SmartLeader API...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="""
    ## IdeiaTech SmartLeader - Sistema de Gestão Inteligente de Trabalho Híbrido
    
    ### Funcionalidades
    
    - **IA Generativa**: Recomendações inteligentes de tarefas baseadas em IA
    - **Distribuição Automática**: Balanceamento de carga de trabalho
    - **Monitoramento de Bem-estar**: Análise de humor e energia
    - **Gestão de Skills**: Mapeamento automático de habilidades
    - **Dashboard Gerencial**: Métricas e insights em tempo real
    
    ### Autenticação
    
    Utilize o endpoint `/api/v1/auth/login` para obter um token JWT.
    """,
    version=settings.API_VERSION,
    lifespan=lifespan,
    docs_url=f"/api/{settings.API_VERSION}/docs",
    redoc_url=f"/api/{settings.API_VERSION}/redoc",
    openapi_url=f"/api/{settings.API_VERSION}/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware para logging de todas as requisições"""
    start_time = time.time()
    logger.info(f"Request: {request.method} {request.url.path}")
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"Response: {request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.3f}s")
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.get("/health", tags=["Health"])
async def health_check():
    """Endpoint de health check"""
    return {
        "status": "healthy",
        "service": "IdeiaTech SmartLeader API",
        "version": settings.API_VERSION
    }


@app.get("/", tags=["Root"])
async def root():
    """Endpoint raiz da API"""
    return {
        "message": "IdeiaTech SmartLeader API",
        "version": settings.API_VERSION,
        "docs": f"/api/{settings.API_VERSION}/docs",
        "health": "/health"
    }


app.include_router(auth.router, prefix=f"/api/{settings.API_VERSION}/auth", tags=["Autenticação"])
app.include_router(users.router, prefix=f"/api/{settings.API_VERSION}/users", tags=["Usuários"])
app.include_router(tasks.router, prefix=f"/api/{settings.API_VERSION}/tasks", tags=["Tarefas"])
app.include_router(skills.router, prefix=f"/api/{settings.API_VERSION}/skills", tags=["Habilidades"])
app.include_router(ai_recommendations.router, prefix=f"/api/{settings.API_VERSION}/ai", tags=["IA e Recomendações"])


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handler global para exceções não tratadas"""
    logger.error(f"Erro não tratado: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Erro interno do servidor",
            "message": str(exc) if settings.DEBUG else "Erro ao processar requisição"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.API_HOST, port=settings.API_PORT, reload=settings.DEBUG)
