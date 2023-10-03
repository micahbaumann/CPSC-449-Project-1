import sqlite3
import contextlib

from fastapi import FastAPI, Depends
from pydantic import BaseModel
from pydantic_settings import BaseSettings


class Settings(BaseSettings, env_file=".env", extra="ignore"):
    database: str
    logging_config: str

class Frozen(BaseSettings, env_file=".env", extra="ignore"):
    is_frozen: bool

class Classes(BaseModel):
    Department: str
    class_code: str
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
frozen = Frozen()
app = FastAPI()

# This is an example endpoint. Change the "/" to the path. For example: "/listclasses"
# For each new endpoint here, create a new endpoint in the etc/krakend.json file

### Student related endpoints
@app.get("/")
def greet():
    return {"Hello": "World"}

@app.get("/list/")
def list_open_classes(db: sqlite3.Connection = Depends(get_db)):
    classes = db.execute("SELECT * FROM Classes WHERE Classes.CurrentEnrollment < Classes.MaximumEnrollment")
    return {"Classes": classes.fetchall()}

@app.post("/enroll/{studentid}/{classid}")
def enroll_student_in_class(studentid: int, classid: str, db: sqlite3.Connection = Depends(get_db)):
    return {}

@app.delete("/drop/{studentid}/{classid}")
def drop_student_from_class(studentid: int, classid: str, db: sqlite3.Connection = Depends(get_db)):
    return {}

@app.get("/waitlist/{studentid}/{classid}")
def view_waitlist_position(studentid: int, classid: str, db: sqlite3.Connection = Depends(get_db)):
    return {}


### Instructor related endpoints

@app.get("enrolled/{instructorid}/{classid}")
def view_enrolled(instructorid: int, classid: str, db: sqlite3.Connection = Depends(get_db)):
    return {}

@app.get("dropped/{instructorid}/{classid}")
def view_dropped(instructorid: int, classid: str, db: sqlite3.Connection = Depends(get_db)):
    return {}

@app.delete("drop/{instructorid}/{classid}/{studentid}")
def drop_student(instructorid: int, classid: str,studentid,int, db: sqlite3.Connection = Depends(get_db)):
    return {}





### Registrar related endpoints

@app.put("/freeze/")
def view_waitlist_position():
    frozen.is_frozen = True
    return {}