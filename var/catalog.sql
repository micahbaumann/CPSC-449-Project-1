PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;

CREATE TABLE Classes (
    CourseCode VARCHAR(5) PRIMARY KEY NOT NULL UNIQUE,
    SectionNumber VARCHAR(5)NOT NULL,
    Name VARCHAR(100),
    InstructorID INT,
    CurrentEnrollment INT,
    MaximumEnrollment INT
);

CREATE TABLE Students (
    StudentID VARCHAR(5) PRIMARY KEY NOT NULL UNIQUE
);

CREATE TABLE StudentClasses (
    StudentID VARCHAR(5) PRIMARY KEY NOT NULL,
    ClassID VARCHAR(5),
    SectionID VARCHAR(5),
    EnrollmentStatus INT
);

CREATE TABLE Instructors (
    InstructorID VARCHAR(5) PRIMARY KEY NOT NULL UNIQUE
);

CREATE TABLE InstructorClasses (
    InstructorID VARCHAR(5) PRIMARY KEY NOT NULL,
    ClassID VARCHAR(5),
    SectionID VARCHAR(5)
);

CREATE TABLE Freeze (
    IsFrozen BOOLEAN DEFAULT 0
);

INSERT INTO Classes VALUES
("120A",5,'Introduction to Programming',1,15,30),
("121",5,'Object-Oriented Programming',1,30,30),
("131",5,'Data Structures',1,25,30);

INSERT INTO Students VALUES ("001"),("002"),("003"), ("004"),("005"),("006"),("007"),("008"),("009"),("010");

INSERT INTO StudentClasses VALUES
("001", "120A", 5, 0),
("002", "121",  5, 0);


INSERT INTO Instructors VALUES ("001"),("002"),("003"),("004"),("005");

INSERT INTO InstructorClasses VALUES 
("001","120A",5);

COMMIT;
