-- SQLite Schema for AI Children's Story Application

CREATE TABLE IF NOT EXISTS storybooks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    cover_title TEXT,
    age_group TEXT NOT NULL,
    theme TEXT NOT NULL,
    character_name TEXT NOT NULL,
    character_desc TEXT,
    supporting_characters TEXT,
    story_length INTEGER DEFAULT 8,
    moral TEXT,
    language TEXT DEFAULT 'English',
    art_style TEXT DEFAULT 'Vibrant watercolor children picture book illustration, soft lighting, friendly characters',
    original_draft TEXT, -- JSON snapshot of first generated version for Before/After analysis
    safety_status TEXT DEFAULT 'Pending Review', -- Pending Review, Safe, Needs Revision
    safety_report TEXT, -- JSON output of automated & manual safety checks
    audio_path TEXT DEFAULT '', -- Path to synthesized server-side audio file
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    storybook_id INTEGER NOT NULL,
    page_number INTEGER NOT NULL,
    text TEXT NOT NULL,
    illustration_prompt TEXT,
    image_path TEXT DEFAULT '',
    image_source TEXT DEFAULT 'none', -- 'ai_pollinations', 'ai_openai', 'uploaded', 'none'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (storybook_id) REFERENCES storybooks (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    storybook_id INTEGER NOT NULL,
    reviewer_name TEXT NOT NULL,
    reviewer_type TEXT NOT NULL, -- 'Child (3-5)', 'Child (6-9)', 'Child (10-12)', 'Parent', 'Teacher', 'Educator'
    readability_rating INTEGER NOT NULL CHECK(readability_rating BETWEEN 1 AND 5),
    enjoyment_rating INTEGER NOT NULL CHECK(enjoyment_rating BETWEEN 1 AND 5),
    comments TEXT NOT NULL,
    suggested_improvements TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (storybook_id) REFERENCES storybooks (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS prompt_library (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL, -- 'Story Generation', 'Illustration', 'Character Consistency', 'Safety Review', 'Revision'
    title TEXT NOT NULL,
    prompt_text TEXT NOT NULL,
    target_age TEXT DEFAULT 'All Ages',
    notes TEXT,
    is_built_in INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pages_storybook ON pages(storybook_id, page_number);
CREATE INDEX IF NOT EXISTS idx_feedback_storybook ON feedback(storybook_id);
