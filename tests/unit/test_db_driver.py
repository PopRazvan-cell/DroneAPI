"""The async SQLAlchemy engine must use the MySQL driver."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import create_async_engine


def test_mysql_asyncmy_dialect() -> None:
    engine = create_async_engine("mysql+asyncmy://user:password@127.0.0.1:1/agridrone")

    assert engine.dialect.name == "mysql"
    assert engine.dialect.driver == "asyncmy"
