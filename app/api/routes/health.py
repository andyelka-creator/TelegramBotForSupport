from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import engine

router = APIRouter()


@router.get('/health')
async def health() -> dict:
    try:
        async with engine.connect() as conn:
            await conn.execute(text('SELECT 1'))
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail={'status': 'degraded', 'db': 'down'}) from exc

    return {'status': 'ok', 'db': 'up'}
