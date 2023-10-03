import sqlite3
import contextlib

from fastapi import FastAPI, Depends
from pydantic import BaseModel
from pydantic_settings import BaseSettings
from fastapi import HTTPException


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

#View students who have dropped the class
@app.get("/instructor/dropped/{instructorid}/{classid}")
def view_dropped_students(instructorid: int, classid: int, db: sqlite3.Connection = Depends(get_db)):
    query = "SELECT StudentID FROM StudentClasses WHERE ClassID = ? AND SectionID = ? AND EnrollmentStatus = 'Dropped'"
    dropped_students = db.execute(query, (classid, instructorid)).fetchall()
    if not dropped_students:
        raise HTTPException(status_code=404, detail="No dropped students found for this class.")
    return {"Dropped Students": [student["StudentID"] for student in dropped_students]}

#Drop students administratively (e.g. if they do not show up to class)
@app.delete("/instructor/drop/{instructorid}/{classid}/{studentid}")
def drop_student_administratively(instructorid: int, classid: int, studentid: int, db: sqlite3.Connection = Depends(get_db)):
    query = "UPDATE StudentClasses SET EnrollmentStatus = 'Dropped' WHERE StudentID = ? AND ClassID = ? AND SectionID = ?"
    result = db.execute(query, (studentid, classid, instructorid))
    db.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Student, class, or section not found.")
    return {"message": f"Student {studentid} has been administratively dropped from class {classid}"}

# View the current waiting list for the course
@app.get("/instructor/waitlist/{instructorid}/{classid}")
def view_waitlist(instructorid: int, classid: int, db: sqlite3.Connection = Depends(get_db)):
    query = "SELECT StudentID, Position FROM Waitlist WHERE ClassID = ? AND SectionID = ? ORDER BY Position"
    waitlist = db.execute(query, (classid, instructorid)).fetchall()
    if not waitlist:
        raise HTTPException(status_code=404, detail="No students found in the waitlist for this class.")
    return {"Waitlist": [{"student_id": student["StudentID"], "position": student["Position"]} for student in waitlist]}

### Registrar related endpoints

@app.put("/freeze/")
def view_waitlist_position():
    frozen.is_frozen = True
    return {}