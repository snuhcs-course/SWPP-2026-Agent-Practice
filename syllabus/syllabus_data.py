"""Mock syllabus data for SWPP 2026 Fall.

Swap in the real syllabus and tools.py keeps working, as long as the shape stays
the same. For student handouts, this is the only file that needs replacing.
"""

COURSE = {
    "code": "M1522.000600",
    "title": "Software Development Principles and Practices",
    "term": "2026 Fall",
    "instructor": "Youngki Lee",
    "ta_email": "swpp-ta@hcs.snu.ac.kr",
    "lecture_time": "Tue/Thu 14:00-15:15",
    "room": "302-208",
}

# Weekly schedule. `due` is None when there is nothing to hand in.
SCHEDULE = [
    {"week": 1,  "topic": "Course Introduction & Software Process", "assignment": None,            "due": None},
    {"week": 2,  "topic": "Version Control and Git Workflow",       "assignment": "Lab 1: Git",    "due": "2026-09-15"},
    {"week": 3,  "topic": "Requirements and User Stories",          "assignment": "Lab 2: Specs",  "due": "2026-09-22"},
    {"week": 4,  "topic": "Software Design Principles",             "assignment": "Project Proposal", "due": "2026-09-29"},
    {"week": 5,  "topic": "Agents and Agentic Systems",             "assignment": "Lab 3: Agents", "due": "2026-10-13"},
    {"week": 6,  "topic": "Testing and Test-Driven Development",    "assignment": "Lab 4: Testing", "due": "2026-10-20"},
    {"week": 7,  "topic": "Continuous Integration and Deployment",  "assignment": None,            "due": None},
    {"week": 8,  "topic": "Midterm Exam",                           "assignment": "Midterm",       "due": "2026-10-29"},
    {"week": 9,  "topic": "Refactoring and Code Smells",            "assignment": "Lab 5: Refactoring", "due": "2026-11-10"},
    {"week": 10, "topic": "Design Patterns",                        "assignment": None,            "due": None},
    {"week": 11, "topic": "Software Architecture",                  "assignment": "Project Milestone 1", "due": "2026-11-24"},
    {"week": 12, "topic": "Performance and Profiling",              "assignment": None,            "due": None},
    {"week": 13, "topic": "Security in Software Development",       "assignment": "Lab 6: Security", "due": "2026-12-08"},
    {"week": 14, "topic": "Project Presentations",                  "assignment": "Final Presentation", "due": "2026-12-15"},
    {"week": 15, "topic": "Final Exam",                             "assignment": "Final Exam",    "due": "2026-12-17"},
]

GRADING = {
    "Labs (6)": 30,
    "Team Project": 30,
    "Midterm Exam": 20,
    "Final Exam": 15,
    "Participation": 5,
}

POLICIES = {
    "late_submission": (
        "Assignments may be submitted up to 24 hours late for a 10% penalty, and up to "
        "48 hours late for a 30% penalty. After 48 hours the submission receives 0. "
        "Each student may request one penalty-free 24-hour extension per semester."
    ),
    "attendance": (
        "Attendance counts toward the 5% participation score. The first 3 absences carry "
        "no penalty. From the 4th absence onward, each absence costs 1 point of "
        "participation. A student with 6 or more absences receives an F for the course."
    ),
    "academic_integrity": (
        "All assignments are done individually or within the assigned team. Copying code "
        "verbatim, or submitting AI-generated code without disclosure, is treated as "
        "academic misconduct. Using AI tools is permitted, but REPORT.md must state which "
        "tools were used and how."
    ),
    "team_formation": (
        "Teams for the project consist of 4 students. Teams must be registered on eTL by "
        "Friday of week 4. Students without a team are assigned by the TA. Changing teams "
        "mid-semester is not normally allowed."
    ),
    "office_hours": (
        "Instructor office hours are Wednesdays 15:00-17:00 in room 302-426. "
        "TA office hours are Mondays 16:00-18:00 in room 302-311, by appointment."
    ),
}

POLICY_TOPICS = tuple(POLICIES.keys())
