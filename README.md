# 🌱 StorySprout AI: Illustrated Children's Storybook Creator

> **Capstone Project Question:** *How can AI help create a short illustrated children's story responsibly?*

---

## 🌟 Executive Summary & Project Purpose

**StorySprout AI** is a full-stack web application built with **Python Flask**, **SQLite**, and **ReportLab**. It enables educators, parents, and young authors to co-create beautifully structured, age-appropriate children's picture books using Artificial Intelligence **responsibly**.

Rather than treating AI as an unchecked generator, StorySprout adopts a **Human-in-the-Loop Co-Creation Model**:
1. **Generative Assistance:** AI drafts structured 8–10 page stories with positive morals, consistent character anchors, and age-adapted vocabulary.
2. **Deterministic Safeguards:** An automated 8-point safety audit screens for scary words, violence, bullying, PII, and reading ease before any child reads the story.
3. **Transparent Curation:** Every page can be edited, illustrations can be replaced or manually uploaded, and exported PDFs clearly disclose AI usage.
4. **Zero Cost / Offline Readiness:** The application runs locally out of the box with zero paid API keys required.

---

## 📁 Project Directory Structure

```text
ai_childrens_story/
│
├── .env                         # Local runtime environment settings
├── .env.example                 # Template for configuration & optional API keys
├── .gitignore                   # Ignores venv, database files, and uploaded media
├── app.py                       # Main Flask web application & HTTP route controllers
├── config.py                    # Centralized settings, file limits, and directories
├── requirements.txt             # Python dependencies (Flask, ReportLab, Pillow, gTTS, pytest)
├── README.md                    # Comprehensive documentation and mentor guide
│
├── database/
│   ├── __init__.py
│   ├── db.py                    # SQLite connection management and seed scripts
│   └── schema.sql               # Relational tables: storybooks, pages, feedback, prompts
│
├── models/
│   ├── __init__.py
│   └── story.py                 # Query wrappers: StorybookModel, PageModel, FeedbackModel, PromptModel
│
├── services/
│   ├── __init__.py
│   ├── story_service.py         # Multi-provider LLM (Gemini, OpenAI) + built-in responsible generator
│   ├── illustration_service.py  # Image generator (Pollinations AI, DALL-E) + secure Pillow uploads
│   ├── narration_service.py     # Server-side MP3 generation (gTTS) & browser synthesis status
│   ├── pdf_service.py           # ReportLab publication engine with cover, margins & disclosures
│   └── safety_service.py        # 8-point rule-based safety auditor & before/after diff engine
│
├── templates/
│   ├── base.html                # Picture-book pastel layout, accessibility, and navigation
│   ├── index.html               # Home page with feature showcase & canonical sample story
│   ├── create_story.html        # Story creation form with 1-click sample pre-fill
│   ├── editor.html              # Interactive page reader/editor with live speech & uploads
│   ├── my_storybooks.html       # SQLite library of all saved picture books
│   ├── prompt_library.html      # Categorized prompt library with 1-click copy & customize
│   ├── safety_review.html       # 8-point child safety checklist and human sign-off form
│   ├── feedback.html            # Test reader feedback logger (ratings, comments, improvements)
│   ├── analysis.html            # Side-by-side Before-and-After editorial diff comparison
│   └── demo.html                # Live demonstration page, architecture & ethical limitations
│
├── static/
│   ├── css/
│   │   └── style.css            # Soft pastel picture-book design system & accessible contrast
│   ├── js/
│   │   └── app.js               # Web Speech API, live word counting, image preview & prompt copy
│   ├── images/
│   │   ├── uploads/             # Secure directory for user-uploaded illustrations
│   │   └── generated/           # Directory for AI-generated illustrations
│   ├── audio/                   # Directory for synthesized MP3 narrations
│   └── pdf/                     # Directory for compiled print-ready PDFs
│
└── tests/
    ├── __init__.py
    ├── test_app.py              # Integration tests for routes, forms, uploads, and views
    └── test_services.py         # Unit tests for story generator, safety checks, diffs, and PDF
```

---

## 💻 Tech Stack & Architecture Overview

| Layer | Technology | Role & Fallback Strategy |
| :--- | :--- | :--- |
| **Backend Framework** | Python 3.10+ / Flask | Light, beginner-friendly web server with explicit routing |
| **Database** | SQLite3 | Local serverless relational storage with foreign keys |
| **Templating** | Jinja2 | Clean HTML rendering with responsive picture-book styling |
| **Story Generation** | Gemini / OpenAI REST APIs | **Offline Fallback:** Built-in template narrative engine |
| **Illustration Gen** | Pollinations.ai / DALL-E | **Zero-Cost Fallback:** Manual Pillow-verified file upload |
| **Narration** | gTTS (Server MP3) | **Client Fallback:** Web Speech API (Browser Synthesis) |
| **PDF Publishing** | ReportLab Platypus | Dynamic 2-pass page numbering, flowables, aspect scaling |
| **Testing** | Pytest | 15 unit and integration test assertions |

---

## 🚀 Beginner-Friendly Quick Start Guide (Windows & VS Code)

### Step 1: Open the Workspace in VS Code
1. Launch **Visual Studio Code**.
2. Select **File > Open Folder...** and select `d:\antigravity\ai_childrens_story` (or `d:\antigravity`).
3. Open the integrated terminal using <kbd>Ctrl</kbd> + <kbd>`</kbd> (or **Terminal > New Terminal**).

### Step 2: Set Up Virtual Environment & Dependencies
In PowerShell:
```powershell
# 1. Create a Python virtual environment (if not already present)
python -m venv venv

# 2. Activate the virtual environment
.\venv\Scripts\Activate.ps1
# (If script execution is blocked: Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass)

# 3. Upgrade pip and install dependencies
pip install -r requirements.txt
```

### Step 3: Run the Application
```powershell
python app.py
```
Open your browser and navigate to:
```text
http://127.0.0.1:5000
```

---

## 🔑 Configuring Optional AI API Keys

StorySprout AI operates **completely free without any API keys** using its built-in story generator, manual image uploads, and browser speech synthesis.

If you wish to connect external AI services:
1. Open the `.env` file in the project root.
2. Add your keys:
   ```env
   # Google Gemini API Key (optional):
   # Get free API key from: https://aistudio.google.com/
   GEMINI_API_KEY=your_gemini_api_key_here

   # OpenAI API Key (optional):
   # Get from: https://platform.openai.com/
   OPENAI_API_KEY=your_openai_api_key_here

   # Hugging Face Token (optional):
   # Get from: https://huggingface.co/settings/tokens
   HF_TOKEN=your_huggingface_token_here

   # Pollinations AI (Enabled by default, free tier, no API key required)
   POLLINATIONS_ENABLED=true
   ```
3. Save the file and restart `python app.py`. The application will automatically detect your configured services.

---

## 📖 Canonical Sample Story: *"The Little Seed's Big Dream"*

To help beginners and reviewers inspect the system immediately upon launch, the SQLite database is automatically seeded with the complete canonical story:

- **Protagonist:** Pip the Acorn (*"A tiny curious brown acorn seed with big sparkling eyes and a soft cap"*)
- **Supporting Characters:** Bella the Butterfly and Mother Earth
- **Target Age:** 6–9 years
- **Theme:** Environment & Patience
- **Moral:** *"Patience, care, and perseverance can turn the smallest beginning into something magnificent."*
- **Structure (8 Pages):**
  1. *Underground Wonder:* Pip rests in warm soil, dreaming of touching the clouds.
  2. *The Butterfly's Visit:* Bella shares stories of dancing clouds and blue skies.
  3. *Mother Earth's Advice:* Mother Earth whispers that patience and sunshine will guide the way.
  4. *The Spring Rain:* A cool raindrop tickles Pip's shell until a green shoot pops out.
  5. *Emerging to Light:* Pip pushes through the soil and greets the sunny meadow.
  6. *Growing Stronger:* Days of sunlight and rain turn Pip into a sturdy sapling.
  7. *The Grand Shelter:* Years pass and Pip becomes a towering oak offering shade to forest creatures.
  8. *Dream Achieved:* Pip touches the clouds and shelters forest friends with love.

---

## 🧪 Testing Every Major Feature (Step-by-Step Walkthrough)

### 1. Test Home Page & Story Creation
1. Go to `http://127.0.0.1:5000/`.
2. Click **✨ Create a New Storybook**.
3. Click the green button **🌱 Load "Little Seed" Preset** to automatically prefill the form.
4. Click **✨ Generate Story Draft**. The story engine will structure 8 pages and redirect to the **Storybook Editor**.

### 2. Test Storybook Editor & Live Browser Speech
1. In the editor, browse through pages using **Previous Page** and **Next Page** or the page pills (`p. 1`, `p. 2`, etc.).
2. Click **🔊 Read This Page Aloud**. Your browser's Web Speech API will synthesize soothing, child-friendly audio.
3. Edit the story text in the textarea and click **💾 Save Page Edits**.

### 3. Test Illustration Generation & Upload Fallback
1. Click **✨ Generate AI Image** on any page to fetch an illustration via Pollinations AI.
2. Click **📤 Upload Own Image**, choose any local PNG/JPG image (<5MB), and submit. The file is validated by Pillow and embedded beside the text.
3. Notice the **Provenance Badge**: it honestly labels the image as `🎨 AI Generated` or `🖼️ User Uploaded`.

### 4. Test Responsible AI & Safety Review
1. In the top bar, click **🛡️ Safety Review**.
2. Inspect the **8-Point Safety Checklist**:
   - Age appropriateness and sentence length limits
   - Violence and frightening content detection
   - Bullying and discrimination detection
   - PII protection (phone, email, street address checks)
   - Readability metrics (word counts, Flesch Reading Ease score)
   - Cultural sensitivity checks
   - Character visual consistency continuity
   - Accuracy of educational and botanical claims
3. Choose a status decision (e.g. *Approved Child-Safe*), add editorial notes, and save.

### 5. Test Before-and-After Editorial Diff
1. In the top bar, click **⚖️ Before & After**.
2. View the side-by-side comparison between the original generated draft and your revised version.
3. Observe the metric cards tracking genuine word count differences and modified pages without fabrication.

### 6. Test Reader Feedback Module
1. In the top bar, click **💬 Feedback**.
2. Submit a review from a test reader (Parent, Child, or Teacher) with 1–5 star ratings and comments.
3. Verify that the review appears cleanly in the feedback list.

### 7. Test PDF Export
1. In the editor or home page, click **📄 Export PDF**.
2. A print-ready PDF is compiled on-the-fly with ReportLab, featuring:
   - Full cover page with badges and age group
   - Scaled illustrations with preserved aspect ratio
   - Missing image graceful fallback frames
   - Moral highlight box
   - Transparent Responsible AI disclosure & author credits

---

## 🔬 Automated Testing Suite

Execute the 15-test automated test suite using pytest:
```powershell
pytest tests -v
```
**Test Coverage:**
- `test_home_page_loads`: Confirms home page routing and branding.
- `test_create_page_loads`: Validates story input form controls.
- `test_generate_story_creates_record`: Verifies story drafting and SQLite storage.
- `test_story_editor_and_page_save`: Checks human editorial persistence.
- `test_safety_audit_page`: Tests the 8-point checklist rendering.
- `test_pdf_export_route`: Asserts valid PDF content-type and payload size.
- `test_feedback_submission`: Verifies reader evaluation persistence.
- `test_prompt_library_page`: Tests prompt categorization and retrieval.
- `test_demo_page`: Asserts architectural showcase page.
- `test_story_generation_builtin`: Verifies zero-key offline narrative generation.
- `test_safety_audit_safe_content`: Confirms high score for positive children's literature.
- `test_safety_audit_flags_inappropriate_words`: Asserts scary/violent keyword detection.
- `test_safety_audit_flags_pii`: Asserts regex detection of telephone and email leaks.
- `test_before_after_draft_comparison`: Verifies genuine textual diff tracking.
- `test_pdf_generation_creates_valid_file`: Validates ReportLab PDF binary creation.

---

## 🛡️ Responsible AI Practices & Ethical Disclaimers

### Core Ethical Guidelines:
1. **Human-in-the-Loop Necessity:** Automated filters provide an assistive first-pass check. They **never replace human judgment**. Parents, teachers, or authors must always review content before sharing with children.
2. **Zero Frightening Tropes:** Story templates and prompts strictly prohibit weapons, blood, gore, nightmare imagery, and sudden scary turns.
3. **Transparent Provenance:** Exported PDFs and editor badges explicitly disclose what was generated by AI versus what was created or edited by humans.
4. **Child Privacy First:** The system never asks for or stores children's personal contact information or photos.

---

## 📋 CAPSTONE 54 Requirements Verification Checklist

| # | Capstone Requirement | Status | Verification in StorySprout AI |
| :---: | :--- | :---: | :--- |
| **1** | **Home Page** | ✅ Complete | Child-friendly pastel hero, quick buttons (Create, Saved, About), responsive design. |
| **2** | **Story Creation** | ✅ Complete | Form for age group (3-5, 6-9, 10-12), theme, character, length (8-10), moral, language, prefill button. |
| **3** | **AI Illustration Management** | ✅ Complete | Visual prompts with character anchors, Pollinations/DALL-E integration, manual upload fallback, Pillow validation. |
| **4** | **Storybook Editor** | ✅ Complete | Page text editor, add/delete/reorder pages, previous/next navigation, word count, live preview. |
| **5** | **Narration** | ✅ Complete | In-browser Web Speech API fallback, gTTS server MP3 generation, download button, distinct UI badges. |
| **6** | **PDF Export** | ✅ Complete | ReportLab export with cover page, age group, scaled illustrations, moral box, and AI disclosure. |
| **7** | **Prompt Library** | ✅ Complete | Categorized library (Story, Illustration, Consistency, Safety, Revision), 1-click copy, custom prompt creation. |
| **8** | **Responsible AI & Safety Review**| ✅ Complete | 8-point checklist (age, violence, bullying, PII, readability, culture, character, education), disclaimer, audit record. |
| **9** | **Feedback Module** | ✅ Complete | Reviewer type, readability & enjoyment ratings, comments, SQLite persistence, no fabricated results. |
| **10** | **Before-and-After Analysis** | ✅ Complete | Stores initial AI draft, compares side-by-side with human revision, metric cards, real textual diffs. |
| **11** | **My Storybooks** | ✅ Complete | SQLite CRUD, list view with status badges, reopen editor, delete storybook after confirmation. |
| **12** | **Final Demo Page** | ✅ Complete | Dedicated demo route (`/demo`) detailing research question, architecture, workflow, sample story, and limitations. |
