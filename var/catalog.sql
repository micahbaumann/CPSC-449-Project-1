PRAGMA foreign_keys=ON;
BEGIN TRANSACTION;

CREATE TABLE Classes (
    ClassID INT NOT NULL UNIQUE,
    CourseCode VARCHAR(15) NOT NULL DEFAULT 'XXX 001',
    SectionNumber INT NOT NULL,
    Name VARCHAR(100) DEFAULT "Class", 
    InstructorID INT NOT NULL,
    MaximumEnrollment INT DEFAULT 30,
    WaitlistCount INT DEFAULT 0,
    WaitlistMaximum INT DEFAUlT 15,
    PRIMARY KEY (ClassID, SectionNumber)
);

INSERT INTO Classes VALUES
(1,"120A",5,'Introduction to Programming',1,30,2,15),
(2,"121", 5,'Object-Oriented Programming',1,30,1,15),
(3,"131", 5,'Data Structures',            2,30,0,15),
(4,"223P",5,'Intro to Python Programming',3,30,0,15),
(5,"223W",5,'Intro to Python Programming Waitlist',3,2,0,15);

CREATE TABLE Students (
    StudentID INT PRIMARY KEY NOT NULL UNIQUE,
    Name VARCHAR(100),
    Email VARCHAR(100)
);

INSERT INTO Students VALUES 
(1,  "Fara Smith", "fsmith@csu.fullerton.edu"),
(2,  "Steve Jobs", "sjobs@csu.fullerton.edu"),
(3,  "Andy Jones", "ajones@csu.fullerton.edu"),
(4,  "Tim Raft",   "traft@csu.fullerton.edu"),
(5,  "Elizabeth Barnes", "ebarnes@csu.fullerton.edu"),
(6,  "George Derns", "gderns@csu.fullerton.edu"),
(7,  "Pheobe Essek", "pessek@fsmithcsu.fullerton.edu"),
(8,  "Earl Poppins", "epoppins@csu.fullerton.edu"),
(9,  "Sarah Colyt", "fsmith@csu.fullerton.edu"),
(10, "Anna Kant", "akant@csu.fullerton.edu");

CREATE TABLE Enrollments (
    EnrollmentID INTEGER         NOT NULL PRIMARY KEY AUTOINCREMENT,
    StudentID INT                NOT NULL,
    ClassID INT                  NOT NULL,
    SectionNumber INT            NOT NULL,
    EnrollmentStatus VARCHAR(25) NOT NULL DEFAULT "ENROLLED",
    FOREIGN KEY (StudentID) REFERENCES Students(StudentID),
    FOREIGN KEY (ClassID, SectionNumber) REFERENCES Classes(ClassID, SectionNumber)
);

INSERT INTO Enrollments(StudentID,ClassID,SectionNumber,EnrollmentStatus) VALUES
(1,1,5,"ENROLLED"),
(2,2,5,"ENROLLED"),
(2,3,5,"ENROLLED"),
(3,5,5,"ENROLLED"),
(2,5,5,"ENROLLED");


CREATE TABLE Instructors (
    InstructorID INT PRIMARY KEY NOT NULL UNIQUE
);

INSERT INTO Instructors VALUES (1),(2),(3),(4),(5);

CREATE TABLE InstructorClasses (
    InstructorClassesID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    InstructorID INT            NOT NULL,
    ClassID INT                 NOT NULL,
    SectionNumber INT           NOT NULL,
    FOREIGN KEY (InstructorID) REFERENCES Instructors(InstructorID),
    FOREIGN KEY (ClassID, SectionNumber) REFERENCES Classes(ClassID, SectionNumber)
);

INSERT INTO InstructorClasses VALUES 
(1,1,1,5),
(2,2,1,5),
(3,3,3,5),
(4,4,4,5);

CREATE TABLE Waitlists (
    WaitlistID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    StudentID INT      NOT NULL,
    ClassID INT        NOT NULL,
    InstructorID INT   NOT NULL,
    SectionNumber INT  NOT NULL,
    Position INT       NOT NULL,
    FOREIGN KEY (StudentID) REFERENCES Students(StudentID),
    FOREIGN KEY (InstructorID) REFERENCES Instructors(InstructorID),
    FOREIGN KEY (ClassID, SectionNumber) REFERENCES Classes(ClassID, SectionNumber)
);

INSERT INTO Waitlists(StudentID,ClassId,InstructorID,SectionNumber,Position) VALUES
(1,1,1,5,1),
(2,2,1,5,2),
(3,1,3,5,5);

CREATE TABLE Freeze (
    IsFrozen BOOLEAN DEFAULT 0
);

INSERT INTO Freeze VALUES (0);

COMMIT;
