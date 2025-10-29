import sys

sys.path.append(r"C:\FILES\Code\shamebot")

from sqlmodel import SQLModel, create_engine
import database

from keys import db_key

engine = create_engine(db_key)

SQLModel.metadata.drop_all(engine)
SQLModel.metadata.create_all(engine)
