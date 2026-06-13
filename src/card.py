"""
UFC Freedom 250 (UFC White House) card definition.

Corner order (red first) and tale-of-the-tape physicals are taken from the
ufcstats matchup pages. Physicals are provided here because several of these
fighters are missing reach/height in the bulk fighter-details file.
"""
EVENT = {
    "name": "UFC Freedom 250",
    "subtitle": "UFC White House",
    "date": "2026-06-14",
    "venue": "South Lawn, The White House",
    "city": "Washington, D.C.",
}

# height/reach in inches, stance, dob (YYYY-MM-DD)
PHYS = {
    "ILIA TOPURIA":   (67, 69, "Orthodox", "1997-01-21"),
    "JUSTIN GAETHJE": (71, 70, "Orthodox", "1988-11-14"),
    "ALEX PEREIRA":   (76, 79, "Orthodox", "1987-07-07"),
    "CIRYL GANE":     (76, 81, "Orthodox", "1990-04-12"),
    "SEAN O'MALLEY":  (71, 72, "Switch",   "1994-10-24"),
    "AIEMANN ZAHABI": (68, 68, "Orthodox", "1987-11-19"),
    "JOSH HOKIT":     (73, 73, "Orthodox", "1997-11-12"),
    "DERRICK LEWIS":  (75, 79, "Orthodox", "1985-02-07"),
    "MAURICIO RUFFY": (71, 75, "Orthodox", "1996-06-17"),
    "MICHAEL CHANDLER": (68, 71, "Orthodox", "1986-04-24"),
    "BO NICKAL":      (73, 76, "Southpaw", "1996-01-14"),
    "KYLE DAUKAUS":   (74, 76, "Southpaw", "1993-02-27"),
    "DIEGO LOPES":    (71, 72, "Orthodox", "1994-12-30"),
    "STEVE GARCIA":   (72, 75, "Southpaw", "1992-05-22"),
}

# (red, blue, weight_class, scheduled_rounds, billing, title)
FIGHTS = [
    ("ILIA TOPURIA",  "JUSTIN GAETHJE",   "Lightweight",  5, "Main Event",   "UFC Lightweight Title"),
    ("ALEX PEREIRA",  "CIRYL GANE",       "Heavyweight",  5, "Co-Main",      "Interim UFC Heavyweight Title"),
    ("SEAN O'MALLEY", "AIEMANN ZAHABI",   "Bantamweight", 3, "Featured",     None),
    ("JOSH HOKIT",    "DERRICK LEWIS",    "Heavyweight",  3, "Featured",     None),
    ("MAURICIO RUFFY", "MICHAEL CHANDLER", "Lightweight", 3, "Featured",     None),
    ("BO NICKAL",     "KYLE DAUKAUS",     "Middleweight", 3, "Featured",     None),
    ("DIEGO LOPES",   "STEVE GARCIA",     "Featherweight", 3, "Featured",    None),
]

# display names (proper casing) for the frontend
DISPLAY = {
    "ILIA TOPURIA": "Ilia Topuria", "JUSTIN GAETHJE": "Justin Gaethje",
    "ALEX PEREIRA": "Alex Pereira", "CIRYL GANE": "Ciryl Gane",
    "SEAN O'MALLEY": "Sean O'Malley", "AIEMANN ZAHABI": "Aiemann Zahabi",
    "JOSH HOKIT": "Josh Hokit", "DERRICK LEWIS": "Derrick Lewis",
    "MAURICIO RUFFY": "Maurício Ruffy", "MICHAEL CHANDLER": "Michael Chandler",
    "BO NICKAL": "Bo Nickal", "KYLE DAUKAUS": "Kyle Daukaus",
    "DIEGO LOPES": "Diego Lopes", "STEVE GARCIA": "Steve Garcia",
}
