import sqlite3
import contextlib

from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel
from pydantic_settings import BaseSettings


class Settings(BaseSettings, env_file=".env", extra="ignore"):
    database: str
    logging_config: str

def get_db():
    with contextlib.closing(sqlite3.connect(settings.database)) as db:
        db.row_factory = sqlite3.Row
        yield db

WAITLIST_MAXIMUM = 15

settings = Settings()
app = FastAPI()

# This is an example endpoint. Change the "/" to the path. For example: "/listclasses"
# For each new endpoint here, create a new endpoint in the etc/krakend.json file

@app.get("/")
def greet():
    return {"Hello": "World"}

### Student related endpoints

@app.get("/list") # Done
def list_open_classes(db: sqlite3.Connection = Depends(get_db)):
    if (db.execute("SELECT IsFrozen FROM Freeze").fetchone()[0] == 1):
        return {"Classes": []}
    
    classes = db.execute(
        "SELECT * FROM Classes WHERE \
            Classes.MaximumEnrollment > (SELECT COUNT(EnrollmentID) FROM Enrollments WHERE Enrollments.ClassID = Classes.ClassID) \
            OR Classes.WaitlistMaximum > (SELECT COUNT(WaitlistID) FROM Waitlists WHERE Waitlists.ClassID = Classes.ClassID)"
    )
    return {"Classes": classes.fetchall()}

@app.post("/enroll/{studentid}/{classid}/{sectionid}") # Janhvi
def enroll_student_in_class(studentid: int, classid: int, sectionid: int, db: sqlite3.Connection = Depends(get_db)):
    class_data = db.execute("SELECT * FROM Classes WHERE ClassID = ?", (classid,)).fetchone()
    if not class_data:
        raise HTTPException(status_code=404, detail="Class not found")
    if class_data["CurrentEnrollment"] >= class_data["MaximumEnrollment"]:
        if class_data["WaitlistCount"] < class_data["WaitlistMaximum"]:
            db.execute("UPDATE Classes SET WaitlistCount = WaitlistCount + 1 WHERE ClassID = ?", (classid,))
            db.commit()
            db.execute("INSERT INTO Waitlists (StudentID, ClassID) VALUES (?, ?)", (studentid, classid))
            db.commit()
            return {"message": f"Student {studentid} added to the waitlist for class {classid} section {sectionid}"}
        else:
            raise HTTPException(status_code=400, detail="Class and waitlist are full")

    db.execute("UPDATE Classes SET CurrentEnrollment = CurrentEnrollment + 1 WHERE ClassID = ?", (classid,))
    db.commit()

    db.execute("INSERT INTO Enrollments (StudentID, ClassID) VALUES (?, ?)", (studentid, classid))
    db.commit()

    return {"message": f"Student {studentid} enrolled in class {classid}"}

@app.delete("/waitlistdrop/{studentid}/{classid}")
def drop_student_from_class(studentid: int, classid: str, db: sqlite3.Connection = Depends(get_db)):
    # Remove student from the class
    db.execute(f"DELETE FROM Enrollments WHERE StudentID = {studentid} AND ClassID = {classid}")
    db.commit()

    # Add student to class if there are students in the waitlist
    waitlist_count = db.execute(f"SELECT COUNT(StudentID) FROM Waitlists WHERE ClassID = {classid}").fetchone()[0]
    #if waitlist_count > 0:
        #db.execute("SELECT MAX() FROM Enrollments")
    
    return {"Student dropped": True}

@app.delete("/enrollmentdrop/{studentid}/{classid}") # Logan
def remove_student_from_waitlist(studentid: int, classid: str, db: sqlite3.Connection = Depends(get_db)):
    #???
    return {}

@app.get("/waitlist/{studentid}/{classid}") # Janhvi
def view_waitlist_position(studentid: int, classid: int, sectionid: int, db: sqlite3.Connection = Depends(get_db)):
    try:
        waitlist_data = db.execute("SELECT Position FROM Waitlists WHERE StudentID = :studentid AND ClassID = :classid", {"studentid": studentid, "classid": classid}).fetchone()
        position = waitlist_data["Position"]
        message = f"Student {studentid} is on the waitlist for class {classid}"
    except TypeError:
        message = f"Student {studentid} is not on the waitlist for class {classid}"
    return {"message": message}
    
### Instructor related endpoints

@app.get("/enrolled/{instructorid}/{classid}") # Logan
def view_enrolled(instructorid: int, classid: str, db: sqlite3.Connection = Depends(get_db)):
    enrolled = db.execute(f"SELECT * FROM Students (SELECT c.ClassID\
                            FROM Instructors as i INNER JOIN Classes as c \
                            ON c.InstructorID = i.InstructorID \
                            WHERE i.InstructorID = {instructorid} AND c.Classid = {classid})")
    
    return {"All students enrolled in this instructor's classes" : enrolled.fetchall()}

@app.get("/dropped/{instructorid}/{classid}")
def view_dropped(instructorid: int, classid: str, db: sqlite3.Connection = Depends(get_db)):
    res = db.execute(f" SELECT * FROM Enrollments as e \
                        WHERE e.ClassID = {classid} \
                        AND e.EnrollmentStatus = \"NOT ENROLLED\"")
    


    return {"Dropped students": res.fetchall()}

@app.delete("/drop/{instructorid}/{classid}/{studentid}")
def drop_student(instructorid: int, classid: str,studentid: int, db: sqlite3.Connection = Depends(get_db)):
    return {}

@app.get("/waitlist/{instructorid}/{classid}/{studentid}")
def view_waitlist(instructorid: int, classid: str, db: sqlite3.Connection = Depends(get_db)):
    return {}

### Registrar related endpoints

@app.post("/add/{classid}/{sectionid}") # Melissa
def add_class(classid: str, sectionid: str, db: sqlite3.Connection = Depends(get_db)):
    db.execute("INSERT INTO Classes (ClassID,SectionNumber) VALUES(classid, sectionid)")
    db.commit
    return {"New Class Added":f"Course {classid} Section {sectionid}"}

@app.delete("/remove/{classid}/{sectionid}") # Melissa
def remove_class(classid: str, sectionid: str, db: sqlite3.Connection = Depends(get_db)):
    db.execute("DELETE FROM Classes WHERE ClassID =? AND SectionNumber =?", (classid, sectionid))
    db.commit()
    return {"Removed" : f"Course {classid} Section {sectionid}"}

@app.put("/freeze/{isfrozen}", status_code=status.HTTP_201_CREATED) # Done
def freeze_enrollment(isfrozen: str, db: sqlite3.Connection = Depends(get_db)):
    if (isfrozen.lower() == "true"):
        db.execute("UPDATE Freeze SET IsFrozen = true")
        db.commit()
    elif (isfrozen.lower() == "false"):
        db.execute("UPDATE Freeze SET IsFrozen = false")
        db.commit()
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Freeze must be true or false.")
    
    checkFrozen = db.execute("SELECT IsFrozen FROM Freeze").fetchone()
    if (checkFrozen[0] == 1):
        checkFrozen = True
    else:
        checkFrozen = False
    return {"Enrollment Frozen": checkFrozen}

@app.get("/checkfrozen")
def check_frozen_status(db: sqlite3.Connection = Depends(get_db)):
    checkFrozen = db.execute("SELECT IsFrozen FROM Freeze").fetchone()
    if (checkFrozen[0] == 1):
        checkFrozen = True
    else:
        checkFrozen = False
    return {"Enrollment Frozen": checkFrozen}

@app.put("/change/{classid}/{newprofessorid}", status_code=status.HTTP_201_CREATED) # Done
def change_prof(classid: int, newprofessorid: int, db: sqlite3.Connection = Depends(get_db)):
    db.execute("UPDATE Classes SET InstructorID=? WHERE ClassID=?", (newprofessorid, classid))
    db.execute("UPDATE InstructorClasses SET InstructorID=? WHERE ClassID=?", (newprofessorid, classid))
    db.commit()
    checkProf = db.execute("SELECT * FROM Classes WHERE ClassID=?", (classid,)).fetchone()
    return {"Professor Class": checkProf}

