"""
Database module for the AI Children's Story Application.
Provides SQLite connection management, table initialization, and initial seed data.
"""

import sqlite3
import json
from pathlib import Path
from flask import g
from config import Config

def get_db():
    """Returns a thread-safe connection to the SQLite database."""
    if 'db' not in g:
        Config.ensure_directories()
        g.db = sqlite3.connect(Config.DATABASE_PATH)
        g.db.row_factory = sqlite3.Row
        # Enable foreign key support in SQLite
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db

def close_db(e=None):
    """Closes the active database connection if open."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db(app=None):
    """Initializes the database schema and populates default prompts and sample story."""
    Config.ensure_directories()
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    
    schema_path = Path(__file__).resolve().parent / "schema.sql"
    with open(schema_path, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    
    # Populate default prompt library if empty
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM prompt_library")
    if cursor.fetchone()[0] == 0:
        seed_prompt_library(conn)
        
    # Populate sample story "The Little Seed's Big Dream" if empty
    cursor.execute("SELECT COUNT(*) as count FROM storybooks WHERE title = ?", ("The Little Seed's Big Dream",))
    if cursor.fetchone()[0] == 0:
        seed_sample_story(conn)
        
    conn.commit()
    conn.close()

def seed_prompt_library(conn):
    """Seeds recommended child-safe prompts into the library."""
    prompts = [
        (
            "Story Generation",
            "Kindness & Empathy Tale (Ages 3-5)",
            "Write a gentle 8-page picture book story for toddlers aged 3-5 about {character_name}, a {character_desc}. The theme is {theme}. Use simple rhyming or repetitive sentences, warm sensory words, and zero conflict or scary situations. End with a loving bedtime moral about helping friends.",
            "3–5 years",
            "Optimized for early readers and read-aloud bedtime sessions.",
            1
        ),
        (
            "Story Generation",
            "Curiosity & Nature Adventure (Ages 6-9)",
            "Create an inspiring 8-page adventure for children aged 6-9 starring {character_name}. Focus on the environment and curiosity. Give the character a relatable challenge (like fear of the dark or trying something new) that they overcome through teamwork and persistence with supporting friend {supporting_characters}. Conclude with an educational nature fact and clear moral.",
            "6–9 years",
            "Balances engaging plot pacing with accessible vocabulary.",
            1
        ),
        (
            "Illustration",
            "Storybook Page Watercolor Art Prompt",
            "Children's storybook illustration of {character_name}, {character_desc}, in a lush vibrant garden under soft morning sunlight, surrounded by friendly smiling insects and dewdrops, warm pastel colors, soft edges, whimsical storybook art style, clean composition, high contrast for easy reading, no frightening shadows.",
            "All Ages",
            "Ensures gentle visuals suitable for picture books.",
            1
        ),
        (
            "Character Consistency",
            "Visual Continuity Anchor",
            "Style and Character Consistency Anchor: [Character: {character_name}, wearing yellow overalls, round brown seed coat, big curious green eyes, tiny smiling mouth]. Render consistently across all panels in soft digital watercolor children's book illustration style.",
            "All Ages",
            "Prepended to all image generation queries to keep visual consistency.",
            1
        ),
        (
            "Safety Review",
            "Child Safeguard & Inclusion Audit",
            "Evaluate this children's story for readers aged {age_group}: 1) Are there any subtle frightening concepts or sudden danger? 2) Does the dialogue model respectful conflict resolution? 3) Are gender roles and cultural depictions fair and inclusive? 4) Is vocabulary accessible?",
            "All Ages",
            "Prompts human reviewers to rigorously audit generated stories.",
            1
        ),
        (
            "Revision",
            "Read-Aloud Rhythm & Rhyme Polishing",
            "Review each page of the following story and refine the rhythm for smooth spoken reading. Replace complex syllables with joyful, phonetically clear words suitable for {age_group}.",
            "All Ages",
            "Improves auditory flow for parent and teacher read-alouds.",
            1
        )
    ]
    conn.executemany(
        """
        INSERT INTO prompt_library (category, title, prompt_text, target_age, notes, is_built_in)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        prompts
    )

def seed_sample_story(conn):
    """Seeds the canonical sample story 'The Little Seed's Big Dream'."""
    sample_pages = [
        {
            "page_number": 1,
            "text": "Deep beneath the soft, warm brown earth rested Pip, a tiny acorn seed with big sparkling dreams.",
            "illustration_prompt": "Children's storybook watercolor of Pip, a tiny smiling brown acorn seed nestled snugly in dark crumbly soil with gentle golden sunbeams filtering down."
        },
        {
            "page_number": 2,
            "text": "Every morning, friendly Bella the Butterfly fluttered by to whisper stories of the wide sky and dancing clouds.",
            "illustration_prompt": "Pip the tiny seed listening happily underground as a colorful yellow butterfly with translucent wings rests on a green blade of grass above."
        },
        {
            "page_number": 3,
            "text": "\"Can a seed as small as me ever touch the clouds?\" Pip asked softly. \"Patience, little one,\" whispered Mother Earth.",
            "illustration_prompt": "Pip the little brown acorn seed looking up with wonder, gentle raindrops soaking into the soil providing sparkling nourishment."
        },
        {
            "page_number": 4,
            "text": "Soon, a cool sip of spring rainwater trickled down, tickling Pip's shell until—POP! A tiny emerald sprout emerged.",
            "illustration_prompt": "A tiny bright green shoot bursting happily from Pip the acorn seed, reaching upwards toward the warm golden daylight."
        },
        {
            "page_number": 5,
            "text": "Pip pushed through the soil and blinked in the bright, cheerful sunshine. \"Hello, wonderful world!\" cheered Pip.",
            "illustration_prompt": "Pip as a fresh two-leaf seedling smiling in a meadow of soft pink daisies and green clover under a bright blue morning sky."
        },
        {
            "page_number": 6,
            "text": "Days turned into weeks. Gentle sunbeams and cool summer showers helped Pip grow taller and stronger every day.",
            "illustration_prompt": "Pip growing into a sturdy young oak sapling with bright green leaves, a friendly bluebird perched gently on one branch."
        },
        {
            "page_number": 7,
            "text": "Years rolled by, and Pip became a grand, sheltering oak tree with wide leafy branches offering cool shade to all forest friends.",
            "illustration_prompt": "A magnificent tall green oak tree with friendly eyes carved gently in the trunk, forest animals resting peacefully under its wide protective branches."
        },
        {
            "page_number": 8,
            "text": "Pip smiled at the dancing clouds above, knowing that with patience, kindness, and time, the smallest seed can grow into the greatest dream.",
            "illustration_prompt": "Golden sunset illuminating Pip the grand oak tree, leaves fluttering like emerald gold, butterflies fluttering peacefully around the canopy."
        }
    ]
    
    original_draft_json = json.dumps({
        "title": "The Little Seed's Big Dream",
        "age_group": "6–9 years",
        "theme": "environment",
        "pages": sample_pages,
        "moral": "Patience, care, and perseverance can turn the smallest beginning into something magnificent."
    })
    
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO storybooks (
            title, cover_title, age_group, theme, character_name, character_desc,
            supporting_characters, story_length, moral, language, art_style,
            original_draft, safety_status, safety_report
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "The Little Seed's Big Dream",
            "The Little Seed's Big Dream",
            "6–9 years",
            "environment",
            "Pip the Acorn",
            "A tiny curious brown acorn seed with big expressive eyes and a heart full of wonder",
            "Bella the Butterfly and Mother Earth",
            8,
            "Patience, care, and perseverance can turn the smallest beginning into something magnificent.",
            "English",
            "Soft watercolor children's picture book illustration, pastel tones, friendly expressive characters",
            original_draft_json,
            "Approved Safe",
            json.dumps({
                "overall_status": "Approved Safe",
                "score": 100,
                "flags": [],
                "verified_by_human": True,
                "notes": "Verified child-safe educational content about plant growth, patience, and nature."
            })
        )
    )
    storybook_id = cursor.lastrowid
    
    for page in sample_pages:
        cursor.execute(
            """
            INSERT INTO pages (storybook_id, page_number, text, illustration_prompt, image_path, image_source)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                storybook_id,
                page["page_number"],
                page["text"],
                page["illustration_prompt"],
                "", # Image paths start clean or can be generated/uploaded
                "none"
            )
        )
        
    # Seed a sample reader feedback
    cursor.execute(
        """
        INSERT INTO feedback (storybook_id, reviewer_name, reviewer_type, readability_rating, enjoyment_rating, comments, suggested_improvements)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            storybook_id,
            "Elena Miller (Elementary Teacher)",
            "Teacher",
            5,
            5,
            "A heartwarming and scientifically accurate metaphor for plant growth and emotional resilience. My 2nd grade class loved it!",
            "Consider adding an interactive activity prompt on page 8, like 'Draw your own dream tree'."
        )
    )
