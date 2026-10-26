"""
Main Flask Application for AI Children's Story Maker.
Coordinates routing, authentication-free beginner friendly local workflows,
responsible AI review checkpoints, and media generation.
"""

import os
import json
import logging
from pathlib import Path
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, send_file, abort, jsonify
)
from werkzeug.exceptions import RequestEntityTooLarge

from config import Config
from database.db import get_db, close_db, init_db
from models.story import StorybookModel, PageModel, FeedbackModel, PromptModel
from services.story_service import StoryService
from services.illustration_service import IllustrationService
from services.narration_service import NarrationService
from services.pdf_service import PDFService
from services.safety_service import SafetyService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    """Application factory for Flask."""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize DB and seed data
    with app.app_context():
        init_db()
        
    app.teardown_appcontext(close_db)
    
    # ---------------------------------------------------------
    # Route 1: Home Page
    # ---------------------------------------------------------
    @app.route("/")
    def index():
        storybooks = StorybookModel.get_all()
        # Find sample canonical story if available
        sample_story = None
        for s in storybooks:
            if s["title"] == "The Little Seed's Big Dream":
                sample_story = s
                break
        if not sample_story and storybooks:
            sample_story = storybooks[0]
            
        return render_template(
            "index.html",
            storybooks=storybooks,
            sample_story=sample_story
        )

    # ---------------------------------------------------------
    # Route 2: Story Creation Form & Action
    # ---------------------------------------------------------
    @app.route("/create", methods=["GET"])
    def create_story():
        return render_template("create_story.html")

    @app.route("/create/generate", methods=["POST"])
    def generate_story_action():
        form_data = {
            "title": request.form.get("title", "").strip(),
            "age_group": request.form.get("age_group", "6–9 years"),
            "theme": request.form.get("theme", "friendship"),
            "character_name": request.form.get("character_name", "").strip(),
            "character_desc": request.form.get("character_desc", "").strip(),
            "supporting_characters": request.form.get("supporting_characters", "").strip(),
            "story_length": int(request.form.get("story_length", 8)),
            "moral": request.form.get("moral", "").strip(),
            "language": request.form.get("language", "English"),
            "art_style": request.form.get("art_style", "Soft watercolor children's picture book illustration")
        }

        if not form_data["title"] or not form_data["character_name"]:
            flash("Please provide a story title and main character name.", "warning")
            return redirect(url_for("create_story"))

        try:
            # Generate structured story
            generated = StoryService.generate_story(form_data)
            storybook_id = StorybookModel.create(form_data, generated.get("pages", []))
            
            source_info = generated.get("generation_source", "Story Engine")
            flash(f"✨ Story draft created successfully using {source_info}! Review and edit each page below.", "success")
            return redirect(url_for("view_story", story_id=storybook_id, page=0))
        except Exception as e:
            logger.error(f"Error generating story: {e}")
            flash(f"Failed to generate story draft: {str(e)}", "danger")
            return redirect(url_for("create_story"))

    # ---------------------------------------------------------
    # Route 3: Storybook Viewer & Interactive Editor
    # ---------------------------------------------------------
    @app.route("/story/<int:story_id>")
    def view_story(story_id):
        storybook = StorybookModel.get_by_id(story_id)
        if not storybook:
            flash("Storybook not found.", "warning")
            return redirect(url_for("my_storybooks"))

        pages = PageModel.get_by_storybook(story_id)
        page_idx = int(request.args.get("page", 0))
        if page_idx < 0:
            page_idx = 0
        elif pages and page_idx >= len(pages):
            page_idx = len(pages) - 1

        feedbacks = FeedbackModel.get_by_storybook(story_id)

        return render_template(
            "editor.html",
            storybook=storybook,
            pages=pages,
            current_page_idx=page_idx,
            feedback_count=len(feedbacks)
        )

    @app.route("/page/<int:page_id>/save", methods=["POST"])
    def save_page_action(page_id):
        page = PageModel.get_by_id(page_id)
        if not page:
            abort(404)

        text = request.form.get("text", "").strip()
        prompt = request.form.get("illustration_prompt", "").strip()
        page_idx = request.form.get("page_idx", 0)

        PageModel.update_text_and_prompt(page_id, text, prompt)
        flash("Page edits saved successfully.", "success")
        return redirect(url_for("view_story", story_id=page["storybook_id"], page=page_idx))

    # ---------------------------------------------------------
    # Route 4: Illustration Management (AI Generate, Upload, Remove)
    # ---------------------------------------------------------
    @app.route("/page/<int:page_id>/generate_image", methods=["POST"])
    def generate_page_image_action(page_id):
        page = PageModel.get_by_id(page_id)
        if not page:
            abort(404)
        
        prompt = page["illustration_prompt"] or "Children's storybook illustration"
        page_idx = request.form.get("page_idx", 0)

        web_path, source = IllustrationService.generate_image_for_prompt(
            prompt=prompt,
            storybook_id=page["storybook_id"],
            page_number=page["page_number"]
        )

        if web_path:
            PageModel.update_image(page_id, web_path, source)
            flash(f"✨ Illustration generated successfully via {source}!", "success")
        else:
            flash(
                "Image generation service was unavailable or not configured. You can upload an illustration directly below!",
                "warning"
            )

        return redirect(url_for("view_story", story_id=page["storybook_id"], page=page_idx))

    @app.route("/page/<int:page_id>/upload_image", methods=["POST"])
    def upload_page_image_action(page_id):
        page = PageModel.get_by_id(page_id)
        if not page:
            abort(404)

        file = request.files.get("image_file")
        page_idx = request.form.get("page_idx", 0)

        try:
            web_path, source = IllustrationService.save_uploaded_image(
                file, page["storybook_id"], page["page_number"]
            )
            PageModel.update_image(page_id, web_path, source)
            flash("Image uploaded and validated successfully!", "success")
        except ValueError as ve:
            flash(str(ve), "danger")
        except Exception as e:
            flash(f"Failed to upload image: {str(e)}", "danger")

        return redirect(url_for("view_story", story_id=page["storybook_id"], page=page_idx))

    @app.route("/page/<int:page_id>/remove_image", methods=["POST"])
    def remove_page_image_action(page_id):
        page = PageModel.get_by_id(page_id)
        if not page:
            abort(404)

        page_idx = request.form.get("page_idx", 0)
        if page["image_path"]:
            IllustrationService.delete_image_file(page["image_path"])
            PageModel.update_image(page_id, "", "none")
            flash("Illustration removed from page.", "info")

        return redirect(url_for("view_story", story_id=page["storybook_id"], page=page_idx))

    # ---------------------------------------------------------
    # Route 5: Page Management (Add, Delete, Update Metadata)
    # ---------------------------------------------------------
    @app.route("/story/<int:story_id>/add_page", methods=["POST"])
    def add_page_action(story_id):
        storybook = StorybookModel.get_by_id(story_id)
        if not storybook:
            abort(404)

        PageModel.add_page(
            storybook_id=story_id,
            text=f"A new chapter unfolded in {storybook['character_name']}'s journey.",
            prompt=f"Children's book illustration of {storybook['character_name']} exploring happily."
        )
        pages = PageModel.get_by_storybook(story_id)
        flash("New page added to the storybook.", "success")
        return redirect(url_for("view_story", story_id=story_id, page=len(pages)-1))

    @app.route("/page/<int:page_id>/delete", methods=["POST"])
    def delete_page_action(page_id):
        page = PageModel.get_by_id(page_id)
        if not page:
            abort(404)
        storybook_id = page["storybook_id"]
        
        # Remove image file if any
        if page["image_path"]:
            IllustrationService.delete_image_file(page["image_path"])

        PageModel.delete_page(page_id)
        flash("Page deleted and remaining pages renumbered.", "info")
        return redirect(url_for("view_story", story_id=storybook_id, page=0))

    @app.route("/story/<int:story_id>/update_meta", methods=["POST"])
    def update_story_meta_action(story_id):
        storybook = StorybookModel.get_by_id(story_id)
        if not storybook:
            abort(404)

        title = request.form.get("title", storybook["title"]).strip()
        cover_title = request.form.get("cover_title", title).strip()
        moral = request.form.get("moral", storybook["moral"]).strip()
        
        StorybookModel.update_metadata(
            storybook_id=story_id,
            title=title,
            cover_title=cover_title,
            moral=moral,
            age_group=storybook["age_group"],
            theme=storybook["theme"]
        )
        flash("Storybook title and moral updated.", "success")
        return redirect(url_for("view_story", story_id=story_id))

    # ---------------------------------------------------------
    # Route 6: Narration Audio Generation (gTTS)
    # ---------------------------------------------------------
    @app.route("/story/<int:story_id>/narration", methods=["POST"])
    def generate_narration_action(story_id):
        storybook = StorybookModel.get_by_id(story_id)
        if not storybook:
            abort(404)

        pages = PageModel.get_by_storybook(story_id)
        try:
            audio_rel_path = NarrationService.generate_storybook_audio(
                storybook_id=story_id,
                title=storybook["title"],
                pages=pages,
                lang=storybook.get("language", "English")
            )
            StorybookModel.update_audio_path(story_id, audio_rel_path)
            flash("🎙️ Narration MP3 audio synthesized successfully! You can listen or download below.", "success")
        except Exception as e:
            logger.error(f"Narration generation error: {e}")
            flash(f"Audio generation notice: {str(e)}. You can also use the browser speech synthesis button on each page!", "warning")

        return redirect(url_for("view_story", story_id=story_id))

    # ---------------------------------------------------------
    # Route 7: PDF Export
    # ---------------------------------------------------------
    @app.route("/story/<int:story_id>/export_pdf")
    def export_pdf(story_id):
        storybook = StorybookModel.get_by_id(story_id)
        if not storybook:
            abort(404)

        pages = PageModel.get_by_storybook(story_id)
        try:
            pdf_rel_path = PDFService.generate_storybook_pdf(storybook, pages)
            abs_path = Config.STATIC_DIR / pdf_rel_path.replace("/", os.sep)
            
            clean_download_name = f"{storybook['title'].replace(' ', '_')}_PictureBook.pdf"
            return send_file(
                abs_path,
                as_attachment=True,
                download_name=clean_download_name,
                mimetype="application/pdf"
            )
        except Exception as e:
            logger.error(f"Error compiling PDF: {e}")
            flash(f"Could not generate PDF: {str(e)}", "danger")
            return redirect(url_for("view_story", story_id=story_id))

    # ---------------------------------------------------------
    # Route 8: Responsible AI & Safety Review
    # ---------------------------------------------------------
    @app.route("/story/<int:story_id>/safety", methods=["GET"])
    def safety_audit_page(story_id):
        storybook = StorybookModel.get_by_id(story_id)
        if not storybook:
            abort(404)
        pages = PageModel.get_by_storybook(story_id)

        # Run fresh rule-based audit
        report = SafetyService.audit_storybook(storybook, pages)
        return render_template("safety_review.html", storybook=storybook, report=report)

    @app.route("/story/<int:story_id>/safety", methods=["POST"])
    def update_safety_action(story_id):
        storybook = StorybookModel.get_by_id(story_id)
        if not storybook:
            abort(404)

        pages = PageModel.get_by_storybook(story_id)
        report = SafetyService.audit_storybook(storybook, pages)

        new_status = request.form.get("status", "Approved Safe")
        notes = request.form.get("notes", "").strip()
        report["human_reviewer_notes"] = notes
        report["human_review_status"] = new_status

        StorybookModel.update_safety(story_id, new_status, report)
        flash("Safety audit status and human review notes recorded.", "success")
        return redirect(url_for("safety_audit_page", story_id=story_id))

    # ---------------------------------------------------------
    # Route 9: Reader Feedback Module
    # ---------------------------------------------------------
    @app.route("/story/<int:story_id>/feedback", methods=["GET"])
    def feedback_page(story_id):
        storybook = StorybookModel.get_by_id(story_id)
        if not storybook:
            abort(404)
        feedbacks = FeedbackModel.get_by_storybook(story_id)
        return render_template("feedback.html", storybook=storybook, feedbacks=feedbacks)

    @app.route("/story/<int:story_id>/feedback", methods=["POST"])
    def add_feedback_action(story_id):
        storybook = StorybookModel.get_by_id(story_id)
        if not storybook:
            abort(404)

        data = {
            "reviewer_name": request.form.get("reviewer_name", "").strip(),
            "reviewer_type": request.form.get("reviewer_type", "Parent"),
            "readability_rating": int(request.form.get("readability_rating", 5)),
            "enjoyment_rating": int(request.form.get("enjoyment_rating", 5)),
            "comments": request.form.get("comments", "").strip(),
            "suggested_improvements": request.form.get("suggested_improvements", "").strip()
        }

        if not data["reviewer_name"] or not data["comments"]:
            flash("Please provide reviewer name and comments.", "warning")
            return redirect(url_for("feedback_page", story_id=story_id))

        FeedbackModel.add_feedback(story_id, data)
        flash("Thank you! Reader feedback saved.", "success")
        return redirect(url_for("feedback_page", story_id=story_id))

    # ---------------------------------------------------------
    # Route 10: Before-and-After Analysis
    # ---------------------------------------------------------
    @app.route("/story/<int:story_id>/analysis")
    def analysis_page(story_id):
        storybook = StorybookModel.get_by_id(story_id)
        if not storybook:
            abort(404)

        pages = PageModel.get_by_storybook(story_id)
        diff_data = SafetyService.compare_drafts(storybook.get("original_draft"), storybook, pages)
        return render_template("analysis.html", storybook=storybook, diff_data=diff_data)

    # ---------------------------------------------------------
    # Route 11: My Storybooks & Deletion
    # ---------------------------------------------------------
    @app.route("/storybooks")
    def my_storybooks():
        books = StorybookModel.get_all()
        return render_template("my_storybooks.html", storybooks=books)

    @app.route("/story/<int:story_id>/delete", methods=["POST"])
    def delete_story_action(story_id):
        storybook = StorybookModel.get_by_id(story_id)
        if storybook:
            # Delete any associated images and audio
            pages = PageModel.get_by_storybook(story_id)
            for p in pages:
                if p["image_path"]:
                    IllustrationService.delete_image_file(p["image_path"])
            if storybook["audio_path"]:
                IllustrationService.delete_image_file(storybook["audio_path"])

            StorybookModel.delete(story_id)
            flash(f"Storybook '{storybook['title']}' was deleted.", "info")
        return redirect(url_for("my_storybooks"))

    # ---------------------------------------------------------
    # Route 12: Prompt Library
    # ---------------------------------------------------------
    @app.route("/prompts")
    def prompt_library():
        prompts = PromptModel.get_all()
        return render_template("prompt_library.html", prompts=prompts)

    @app.route("/prompts/add", methods=["POST"])
    def add_prompt_action():
        category = request.form.get("category", "Story Generation")
        title = request.form.get("title", "").strip()
        prompt_text = request.form.get("prompt_text", "").strip()
        target_age = request.form.get("target_age", "All Ages").strip()
        notes = request.form.get("notes", "").strip()

        if not title or not prompt_text:
            flash("Please enter both a title and prompt text.", "warning")
            return redirect(url_for("prompt_library"))

        PromptModel.add(category, title, prompt_text, target_age, notes)
        flash("Custom prompt added to library.", "success")
        return redirect(url_for("prompt_library"))

    # ---------------------------------------------------------
    # Route 13: Live Demo & Responsible AI Blueprint
    # ---------------------------------------------------------
    @app.route("/demo")
    def demo_page():
        books = StorybookModel.get_all()
        sample_story = None
        for b in books:
            if b["title"] == "The Little Seed's Big Dream":
                sample_story = b
                break
        if not sample_story and books:
            sample_story = books[0]
            
        return render_template("demo.html", sample_story=sample_story)

    # ---------------------------------------------------------
    # Error Handlers
    # ---------------------------------------------------------
    @app.errorhandler(413)
    @app.errorhandler(RequestEntityTooLarge)
    def file_too_large(e):
        flash("Uploaded image is too large! Maximum allowed size is 5MB.", "danger")
        return redirect(request.referrer or url_for("my_storybooks")), 413

    @app.errorhandler(404)
    def not_found(e):
        return render_template("base.html", content="<div class='card' style='text-align:center; padding:3rem;'><h2>Page Not Found</h2><p>The requested story page could not be located.</p><a href='/' class='btn btn-primary' style='margin-top:1rem;'>Return Home</a></div>"), 404

    @app.errorhandler(500)
    def internal_error(e):
        logger.error(f"Internal error: {e}")
        return render_template("base.html", content="<div class='card' style='text-align:center; padding:3rem;'><h2>Something went wrong</h2><p>An unexpected error occurred. Please try again or return home.</p><a href='/' class='btn btn-primary' style='margin-top:1rem;'>Return Home</a></div>"), 500

    return app

# Development entry point
app = create_app()

if __name__ == "__main__":
    Config.ensure_directories()
    print("=" * 70)
    print("StorySprout AI - Responsible Children's Story Maker")
    print(f"Running at: http://127.0.0.1:{Config.PORT}")
    print("Child Safeguards & Human-in-the-Loop Engine Active")
    print("=" * 70)
    app.run(host="127.0.0.1", port=Config.PORT, debug=Config.DEBUG)
