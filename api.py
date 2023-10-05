import sqlite3
import contextlib

from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from pydantic_settings import BaseSettings


class Settings(BaseSettings, env_file=".env", extra="ignore"):
    database: str
    logging_config: str

def get_db():
    with contextlib.closing(sqlite3.connect(settings.database)) as db:
        db.row_factory = sqlite3.Row
        yield db

settings = Settings()
app = FastAPI()

# This is an example endpoint. Change the "/" to the path. For example: "/listclasses"
# For each new endpoint here, create a new endpoint in the etc/krakend.json file

### Student related endpoints
@app.get("/")
def greet():
    return {"Hello": "World"}

@app.get("/list/")
def list_open_classes(db: sqlite3.Connection = Depends(get_db)):
    if (db.execute("SELECT IsFrozen FROM Freeze").fetchone()[0] == 1):
        return {"Classes": []}

    classes = db.execute("SELECT * FROM Classes WHERE Classes.CurrentEnrollment < Classes.MaximumEnrollment OR WaitlistCount < WaitlistMaximum")
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

@app.get("/enrolled/{instructorid}/{classid}")
def view_enrolled(instructorid: int, classid: str, db: sqlite3.Connection = Depends(get_db)):
    enrolled = db.execute("SELECT CurrentEnrollment FROM Classes WHERE InstructorID = ? AND ClassID = ?", (instructorid,classid)).fetchone()
    if not enrolled:
            return{"message" : f"There are no students enrolled in instructor: {instructorid } with classID: {classid}"}
    return {"Enrolled": enrolled}

@app.get("/dropped/{instructorid}/{classid}")
def view_dropped(instructorid: int, classid: str, db: sqlite3.Connection = Depends(get_db)):
    return {}

@app.delete("/drop/{instructorid}/{classid}/{studentid}")
def drop_student(instructorid: int, classid: str,studentid: int, db: sqlite3.Connection = Depends(get_db)):
    return {}

@app.get("/waitlist/{instructorid}/{classid}/{studentid}")
def view_waitlist(instructorid: int, classid: str, db: sqlite3.Connection = Depends(get_db)):
    return {}


### Registrar related endpoints
@app.post("/add/{classid}/{sectionid}")
def add_class(classid: str, sectionid: str, db: sqlite3.Connection = Depends(get_db)):
    db.execute("INSERT INTO Classes (ClassID,SectionNumber) VALUES(classid, sectionid)")
    db.commit
    return {"New Class Added":f"Course {classid} Section {sectionid}"}

@app.post("/remove/{classid}/{sectionid}")
def remove_class(classid: str, sectionid: str, db: sqlite3.Connection = Depends(get_db)):
    db.execute("DELETE FROM Classes WHERE ClassID ?= AND SectionNumber ?=", (classid, sectionid))
    db.commit()
    return {"Removed" : f"Course {classid} Section {sectionid}"}

@app.put("/freeze/{isfrozen}/")
def freeze_enrollment(isfrozen: str, db: sqlite3.Connection = Depends(get_db)):
    if (isfrozen.lower() == "true"):
        db.execute("UPDATE Freeze SET IsFrozen = true")
        db.commit()
    elif (isfrozen.lower() == "false"):
        db.execute("UPDATE Freeze SET IsFrozen = false")
        db.commit()
    else:
        raise HTTPException(status_code=500, detail="Freeze must be true or false.")
    
    checkFrozen = db.execute("SELECT IsFrozen FROM Freeze").fetchone()
    if (checkFrozen[0] == 1):
        checkFrozen = True
    else:
        checkFrozen = False
    return {"Enrollment Frozen": checkFrozen}

@app.get("/checkfrozen/")
def check_frozen_status(db: sqlite3.Connection = Depends(get_db)):
    checkFrozen = db.execute("SELECT IsFrozen FROM Freeze").fetchone()
    if (checkFrozen[0] == 1):
        checkFrozen = True
    else:
        checkFrozen = False
    return {"Enrollment Frozen": checkFrozen}

@app.put("/change/{classid}/{sectionid}/{newprofessorid}/")
def change_prof(classid: str, sectionid: str, newprofessorid: str, db: sqlite3.Connection = Depends(get_db)):
    db.execute("UPDATE Classes SET InstructorID=? WHERE ClassID=? AND SectionNumber=?", (newprofessorid, classid, sectionid))
    db.execute("UPDATE InstructorClasses SET InstructorID=? WHERE ClassID=? AND SectionID=?", (newprofessorid, classid, sectionid))
    db.commit()
    checkProf = db.execute("SELECT * FROM Classes WHERE ClassID=? AND SectionNumber=?", (classid, sectionid)).fetchone()
    return {"Professor Class": checkProf}

