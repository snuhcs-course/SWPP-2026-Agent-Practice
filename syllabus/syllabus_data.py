"""Real syllabus data for SWPP 2026 Fall (M1522.002400), sourced from swpp_syllabus.pdf.

Two kinds of fields live here, and the comments below say which is which:

  REAL        - taken directly from swpp_syllabus.pdf (course info, weekly topics,
                grading breakdown, attendance policy, AI-tool disclosure policy).
  PLACEHOLDER - the official syllabus does not specify this at all (per-week
                assignment names and due dates, TA email, exact team size, a
                late-submission percentage policy). Kept as illustrative data so
                the tool-design lab still has something to look up - the official
                PDF's own "Weekly Lecture Plan" table literally says "there is no
                weekly lecture plans," and this course's real grading has no
                exam/lab line items to look up by name. Placeholder assignments are
                positioned under the REAL week that topically matches them (e.g. a
                Git lab under the real "Version Control with Git" week), not just
                copied over at their old week numbers.

tools.py keeps working as long as the shape stays the same. For student handouts,
this is the only file that needs replacing.
"""

COURSE = {
    "code": "M1522.002400",                                            # REAL
    "title": "Principles and Practices of Software Development",       # REAL
    "term": "2026 Fall",                                                # REAL
    "credits": 4,                                                       # REAL
    "instructor": "Youngki Lee",                                        # REAL
    "lecture_time": "Mon/Wed 15:30-16:45 (Theory), Wed 19:00-20:50 (Practice)",  # REAL
    "room": "302-311-1",                                                # REAL
    "ta_email": "swpp-ta@hcs.snu.ac.kr",       # PLACEHOLDER - no TA contact in the PDF
}

# Weekly schedule. `topic` is REAL (swpp_syllabus.pdf, section 7, "Lecture Plan").
# `assignment` / `due` are PLACEHOLDER - the PDF names no assignments or dates at all.
SCHEDULE = [
    {"week": 1,  "topic": "Course Overview and Project Introduction",              "assignment": None,                        "due": None},
    {"week": 2,  "topic": "Software Development Processes",                        "assignment": None,                        "due": None},
    {"week": 3,  "topic": "Project Management and Agile Development",              "assignment": "Project Proposal",          "due": "2026-09-23"},
    {"week": 4,  "topic": "Version Control with Git",                              "assignment": "Lab 1: Git",                "due": "2026-09-30"},
    {"week": 5,  "topic": "Requirements Engineering",                              "assignment": "Lab 2: Specs",              "due": "2026-10-07"},
    {"week": 6,  "topic": "Specification-Driven Development with AI Coding Agents", "assignment": "Lab 3: Agents",            "due": "2026-10-14"},
    {"week": 7,  "topic": "AI-Assisted Code Review",                               "assignment": None,                        "due": None},
    {"week": 8,  "topic": "Software Testing Fundamentals",                         "assignment": "Lab 4: Testing",            "due": "2026-10-28"},
    {"week": 9,  "topic": "AI-Assisted Testing and Testing AI Systems",            "assignment": None,                        "due": None},
    {"week": 10, "topic": "Project Midterm Presentations",                         "assignment": "Project Midterm Presentation", "due": "2026-11-11"},
    {"week": 11, "topic": "Usability Evaluation and Heuristic Evaluation",         "assignment": "Project Milestone 1",       "due": "2026-11-18"},
    {"week": 12, "topic": "Software Design Patterns I",                            "assignment": None,                        "due": None},
    {"week": 13, "topic": "Software Design Patterns II",                           "assignment": "Lab 5: Design Patterns",    "due": "2026-12-02"},
    {"week": 14, "topic": "User Acceptance Testing, Deployment, and Release",      "assignment": "Lab 6: Deployment",         "due": "2026-12-09"},
    {"week": 15, "topic": "Project Final Presentations",                           "assignment": "Project Final Presentation", "due": "2026-12-16"},
]

# REAL - swpp_syllabus.pdf, section 3 ("Evaluation"). This course has no separate
# midterm/final exam line items - only these two components, and they sum to 100.
GRADING = {
    "Task": 70,
    "Random Evaluation": 30,
}

POLICIES = {
    # REAL - swpp_syllabus.pdf, section 3, "Attendance Policy".
    "attendance": (
        "Students who are absent for more than one-third (1/3) of class sessions "
        "receive a grade of F (or U) for the course, unless the instructor deems the "
        "cause of absence unavoidable. Up to 2 lecture absences and 1 lab-session "
        "absence are allowed for personal reasons without penalty; additional "
        "absences result in a grade penalty."
    ),
    # REAL - swpp_syllabus.pdf, section 4, "생성형 AI 도구 활용 방침" (Generative AI Tool
    # Usage Policy). Filed under academic_integrity, the closest existing tool
    # category to "how AI-assisted work must be disclosed."
    "academic_integrity": (
        "This course actively incorporates generative AI-based coding agents "
        "throughout the software development process. For every assignment and "
        "project, students must disclose which AI tools were used, describe how "
        "they were used, and identify which parts of the submission are "
        "AI-generated. Detailed guidelines on acceptable AI tool use and how it is "
        "evaluated are provided during the course. Submitting AI-generated work "
        "without this disclosure is treated as an academic-integrity violation."
    ),
    # PLACEHOLDER - the official syllabus specifies no late-submission percentage
    # policy at all.
    "late_submission": (
        "Assignments may be submitted up to 24 hours late for a 10% penalty, and up to "
        "48 hours late for a 30% penalty. After 48 hours the submission receives 0. "
        "Each student may request one penalty-free 24-hour extension per semester."
    ),
    # PLACEHOLDER - the official syllabus specifies no team size or registration
    # deadline.
    "team_formation": (
        "Teams for the project consist of 4 students. Teams must be registered on eTL by "
        "Friday of week 4. Students without a team are assigned by the TA. Changing teams "
        "mid-semester is not normally allowed."
    ),
    # PLACEHOLDER - the official syllabus lists no office hours (only a phone
    # number for the disability-support contact, which is not the same thing).
    "office_hours": (
        "Instructor office hours are Wednesdays 15:00-17:00 in room 302-426. "
        "TA office hours are Mondays 16:00-18:00 in room 302-311, by appointment."
    ),
}

POLICY_TOPICS = tuple(POLICIES.keys())
