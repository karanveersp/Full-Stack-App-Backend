from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# create engine
engine = create_engine('mysql://user:pass@localhost:3306/test')

Session = sessionmaker(bind=engine)

Base = declarative_base()

