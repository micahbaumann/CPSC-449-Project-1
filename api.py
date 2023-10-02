import sqlite3
import contextlib

from fastapi import FastAPI, Depends
from pydantic import BaseModel
from pydantic_settings import BaseSettings

class Settings(BaseSettings, env_file=".env", extra="ignore"):
    database: str
    logging_config: str

class Class(BaseModel):
    Department: str
    course_code: int
    section_number: int
    name: str
    Instructor: int
    Current_enrollment: int
    Maximum_enrollment: int

def get_db():
    with contextlib.closing(sqlite3.connect(settings.database)) as db:
        db.row_factory = sqlite3.Row
        yield db

settings = Settings()
app = FastAPI()

# This is an example endpoint. Change the "/" to the path. For example: "/listclasses"
# For each new endpoint here, create a new endpoint in the etc/krakend.json file
@app.get("/list/")
def list_open_classes(db: sqlite3.Connection = Depends(get_db)):
    classes = db.execute("SELECT * FROM Class")
    return {"class": classes.fetchall()}