"""
Data access models for Storybooks, Pages, Feedback, and Prompts.
Provides clear, encapsulated database query methods.
"""

import json
from database.db import get_db

class StorybookModel:
    @staticmethod
    def get_all():
        """Retrieve all storybooks ordered by creation date descending."""
        db = get_db()
        cursor = db.execute(
            """
            SELECT s.*, 
                   COUNT(p.id) as page_count,
                   (SELECT COUNT(*) FROM feedback f WHERE f.storybook_id = s.id) as feedback_count
            FROM storybooks s
            LEFT JOIN pages p ON p.storybook_id = s.id
            GROUP BY s.id
            ORDER BY s.created_at DESC
            """
        )
        return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_by_id(storybook_id):
        """Retrieve a single storybook by its ID."""
        db = get_db()
        cursor = db.execute(
            "SELECT * FROM storybooks WHERE id = ?", (storybook_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    @staticmethod
    def create(data, pages):
        """Creates a new storybook along with its pages and original draft snapshot."""
        db = get_db()
        cursor = db.cursor()
        
        # Prepare original draft snapshot for before/after comparison
        original_draft_dict = {
            "title": data.get("title"),
            "age_group": data.get("age_group"),
            "theme": data.get("theme"),
            "moral": data.get("moral"),
            "pages": pages
        }
        
        cursor.execute(
            """
            INSERT INTO storybooks (
                title, cover_title, age_group, theme, character_name, character_desc,
                supporting_characters, story_length, moral, language, art_style,
                original_draft, safety_status, safety_report
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data.get("title"),
                data.get("cover_title") or data.get("title"),
                data.get("age_group"),
                data.get("theme"),
                data.get("character_name"),
                data.get("character_desc"),
                data.get("supporting_characters"),
                len(pages),
                data.get("moral"),
                data.get("language", "English"),
                data.get("art_style", "Soft watercolor children's book illustration"),
                json.dumps(original_draft_dict),
                "Pending Review",
                json.dumps({"overall_status": "Pending Review", "flags": []})
            )
        )
        storybook_id = cursor.lastrowid
        
        # Insert pages
        for idx, page in enumerate(pages, start=1):
            cursor.execute(
                """
                INSERT INTO pages (
                    storybook_id, page_number, text, illustration_prompt, image_path, image_source
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    storybook_id,
                    idx,
                    page.get("text", "").strip(),
                    page.get("illustration_prompt", "").strip(),
                    page.get("image_path", ""),
                    page.get("image_source", "none")
                )
            )
            
        db.commit()
        return storybook_id

    @staticmethod
    def update_metadata(storybook_id, title, cover_title, moral, age_group, theme):
        """Update top-level storybook fields."""
        db = get_db()
        db.execute(
            """
            UPDATE storybooks
            SET title = ?, cover_title = ?, moral = ?, age_group = ?, theme = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (title, cover_title, moral, age_group, theme, storybook_id)
        )
        db.commit()

    @staticmethod
    def update_safety(storybook_id, status, report_dict):
        """Save responsible AI audit results."""
        db = get_db()
        db.execute(
            """
            UPDATE storybooks
            SET safety_status = ?, safety_report = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (status, json.dumps(report_dict), storybook_id)
        )
        db.commit()

    @staticmethod
    def update_audio_path(storybook_id, audio_path):
        """Save generated narration audio file path."""
        db = get_db()
        db.execute(
            "UPDATE storybooks SET audio_path = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (audio_path, storybook_id)
        )
        db.commit()

    @staticmethod
    def delete(storybook_id):
        """Deletes a storybook and all cascaded pages and feedback."""
        db = get_db()
        db.execute("DELETE FROM storybooks WHERE id = ?", (storybook_id,))
        db.commit()


class PageModel:
    @staticmethod
    def get_by_storybook(storybook_id):
        """Retrieve all pages of a storybook ordered by page number."""
        db = get_db()
        cursor = db.execute(
            "SELECT * FROM pages WHERE storybook_id = ? ORDER BY page_number ASC",
            (storybook_id,)
        )
        return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_by_id(page_id):
        """Retrieve a single page by ID."""
        db = get_db()
        cursor = db.execute("SELECT * FROM pages WHERE id = ?", (page_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    @staticmethod
    def update_text_and_prompt(page_id, text, illustration_prompt):
        """Update the page text and prompt."""
        db = get_db()
        db.execute(
            """
            UPDATE pages
            SET text = ?, illustration_prompt = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (text, illustration_prompt, page_id)
        )
        db.commit()

    @staticmethod
    def update_image(page_id, image_path, image_source):
        """Update image path and provenance source."""
        db = get_db()
        db.execute(
            """
            UPDATE pages
            SET image_path = ?, image_source = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (image_path, image_source, page_id)
        )
        db.commit()

    @staticmethod
    def add_page(storybook_id, text="", prompt=""):
        """Add a new page at the end of the storybook."""
        db = get_db()
        cursor = db.execute(
            "SELECT COALESCE(MAX(page_number), 0) + 1 FROM pages WHERE storybook_id = ?",
            (storybook_id,)
        )
        next_num = cursor.fetchone()[0]
        db.execute(
            """
            INSERT INTO pages (storybook_id, page_number, text, illustration_prompt)
            VALUES (?, ?, ?, ?)
            """,
            (storybook_id, next_num, text, prompt)
        )
        db.commit()

    @staticmethod
    def delete_page(page_id):
        """Delete a page and renumber remaining pages consecutively."""
        db = get_db()
        cursor = db.execute("SELECT storybook_id FROM pages WHERE id = ?", (page_id,))
        row = cursor.fetchone()
        if not row:
            return
        storybook_id = row["storybook_id"]
        
        db.execute("DELETE FROM pages WHERE id = ?", (page_id,))
        
        # Renumber remaining pages
        pages = db.execute(
            "SELECT id FROM pages WHERE storybook_id = ? ORDER BY page_number ASC",
            (storybook_id,)
        ).fetchall()
        
        for idx, p in enumerate(pages, start=1):
            db.execute("UPDATE pages SET page_number = ? WHERE id = ?", (idx, p["id"]))
            
        db.commit()

    @staticmethod
    def reorder_pages(storybook_id, page_ids_order):
        """Reorder pages according to a list of page IDs."""
        db = get_db()
        for new_idx, pid in enumerate(page_ids_order, start=1):
            db.execute(
                "UPDATE pages SET page_number = ? WHERE id = ? AND storybook_id = ?",
                (new_idx, pid, storybook_id)
            )
        db.commit()


class FeedbackModel:
    @staticmethod
    def get_by_storybook(storybook_id):
        """Get all feedback for a storybook."""
        db = get_db()
        cursor = db.execute(
            "SELECT * FROM feedback WHERE storybook_id = ? ORDER BY created_at DESC",
            (storybook_id,)
        )
        return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def add_feedback(storybook_id, data):
        """Add reviewer feedback."""
        db = get_db()
        db.execute(
            """
            INSERT INTO feedback (
                storybook_id, reviewer_name, reviewer_type, readability_rating,
                enjoyment_rating, comments, suggested_improvements
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                storybook_id,
                data.get("reviewer_name"),
                data.get("reviewer_type"),
                int(data.get("readability_rating", 5)),
                int(data.get("enjoyment_rating", 5)),
                data.get("comments", "").strip(),
                data.get("suggested_improvements", "").strip()
            )
        )
        db.commit()


class PromptModel:
    @staticmethod
    def get_all():
        """Retrieve all prompt library entries."""
        db = get_db()
        cursor = db.execute(
            "SELECT * FROM prompt_library ORDER BY category ASC, id ASC"
        )
        return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def add(category, title, prompt_text, target_age, notes):
        """Add a custom prompt to the library."""
        db = get_db()
        db.execute(
            """
            INSERT INTO prompt_library (category, title, prompt_text, target_age, notes, is_built_in)
            VALUES (?, ?, ?, ?, ?, 0)
            """,
            (category, title, prompt_text, target_age, notes)
        )
        db.commit()
