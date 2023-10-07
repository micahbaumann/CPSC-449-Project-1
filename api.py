import sqlite3
import contextlib

from fastapi import FastAPI, Depends, HTTPException, status
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

@app.post("/enroll/{studentid}/{classid}/{sectionid}", status_code=status.HTTP_201_CREATED) # Janhvi
def enroll_student_in_class(studentid: int, classid: int, sectionid: int, db: sqlite3.Connection = Depends(get_db)):
    classes = db.execute("SELECT * FROM Classes WHERE ClassID = ?", (classid,)).fetchone()
    if not classes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found")
    class_section = classes["SectionNumber"]
    instructorid = classes["InstructorID"]
    count = db.execute("SELECT COUNT() FROM Enrollments WHERE ClassID = ?", (classid,)).fetchone()[0]
    waitlist_count = db.execute("SELECT COUNT() FROM Waitlists WHERE ClassID = ?", (classid,)).fetchone()[0]
    print(count)
    if count <= classes["MaximumEnrollment"]:
        db.execute("INSERT INTO Enrollments(StudentID, ClassID, SectionNumber) VALUES(?,?,?)",(studentid, classid, class_section))
        db.commit()
        return {"message": f"Enrolled student {studentid} in section {class_section} of class {classid}."}
    elif waitlist_count <= WAITLIST_MAXIMUM:

        max_waitlist_position = db.execute("SELECT MAX(Position) FROM Waitlists WHERE ClassID = ? AND  SectionNumber = ?",(classid,sectionid)).fetchone()[0]
        print("Position: " + str(max_waitlist_position))
        db.execute("INSERT INTO Waitlists(StudentID, ClassID, SectionNumber, InstructorID, Position) VALUES(?,?,?,?,?)",(studentid, classid, class_section,instructorid,max_waitlist_position + 1))
        db.commit()
        return {"message": f"Enrolled in waitlist {class_section} of class {classid}."}
    else:
        return {"message": f"Unable to enroll in waitlist for the class, reached the maximum number of students"}

@app.delete("/enrollmentdrop/{studentid}/{classid}/{sectionid}") # Done
def drop_student_from_class(studentid: int, classid: int,sectionid: int, db: sqlite3.Connection = Depends(get_db)):
    # Try to Remove student from the class
    
    dropped_student = db.execute("SELECT StudentID FROM Enrollments WHERE StudentID = ? AND ClassID = ? AND SectionNumber = ?",(studentid,classid,sectionid)).fetchone()
    if not dropped_student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Student and class combination not found")

    query = db.execute("UPDATE Enrollments SET EnrollmentStatus = 'DROPPED' WHERE StudentID = ? AND ClassID = ?", (studentid, classid))
    db.commit()
    # Add student to class if there are students in the waitlist for this class
    next_on_waitlist = db.execute("SELECT * FROM Waitlists WHERE ClassID = ? ORDER BY Position ASC", (classid,)).fetchone()
    if next_on_waitlist:
        try:
            db.execute("INSERT INTO Enrollments(StudentID, ClassID, SectionNumber,EnrollmentStatus) \
                            VALUES (?, ?, ?,'ENROLLED')", (next_on_waitlist['StudentID'], classid, sectionid))
            db.execute("DELETE FROM Waitlists WHERE StudentID = ? AND ClassID = ?", (next_on_waitlist['StudentID'], classid))
            db.execute("UPDATE Classes SET WaitlistCount = WaitlistCount - 1 WHERE ClassID = ?", (classid,))
            db.commit()
        except sqlite3.IntegrityError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "ErrorType": type(e).__name__, 
                    "ErrorMessage": str(e)
                },
            )
        
        return {"Result": [
            {"Student dropped from class": dropped_student}, 
            {"Student added from waitlist": next_on_waitlist},
        ]}
    return {"Result": [{"Student dropped from class": dropped_student} ]}

@app.delete("/waitlistdrop/{studentid}/{classid}") # Logan DONE
def remove_student_from_waitlist(studentid: int, classid: int, db: sqlite3.Connection = Depends(get_db)):
    exists = db.execute("SELECT * FROM Waitlists WHERE StudentID = ? AND ClassID = ?", (studentid, classid)).fetchone()
    if not exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"Error": "No such student found in the given class on the waitlist"}
        )
    db.execute("DELETE FROM Waitlists WHERE StudentID = ? AND ClassID = ?", (studentid, classid))
    db.execute("UPDATE Classes SET WaitlistCount = WaitlistCount - 1 WHERE ClassID = ?", (classid,))
    db.commit()
    return {"Element removed": exists}
    
@app.get("/waitlist/{studentid}/{classid}") # Janhvi DONE
def view_waitlist_position(studentid: int, classid: int, db: sqlite3.Connection = Depends(get_db)):
    position = None
    position = db.execute("SELECT Position FROM Waitlists WHERE StudentID = ? AND ClassID = ?", (studentid,classid,)).fetchone()
    
    if position:
        message = f"Student {studentid} is on the waitlist for class {classid} in position"
    else:
        message = f"Student {studentid} is not on the waitlist for class {classid}"
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=message,
        )
    return {message: position}
    
### Instructor related endpoints

@app.get("/enrolled/{instructorid}/{classid}/{sectionid}") # Logan DONE
def view_enrolled(instructorid: int, classid: int, sectionid: int, db: sqlite3.Connection = Depends(get_db)):
    enrolled_students = db.execute("SELECT * FROM Students INNER JOIN (SELECT StudentID FROM Enrollments as e INNER JOIN \
                                    (SELECT ClassID FROM Classes WHERE InstructorID = ? AND ClassID = ? AND SectionNumber = ?) as ic \
                                ON e.ClassID = ic.ClassID WHERE e.EnrollmentStatus = \"ENROLLED\") as si \
                            ON Students.StudentID = si.StudentID",(instructorid,classid,sectionid))
    enrolled = enrolled_students.fetchall()
    if enrolled:
        return {"All students enrolled in this instructor's classes" : enrolled}
    else:
        raise HTTPException(
            status_code=status.HTTP_204_NO_CONTENT,
        )

@app.get("/dropped/{instructorid}/{classid}/{sectionid}") # Arjit DONE
def view_dropped_students(instructorid: int, classid: int, sectionid: int, db: sqlite3.Connection = Depends(get_db)):
    query = "SELECT StudentID FROM Enrollments WHERE ClassID = ? AND SectionNumber = ? AND EnrollmentStatus = 'DROPPED'"
    dropped_students = db.execute(query, (classid, sectionid)).fetchall()
    if not dropped_students:
        raise HTTPException(status_code=404, detail="No dropped students found for this class.")
    return {"Dropped Students ID": [student["StudentID"] for student in dropped_students]}

@app.delete("/drop/{instructorid}/{classid}/{studentid}") #Arjit DONE
def drop_student_administratively(instructorid: int, classid: int, studentid: int, db: sqlite3.Connection = Depends(get_db)):
    query = "UPDATE Enrollments SET EnrollmentStatus = 'DROPPED' WHERE StudentID = ? AND ClassID = ?"
    result = db.execute(query, (studentid, classid))
    db.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Student, class, or section not found.")
    return {"message": f"Student {studentid} has been administratively dropped from class {classid}"}

@app.get("/waitlist/{instructorid}/{classid}/{sectionid}") #Arjit DONE
def view_waitlist(instructorid: int, classid: str, sectionid: int, db: sqlite3.Connection = Depends(get_db)):
    query = "SELECT * FROM Students INNER JOIN (SELECT StudentID, Position FROM Waitlists WHERE ClassID = ? AND SectionNumber =? AND InstructorID = ? ORDER BY Position) as w on Students.StudentID = w.StudentID"
    waitlist = db.execute(query, (classid, sectionid, instructorid)).fetchall()
    if not waitlist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No students found in the waitlist for this class")
    return {"Waitlist": [{"student_id": student["StudentID"], "Email": student["Email"], "Name": student["Name"],"position": student["Position"]} for student in waitlist]}

### Registrar related endpoints

@app.post("/add/{classid}/{sectionid}/{instructorid}", status_code=status.HTTP_201_CREATED) # Melissa DONE
def add_class(classid: str, sectionid: str, instructorid: str, db: sqlite3.Connection = Depends(get_db)):
    try:
        db.execute(f"INSERT INTO Classes (ClassID,SectionNumber, InstructorID) VALUES({classid}, {sectionid}, {instructorid})")
        db.commit()
    except sqlite3.IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "ErrorType": type(e).__name__, 
                "ErrorMessage": str(e)
            },
        )
    return {"New Class Added":f"Course {classid} Section {sectionid}"}

@app.delete("/remove/{classid}/{sectionid}") # Melissa DONE
def remove_class(classid: str, sectionid: str, db: sqlite3.Connection = Depends(get_db)):

    class_found = db.execute("SELECT * FROM Classes WHERE ClassID = ? AND SectionNumber = ?",(classid,sectionid)).fetchone()
    if not class_found:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Class {classid} Section {sectionid} does not exist in database.")
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

@app.put("/change/{classid}/{newprofessorid}", status_code=status.HTTP_204_NO_CONTENT) # Micah Done
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

