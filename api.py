import sqlite3
import contextlib

from fastapi import FastAPI, Depends, HTTPException, status, Response
from pydantic import BaseModel
from pydantic_settings import BaseSettings

WAITLIST_MAXIMUM = 15
MAXIMUM_WAITLISTED_CLASSES = 3

class Settings(BaseSettings, env_file=".env", extra="ignore"):
    database: str
    logging_config: str

def get_db():
    with contextlib.closing(sqlite3.connect(settings.database)) as db:
        db.row_factory = sqlite3.Row
        yield db

settings = Settings()
app = FastAPI()

def check_id_exists_in_table(id_name: str,id_val: int, table_name: str, db: sqlite3.Connection = Depends(get_db)) -> bool:
    """return true if value found, false if not found"""
    vals = db.execute(f"SELECT * FROM {table_name} WHERE {id_name} = ?",(id_val,)).fetchone()
    if vals:
        return True
    else:
        return False

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

@app.delete("/enrollmentdrop/{studentid}/{classid}") # Done
def drop_student_from_class(studentid: int, classid: int, response: Response, db: sqlite3.Connection = Depends(get_db)):
    # Try to Remove student from the class
    try:
        dropped_student = db.execute(f"SELECT StudentID FROM Enrollments WHERE StudentID = {studentid} AND ClassID = {classid}").fetchone()
    except sqlite3.IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_40,
            detail={"ErrorType": type(e).__name__, "ErrorMessage": str(e)}
        )
   
    query = db.execute(f"UPDATE Enrollments SET EnrollmentStatus = 'DROPPED' WHERE StudentID = {studentid} AND ClassID = {classid}")
    db.commit()
    # Add student to class if there are students in the waitlist for this course
    next_on_waitlist = db.execute(f"SELECT * FROM Waitlists WHERE ClassID = {classid} ORDER BY Position ASC").fetchone()
    if next_on_waitlist:
        db.execute(f"DELETE FROM Waitlists WHERE StudentID = {studentid} AND ClassID = {classid}")
        db.execute(f"  INSERT INTO Enrollments(StudentID, ClassID, SectionNumber,EnrollmentStatus) \
                       VALUES ({studentid}, {classid}, {dropped_student['SectionNumber'],'ENROLLED'})")
        db.execute("UPDATE Classes SET WaitlistCount = WaitlistCount + 1 WHERE ClassID = ?", (classid,))
        db.commit()
        return {"Result": [
            {"Student dropped from class": dropped_student}, 
            {"Student added from waitlist": next_on_waitlist},
        ]}
    if dropped_student:
        return {"Student dropped from class": dropped_student}
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student and class combination not found")
        #return {"Result": "Student and class combination not found"}

@app.delete("/waitlistdrop/{studentid}/{classid}") # Logan
def remove_student_from_waitlist(studentid: int, classid: int, db: sqlite3.Connection = Depends(get_db)):
    exists = db.execute(f"SELECT * FROM Waitlists WHERE StudentID = {studentid} AND ClassID = {classid}").fetchone()
    if exists:
        db.execute(f"DELETE FROM Waitlists WHERE StudentID = {studentid} AND ClassID = {classid}")
        db.execute("UPDATE Classes SET WaitlistCount = WaitlistCount - 1 WHERE ClassID = ?", (classid,))
        db.commit()
        return {"Element removed": exists}
    else:
        return {"Error": "No such student found in the given class on the waitlist"}

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

@app.get("/enrolled/{instructorid}/{classid}/{sectionid}") # Logan
def view_enrolled(instructorid: int, classid: int, sectionid: int, db: sqlite3.Connection = Depends(get_db)):
    enrolled = db.execute(f"SELECT StudentID FROM Enrollments as e INNER JOIN \
                                (SELECT ClassID FROM Classes WHERE InstructorID = {instructorid} AND ClassID = {classid}) as ic \
                            ON e.ClassID = ic.ClassID")
    
    return {"All students enrolled in this instructor's classes" : enrolled.fetchall()}

@app.get("/instructor/dropped/{instructorid}/{classid}/{sectionid}")
def view_dropped_students(instructorid: int, classid: int, sectionid: int, db: sqlite3.Connection = Depends(get_db)):
    query = "SELECT StudentID FROM Enrollments WHERE ClassID = ? AND SectionNumber = ? AND EnrollmentStatus = 'DROPPED'"
    dropped_students = db.execute(query, (classid, sectionid)).fetchall()
    if not dropped_students:
        raise HTTPException(status_code=404, detail="No dropped students found for this class.")
    return {"Dropped Students": [student["StudentID"] for student in dropped_students]}

@app.delete("/instructor/drop/{instructorid}/{classid}/{studentid}")
def drop_student_administratively(instructorid: int, classid: int, studentid: int, db: sqlite3.Connection = Depends(get_db)):
    query = "UPDATE Enrollments SET EnrollmentStatus = 'DROPPED' WHERE StudentID = ? AND ClassID = ?"
    result = db.execute(query, (studentid, classid))
    db.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Student, class, or section not found.")
    return {"message": f"Student {studentid} has been administratively dropped from class {classid}"}

@app.get("/waitlist/{instructorid}/{classid}/{sectionid}")
def view_waitlist(instructorid: int, classid: str, sectionid: int, db: sqlite3.Connection = Depends(get_db)):
    query = "SELECT StudentID, Position FROM Waitlists WHERE ClassID = ? AND SectionNumber =? AND InstructorID = ? ORDER BY Position"
    waitlist = db.execute(query, (classid, sectionid, instructorid)).fetchall()
    if not waitlist:
        raise HTTPException(status_code=404, detail="No students found in the waitlist for this class.")
    return {"Waitlist": [{"student_id": student["StudentID"], "position": student["Position"]} for student in waitlist]}

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

@app.put("/freeze/{isfrozen}", status_code=status.HTTP_204_NO_CONTENT) # Done
def freeze_enrollment(isfrozen: str, db: sqlite3.Connection = Depends(get_db)):
    if (isfrozen.lower() == "true"):
        db.execute("UPDATE Freeze SET IsFrozen = true")
        db.commit()
    elif (isfrozen.lower() == "false"):
        db.execute("UPDATE Freeze SET IsFrozen = false")
        db.commit()
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Freeze must be true or false.")

@app.get("/checkfrozen")
def check_frozen_status(db: sqlite3.Connection = Depends(get_db)):
    checkFrozen = db.execute("SELECT IsFrozen FROM Freeze").fetchone()
    if (checkFrozen[0] == 1):
        checkFrozen = True
    else:
        checkFrozen = False
    return {"Enrollment Frozen": checkFrozen}

@app.put("/change/{classid}/{newprofessorid}", status_code=status.HTTP_204_NO_CONTENT) # Done
def change_prof(classid: int, newprofessorid: int, db: sqlite3.Connection = Depends(get_db)):
    valid_instructor_id = check_id_exists_in_table("InstructorID",newprofessorid,"Classes",db)
    valid_class_id = check_id_exists_in_table("ClassID",classid,"Classes",db)
    if not valid_instructor_id or not valid_class_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class or Instructor does not exist",
        )
    try:
        db.execute("UPDATE Classes SET InstructorID=? WHERE ClassID=?", (newprofessorid, classid))
        db.execute("UPDATE InstructorClasses SET InstructorID=? WHERE ClassID=?", (newprofessorid, classid))
        db.commit()
    except sqlite3.IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"type": type(e).__name__, "msg": str(e)},
        )

