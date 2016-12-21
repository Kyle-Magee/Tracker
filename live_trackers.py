from steamtracker import run
from app import SteamTrackers, Users
import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import time
import os



BASE_DIR = os.path.abspath(os.path.dirname(__file__))
engine = sqlalchemy.create_engine('sqlite:///' + os.path.join(BASE_DIR, 'tracker.db'))
Base = declarative_base()
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


while True:
    for user in session.query(SteamTrackers).all():
        usermeta = session.query(Users).filter_by(db_id=user.user_id)
        run(user, usermeta)
        session.commit()

    time.sleep(3600)