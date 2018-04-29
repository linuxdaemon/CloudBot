from sqlalchemy.ext.declarative import declarative_base as _declarative_base
from sqlalchemy.orm import sessionmaker as _sessionmaker, scoped_session as _scoped_session

Base = _declarative_base()
Session = _scoped_session(_sessionmaker())

metadata = Base.metadata


class ContextSession:
    def __init__(self):
        self._session = Session()

    def __enter__(self):
        return self.session

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            try:
                self.session.commit()
            except Exception:
                self.session.rollback()
                self.session.commit()
                raise
        else:
            self.session.rollback()
            self.session.commit()

    @property
    def session(self):
        """
        :rtype: sqlalchemy.orm.Session
        """
        return self._session
