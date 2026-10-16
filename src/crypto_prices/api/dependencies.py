from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from crypto_prices.db.session import get_session
from crypto_prices.repositories.prices import PriceRepository
from crypto_prices.services.prices import PriceService

SessionDependency = Annotated[AsyncSession, Depends(get_session)]


def get_price_service(session: SessionDependency) -> PriceService:
    return PriceService(PriceRepository(session))
