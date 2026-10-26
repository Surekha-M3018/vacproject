"""
Responsible AI & Safety Review Service.
Performs rule-based checks across 8 critical dimensions for children's literature:
1. Age appropriateness & sentence complexity
2. Violence and frightening content
3. Bullying and discrimination
4. Privacy and personal identifiable information (PII)
5. Grammar and readability metrics (Flesch Reading Ease)
6. Cultural sensitivity and inclusion
7. Character consistency across pages
8. Accuracy of educational / scientific claims

Also provides genuine Before-and-After textual comparison without fabricating edits.
"""

import re
import difflib
import json
import logging

logger = logging.getLogger(__name__)

class SafetyService:
    # Rule-based word lists
    VIOLENCE_WORDS = {
        "kill", "death", "die", "died", "blood", "bloody", "bleed", "wound",
        "hurt", "pain", "knife", "gun", "weapon", "shoot", "stab", "sword",
        "punch", "hit", "kick", "murder", "monster", "nightmare", "terror",
        "scream", "screamed", "demon", "evil", "poison", "strangle", "drown"
    }

    BULLYING_WORDS = {
        "stupid", "idiot", "dumb", "ugly", "fat", "loser", "freak", "hate",
        "hated", "worthless", "shut up", "get lost", "tease", "mocked", "exclude",
        "puny", "useless", "clumsy"
    }

    CULTURAL_SENSITIVITY_WORDS = {
        "primitive", "savage", "exotic", "oriental", "gypsy", "crazy", "insane"
    }

    EDUCATIONAL_CLAIM_KEYWORDS = {
        "gravity", "photosynthesis", "solar system", "planet", "dinosaur",
        "temperature", "oxygen", "bacteria", "molecule", "ecosystem", "orbit"
    }

    # Regex patterns for PII
    EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    PHONE_PATTERN = re.compile(r'(\b\d{3}[-.\s]??\d{3}[-.\s]??\d{4}\b|\b\d{10}\b)')
    ADDRESS_KEYWORDS = ["street", "avenue", "drive", "road", "apartment", "zip code", "postal code"]

    @classmethod
    def audit_storybook(cls, storybook, pages):
        """
        Executes rule-based checks across all 8 dimensions.
        Returns a structured report dictionary with flags, scores, and honest disclaimers.
        """
        age_group = storybook.get("age_group", "6–9 years")
        character_name = storybook.get("character_name", "").strip().lower()
        
        all_text = " ".join([p.get("text", "") for p in pages])
        page_texts = [(p.get("page_number", idx + 1), p.get("text", "")) for idx, p in enumerate(pages)]
        
        flags = []
        
        # 1. Age Appropriateness / Sentence Length Check
        max_words_per_sentence = 12 if "3–5" in age_group else (20 if "6–9" in age_group else 28)
        long_sentences = []
        for page_num, text in page_texts:
            sentences = re.split(r'[.!?]+', text)
            for s in sentences:
                words = s.strip().split()
                if len(words) > max_words_per_sentence:
                    long_sentences.append(f"Page {page_num}: '{s.strip()[:60]}...' ({len(words)} words)")
        
        if long_sentences:
            flags.append({
                "category": "Age Appropriateness",
                "severity": "info",
                "title": "Long Sentences Detected",
                "description": f"Target age {age_group} prefers sentences under {max_words_per_sentence} words for effortless reading aloud.",
                "occurrences": long_sentences[:3]
            })

        # 2. Violence & Frightening Content Check
        violence_hits = []
        for page_num, text in page_texts:
            tokens = re.findall(r'\b[a-z]+\b', text.lower())
            found = set(tokens).intersection(cls.VIOLENCE_WORDS)
            if found:
                violence_hits.append(f"Page {page_num}: Found '{', '.join(found)}'")
        if violence_hits:
            flags.append({
                "category": "Violence & Frightening Content",
                "severity": "danger",
                "title": "Potentially Scary Words Flagged",
                "description": "Consider softening words that might frighten young listeners at bedtime.",
                "occurrences": violence_hits
            })

        # 3. Bullying & Discrimination Check
        bullying_hits = []
        for page_num, text in page_texts:
            tokens = re.findall(r'\b[a-z\s]+\b', text.lower())
            for word in cls.BULLYING_WORDS:
                if word in text.lower():
                    bullying_hits.append(f"Page {page_num}: Contains '{word}'")
        if bullying_hits:
            flags.append({
                "category": "Bullying & Discrimination",
                "severity": "danger",
                "title": "Unkind Language Flagged",
                "description": "Story contains words often associated with teasing or insults. Verify they are resolved kindly.",
                "occurrences": bullying_hits
            })

        # 4. Privacy & PII (Personal Identifiable Information)
        pii_hits = []
        if cls.EMAIL_PATTERN.search(all_text):
            pii_hits.append("Detected possible email address.")
        if cls.PHONE_PATTERN.search(all_text):
            pii_hits.append("Detected possible telephone number.")
        for addr_word in cls.ADDRESS_KEYWORDS:
            if re.search(r'\b\d+\s+[A-Za-z]+\s+' + addr_word, all_text, re.IGNORECASE):
                pii_hits.append(f"Detected possible street address pattern ({addr_word}).")
        if pii_hits:
            flags.append({
                "category": "Privacy & Personal Information",
                "severity": "danger",
                "title": "Potential PII Detected",
                "description": "Stories should not contain real names, personal contact details, or real home addresses.",
                "occurrences": pii_hits
            })

        # 5. Grammar & Readability
        words = re.findall(r'\b\w+\b', all_text)
        sentences = [s for s in re.split(r'[.!?]+', all_text) if s.strip()]
        total_words = len(words)
        total_sentences = max(1, len(sentences))
        avg_sentence_len = round(total_words / total_sentences, 1) if total_sentences else 0
        
        # Flesch Reading Ease approximation
        syllables = sum(cls._estimate_syllables(w) for w in words)
        if total_words > 0 and total_sentences > 0:
            fre_score = round(206.835 - 1.015 * (total_words / total_sentences) - 84.6 * (syllables / total_words), 1)
            fre_score = max(0, min(100, fre_score))
        else:
            fre_score = 80.0

        readability_note = "Very Easy (Ideal for 3-5)" if fre_score >= 80 else ("Easy (Ideal for 6-9)" if fre_score >= 65 else "Moderate (Ideal for 10-12)")

        # 6. Cultural Sensitivity
        cultural_hits = []
        for page_num, text in page_texts:
            tokens = set(re.findall(r'\b[a-z]+\b', text.lower()))
            found = tokens.intersection(cls.CULTURAL_SENSITIVITY_WORDS)
            if found:
                cultural_hits.append(f"Page {page_num}: '{', '.join(found)}'")
        if cultural_hits:
            flags.append({
                "category": "Cultural Sensitivity",
                "severity": "warning",
                "title": "Sensitive Terms Found",
                "description": "Review these words to ensure respectful, inclusive, and culturally uplifting representations.",
                "occurrences": cultural_hits
            })

        # 7. Character Consistency Check
        consistency_notes = []
        if character_name:
            pages_without_char = []
            for page_num, text in page_texts:
                if character_name not in text.lower():
                    pages_without_char.append(str(page_num))
            if len(pages_without_char) > len(page_texts) * 0.5:
                consistency_notes.append(f"Character '{storybook.get('character_name')}' is absent on pages: {', '.join(pages_without_char)}.")
        
        if consistency_notes:
            flags.append({
                "category": "Character Consistency",
                "severity": "info",
                "title": "Protagonist Continuity Check",
                "description": "Ensuring the main character remains central keeps young children engaged.",
                "occurrences": consistency_notes
            })

        # 8. Accuracy of Educational Claims
        edu_hits = []
        for page_num, text in page_texts:
            tokens = set(re.findall(r'\b[a-z\s]+\b', text.lower()))
            for kw in cls.EDUCATIONAL_CLAIM_KEYWORDS:
                if kw in text.lower():
                    edu_hits.append(f"Page {page_num}: Mentions '{kw}'")
        if edu_hits:
            flags.append({
                "category": "Accuracy of Educational Claims",
                "severity": "info",
                "title": "Educational & Science Concepts Detected",
                "description": "Great learning opportunity! Check that scientific or natural facts are portrayed accurately.",
                "occurrences": edu_hits
            })

        # Compute Safety Rating
        has_danger = any(f["severity"] == "danger" for f in flags)
        has_warning = any(f["severity"] == "warning" for f in flags)
        
        if has_danger:
            status = "Needs Human Revision"
            score = 65
        elif has_warning:
            status = "Reviewed with Minor Advisories"
            score = 85
        else:
            status = "Passed Automated Safeguards"
            score = 100

        return {
            "overall_status": status,
            "safety_score": score,
            "flags": flags,
            "readability": {
                "total_words": total_words,
                "total_sentences": total_sentences,
                "avg_sentence_len": avg_sentence_len,
                "flesch_score": fre_score,
                "reading_level": readability_note
            },
            "disclaimer": (
                "IMPORTANT RESPONSIBLE AI NOTICE: Automated rule-based checks act as an initial assistive filter. "
                "They do NOT guarantee 100% child safety, nor can they replace a caring adult or educator's holistic judgment. "
                "Always review and edit all text and visual prompts before sharing with children."
            )
        }

    @classmethod
    def _estimate_syllables(cls, word):
        """Simple syllable estimation heuristic."""
        word = word.lower()
        count = len(re.findall(r'[aeiouy]+', word))
        if word.endswith('e') and not word.endswith('le') and len(word) > 2:
            count = max(1, count - 1)
        return max(1, count)

    @classmethod
    def compare_drafts(cls, original_draft_str, current_storybook, current_pages):
        """
        Calculates genuine before-and-after differences between the original AI draft
        and the user's revised version. Never fabricates changes.
        """
        try:
            original_data = json.loads(original_draft_str) if original_draft_str else {}
        except Exception:
            original_data = {}

        orig_pages = original_data.get("pages", [])
        
        # Word counts
        orig_text_combined = " ".join([p.get("text", "") for p in orig_pages])
        curr_text_combined = " ".join([p.get("text", "") for p in current_pages])
        
        orig_words = len(re.findall(r'\b\w+\b', orig_text_combined))
        curr_words = len(re.findall(r'\b\w+\b', curr_text_combined))
        
        # Page-by-page diffs
        page_diffs = []
        max_pages = max(len(orig_pages), len(current_pages))
        
        total_modified_pages = 0
        for i in range(max_pages):
            orig_p = orig_pages[i] if i < len(orig_pages) else {"text": "", "illustration_prompt": ""}
            curr_p = current_pages[i] if i < len(current_pages) else {"text": "", "illustration_prompt": ""}
            
            orig_txt = orig_p.get("text", "")
            curr_txt = curr_p.get("text", "")
            
            is_changed = (orig_txt.strip() != curr_txt.strip())
            if is_changed:
                total_modified_pages += 1
                
            page_diffs.append({
                "page_number": i + 1,
                "original_text": orig_txt,
                "revised_text": curr_txt,
                "is_changed": is_changed,
                "original_prompt": orig_p.get("illustration_prompt", ""),
                "current_prompt": curr_p.get("illustration_prompt", "")
            })

        # Summary statistics
        return {
            "original_title": original_data.get("title", current_storybook.get("title")),
            "current_title": current_storybook.get("title"),
            "title_changed": original_data.get("title") != current_storybook.get("title"),
            "original_word_count": orig_words,
            "revised_word_count": curr_words,
            "word_count_diff": curr_words - orig_words,
            "original_page_count": len(orig_pages),
            "revised_page_count": len(current_pages),
            "modified_page_count": total_modified_pages,
            "page_diffs": page_diffs
        }
