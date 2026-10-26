"""
Story Generation Service.
Coordinates language model APIs (Gemini, OpenAI) with a rich built-in
responsible story generator fallback when API keys are not provided.
Ensures every story contains 8-10 structured pages, clear narrative arc,
visual prompts with character anchors, and a clear moral.
"""

import json
import logging
import requests
from config import Config

logger = logging.getLogger(__name__)

class StoryService:
    @classmethod
    def generate_story(cls, params):
        """
        Generates a complete structured children's storybook.
        Tries configured API providers first, falling back smoothly to the
        responsible built-in story generator if no keys are set or errors occur.
        """
        title = params.get("title", "").strip() or "The Wonderful Journey"
        age_group = params.get("age_group", "6–9 years")
        theme = params.get("theme", "friendship").lower()
        character_name = params.get("character_name", "").strip() or "Little Explorer"
        character_desc = params.get("character_desc", "").strip() or "A gentle, inquisitive creature with kind eyes"
        supporting_characters = params.get("supporting_characters", "").strip() or "a helpful little robin"
        story_length = int(params.get("story_length", 8))
        story_length = max(8, min(10, story_length)) # Clamp between 8 and 10 pages
        moral = params.get("moral", "").strip() or f"True {theme} brings joy, courage, and harmony to all."
        language = params.get("language", "English")
        art_style = params.get("art_style", "Soft watercolor children's book illustration, friendly faces, gentle lighting")

        # 1. Try Google Gemini API if configured
        if Config.GEMINI_API_KEY:
            try:
                story_data = cls._call_gemini(
                    title, age_group, theme, character_name, character_desc,
                    supporting_characters, story_length, moral, language, art_style
                )
                if story_data and "pages" in story_data and len(story_data["pages"]) >= 8:
                    story_data["generation_source"] = "Google Gemini AI"
                    return story_data
            except Exception as e:
                logger.warning(f"Gemini generation failed, falling back to built-in generator: {e}")

        # 2. Try OpenAI API if configured
        if Config.OPENAI_API_KEY:
            try:
                story_data = cls._call_openai(
                    title, age_group, theme, character_name, character_desc,
                    supporting_characters, story_length, moral, language, art_style
                )
                if story_data and "pages" in story_data and len(story_data["pages"]) >= 8:
                    story_data["generation_source"] = "OpenAI GPT"
                    return story_data
            except Exception as e:
                logger.warning(f"OpenAI generation failed, falling back to built-in generator: {e}")

        # 3. Built-in Responsible Story Generator (Zero external cost / offline fallback)
        story_data = cls._generate_builtin_story(
            title, age_group, theme, character_name, character_desc,
            supporting_characters, story_length, moral, language, art_style
        )
        story_data["generation_source"] = "Built-in Responsible Story Engine"
        return story_data

    @classmethod
    def _call_gemini(cls, title, age_group, theme, character_name, character_desc,
                     supporting_characters, story_length, moral, language, art_style):
        """Calls Google Gemini REST API requesting a structured JSON response."""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={Config.GEMINI_API_KEY}"
        
        prompt = cls._build_llm_prompt(
            title, age_group, theme, character_name, character_desc,
            supporting_characters, story_length, moral, language, art_style
        )
        
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.7,
                "responseMimeType": "application/json"
            }
        }
        
        resp = requests.post(url, json=payload, timeout=25)
        if resp.status_code == 200:
            data = resp.json()
            raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(raw_text)
        return None

    @classmethod
    def _call_openai(cls, title, age_group, theme, character_name, character_desc,
                     supporting_characters, story_length, moral, language, art_style):
        """Calls OpenAI Chat Completion API requesting structured JSON."""
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {Config.OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        prompt = cls._build_llm_prompt(
            title, age_group, theme, character_name, character_desc,
            supporting_characters, story_length, moral, language, art_style
        )
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "You are an award-winning children's book author committed to responsible, safe, uplifting literature."},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.7
        }
        resp = requests.post(url, json=payload, headers=headers, timeout=25)
        if resp.status_code == 200:
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            return json.loads(content)
        return None

    @classmethod
    def _build_llm_prompt(cls, title, age_group, theme, character_name, character_desc,
                           supporting_characters, story_length, moral, language, art_style):
        """Formats an instruction prompt designed for responsible children's storybooks."""
        return f"""
Generate an illustrated children's storybook in JSON format with the following requirements:
- Title: "{title}"
- Target Age Group: "{age_group}"
- Core Theme: "{theme}"
- Main Character: "{character_name}" ({character_desc})
- Supporting Characters: "{supporting_characters}"
- Total Pages: exactly {story_length} pages
- Moral / Takeaway: "{moral}"
- Language: "{language}"
- Art Style Anchor: "{art_style}"

Responsible Child Safeguard Guidelines:
1. Zero frightening content, violence, weapon imagery, or nightmare fuel.
2. Tone must be encouraging, emotionally safe, and age-appropriate.
3. Every page must have:
   - "page_number": integer from 1 to {story_length}
   - "text": 2-4 well-paced sentences suitable for reading aloud to {age_group}.
   - "illustration_prompt": detailed visual description including character visual appearance ({character_desc}) and art style anchor ({art_style}) for visual continuity.
4. Structure:
   - Pages 1-2: Introduction and character motivation
   - Pages 3-5: Gentle challenge or collaborative adventure
   - Pages 6-{story_length-1}: Resolution through teamwork and kindness
   - Page {story_length}: Celebratory conclusion reinforcing the moral.

Return strictly valid JSON with this format:
{{
  "title": "{title}",
  "cover_title": "{title}",
  "age_group": "{age_group}",
  "theme": "{theme}",
  "moral": "{moral}",
  "pages": [
    {{
      "page_number": 1,
      "text": "...",
      "illustration_prompt": "..."
    }}
  ]
}}
"""

    @classmethod
    def _generate_builtin_story(cls, title, age_group, theme, character_name, character_desc,
                                 supporting_characters, story_length, moral, language, art_style):
        """
        High-quality, dynamic story generator that works completely offline.
        Uses structured narrative templates adapted specifically to age groups and themes.
        """
        # Narrative templates by theme
        theme_templates = {
            "friendship": [
                ("Introduction", f"In a sunny valley surrounded by whisper-willow trees lived {character_name}, who loved sharing warm smiles with everyone.",
                 f"{art_style} of {character_name} ({character_desc}) standing cheerfully in a bright sunny meadow of pastel wildflowers."),
                ("Curious Encounter", f"One breezy morning, {character_name} noticed {supporting_characters} sitting quietly by the bubbling brook looking a little lonely.",
                 f"{art_style} showing {character_name} looking across a clear bubbling stream at {supporting_characters} with gentle, caring eyes."),
                ("Reaching Out", f"\"Hello there! Would you like to share my basket of sweet berries?\" asked {character_name} with an open paw and friendly grin.",
                 f"{art_style} of {character_name} offering a woven basket of bright red berries to {supporting_characters} under golden sunshine."),
                ("Finding Joy", f"{supporting_characters} looked up and beamed. Together, they skipped across the stone bridge, discovering that sharing makes everything sweeter.",
                 f"{art_style} of {character_name} and {supporting_characters} happily skipping hand-in-paw across smooth stepping stones over a sparkling river."),
                ("A Gentle Challenge", f"When a sudden gust of wind scattered their painted paper kites into the tall grass, neither friend felt discouraged.",
                 f"{art_style} of colorful paper kites resting gently in soft green clover with {character_name} encouraging their companion."),
                ("Working Together", f"\"If you lift from that side, I will guide from here!\" cheered {character_name}. With teamwork, both kites were safely gathered.",
                 f"{art_style} showing {character_name} and {supporting_characters} collaborating happily to untangle rainbow kites in sunny clover."),
                ("Joyful Flight", f"Up, up into the lavender twilight soared the kites, dancing like bright stars over the peaceful forest canopy.",
                 f"{art_style} of colorful kites soaring into a soft pastel twilight sky while the friends watch side by side with joyful smiles."),
                ("Conclusion & Moral", f"Resting under the twinkling starlight, {character_name} and {supporting_characters} celebrated their newfound bond. {moral}",
                 f"{art_style} of {character_name} and {supporting_characters} resting peacefully on a gentle grassy hill under friendly twinkling stars.")
            ],
            "kindness": [
                ("Introduction", f"At the edge of Sunny Hollow lived {character_name}, known throughout the land for having a heart full of golden sunshine.",
                 f"{art_style} of {character_name} ({character_desc}) tending a cheerful garden of glowing sun-flowers in morning mist."),
                ("Noticing Need", f"While watering the morning blooms, {character_name} spotted {supporting_characters} trying to carry a bundle of fallen branches.",
                 f"{art_style} of {character_name} noticing {supporting_characters} carefully balancing wooden twigs on a cobblestone path."),
                ("Offering Help", f"Without waiting to be asked, {character_name} hurried over. \"Let me carry the heavy end for you!\" was the cheerful offer.",
                 f"{art_style} of {character_name} smiling warmly while lifting the heavy side of the bundle beside {supporting_characters}."),
                ("A Warm Connection", f"Step by step, the bundle felt as light as a feather when carried together with cheerful laughter along the path.",
                 f"{art_style} of {character_name} and companion strolling together down a flower-lined lane with sunbeams dancing around them."),
                ("Sharing Shelter", f"When cool drops of rain began to pitter-patter, they quickly stacked the wood and built a cozy shelter for forest creatures.",
                 f"{art_style} of {character_name} and friend creating a safe, welcoming wooden hideaway with forest birds perching dry and snug under the leafy roof."),
                ("Ripple of Smiles", f"{supporting_characters} smiled warmly and gave {character_name} a polished glass marble that sparkled with colors.",
                 f"{art_style} of {supporting_characters} handing a rainbow glass pebble to {character_name} in mutual appreciation."),
                ("Warm Evenings", f"Other woodland friends gathered round, each bringing a sweet song or warm herbal tea to celebrate their helpful neighbors.",
                 f"{art_style} of {character_name} and cheerful animal neighbors gathered around a small lantern on a cozy porch sharing cups of warm tea."),
                ("Conclusion & Moral", f"Watching the lantern glow, {character_name} felt that kindness is the one gift that grows bigger every time it is given. {moral}",
                 f"{art_style} of {character_name} smiling happily in soft bedtime lighting, safe and content in community love.")
            ],
            "environment": [
                ("Introduction", f"Deep in the emerald woods lived {character_name}, who loved listening to the gentle songs of singing trees and rivers.",
                 f"{art_style} of {character_name} ({character_desc}) leaning gently against a mossy tree trunk listening to forest music."),
                ("A River's Call", f"One sparkling dawn, {character_name} noticed that the singing river was unusually quiet because leaves and twigs blocked its way.",
                 f"{art_style} of a winding stream with floating twigs creating a calm pool while {character_name} watches thoughtfully."),
                ("Calling a Friend", f"\"Let's help the water dance again!\" called {character_name} to {supporting_characters}, who arrived with eager paws and wings.",
                 f"{art_style} of {character_name} waving cheerfully to {supporting_characters} near the shaded riverbank."),
                ("Clearing the Path", f"One by one, they lifted the fallen branches, placing them safely beside the bank to create winter homes for beetles.",
                 f"{art_style} of {character_name} and {supporting_characters} creating a tidy brush pile home for small woodland insects."),
                ("The Waters Sing", f"With a joyous splash, the river bubbled into life again, sparkling like crystal ribbons over smooth blue river stones.",
                 f"{art_style} of crystal clear water flowing merrily over polished stones, creating tiny rainbows in the sunshine."),
                ("Nature's Gratitude", f"Thirsty bluebells and tall ferns along the water bank raised their leaves happily, thanking the little caretakers.",
                 f"{art_style} of lush green ferns and purple wildflowers nodding gracefully towards {character_name} and friends."),
                ("A Forest Sanctuary", f"{character_name} planted three new acorns right beside the riverbank, whispering words of growth and sunshine.",
                 f"{art_style} of {character_name} planting little seeds into dark rich soil with gentle, protective hands."),
                ("Conclusion & Moral", f"The forest sang in joyful harmony under the golden sunset. {character_name} knew that protecting our Earth begins with small, loving acts. {moral}",
                 f"{art_style} of {character_name} and forest friends standing beside the sparkling river under a majestic golden sunset.")
            ],
            "adventure": [
                ("The Map", f"In a cozy nook under the old bookshelf, {character_name} discovered a curious golden map marked with a smiling compass.",
                 f"{art_style} of {character_name} ({character_desc}) examining a vintage storybook map on a rustic wooden floor."),
                ("Setting Forth", f"With a sturdy walking stick and backpack of oat cookies, {character_name} invited {supporting_characters} along for the quest.",
                 f"{art_style} of {character_name} and {supporting_characters} setting off cheerfully down a winding cobblestone trail."),
                ("The Misty Bridge", f"They arrived at the Whispering Bridge, where morning mist rolled softly over the mossy stones.",
                 f"{art_style} of a safe, gentle stone bridge over a calm misty ravine with glowing fireflies lighting the way."),
                ("Courage Together", f"\"Hold tight, we can cross together one step at a time,\" whispered {character_name} with reassuring warmth.",
                 f"{art_style} of the two travelers holding hands and stepping calmly across the bridge under morning glow."),
                ("The Hidden Meadow", f"On the other side lay the legendary Valley of Whispering Bells, filled with giant glowing bluebells that chimed soft melodies.",
                 f"{art_style} of a magical dreamlike valley filled with oversized glowing bluebell flowers ringing in the wind."),
                ("The Discovery", f"In the center of the meadow was not gold or jewels, but a fountain of pure sweet water where all creatures drank in peace.",
                 f"{art_style} of a beautiful stone birdbath fountain with gentle bunnies and fawns sipping fresh water safely."),
                ("Journey Home", f"Having solved the riddle of the map, the brave friends began their journey back, their hearts filled with wonder.",
                 f"{art_style} of {character_name} and companion walking happily homeward as the afternoon sky turns warm apricot."),
                ("Conclusion & Moral", f"Home was cozier than ever, but {character_name} now held memories of courage and friendship that would last forever. {moral}",
                 f"{art_style} of {character_name} tucked under a quilt sipping warm milk while gazing out at the starry night sky.")
            ],
            "education": [
                ("Wonder Begins", f"Every night, {character_name} looked up at the moon and wondered: \"Why does the moon seem to change its silver shape?\"",
                 f"{art_style} of {character_name} ({character_desc}) looking out a circular cottage window at a crescent moon."),
                ("The Little Telescope", f"Together with wise {supporting_characters}, {character_name} polished a small brass telescope made of looking glasses.",
                 f"{art_style} of {character_name} peering through a child's brass telescope alongside {supporting_characters}."),
                ("The Experiment", f"They took an orange, a flashlight, and a small wooden ball to recreate the dance of the Sun, Earth, and Moon.",
                 f"{art_style} of {character_name} holding a toy flashlight illuminating a small ball, casting a soft shadow on a table."),
                ("The Discovery Moment", f"\"Aha!\" gasped {character_name}. \"The moon isn't disappearing at all! It's just the sunlight making shadows as it travels!\"",
                 f"{art_style} of {character_name} with an expression of delighted discovery, eyes wide and smiling brightly."),
                ("Drawing the Phases", f"In a colorful notebook, {character_name} painted each phase: the crescent, the half moon, and the glowing full moon.",
                 f"{art_style} of a child's sketchbook with hand-drawn pastel moon phases, paints, and brushes on the table."),
                ("Sharing Knowledge", f"The next day at the village circle, {character_name} demonstrated the shadow dance to eager young animal friends.",
                 f"{art_style} of young animal students listening attentively as {character_name} demonstrates science happily."),
                ("Curiosity Sparks", f"Questions buzzed in the air like friendly bees, each answer opening up a new world of wonder and scientific curiosity.",
                 f"{art_style} of smiling woodland students raising hands with cheerful enthusiasm under a shady learning tree."),
                ("Conclusion & Moral", f"Looking up at the night sky once more, {character_name} knew that asking questions is the greatest superpower in the universe. {moral}",
                 f"{art_style} of {character_name} sitting peacefully under a full silver moon with a science sketchbook held close.")
            ]
        }

        # Select appropriate template set or fallback to friendship
        selected_pages = theme_templates.get(theme, theme_templates["friendship"])
        
        # If user asked for 9 or 10 pages, expand middle adventure cleanly
        pages_output = []
        for idx in range(story_length):
            if idx < len(selected_pages):
                section, text, prompt = selected_pages[idx]
            else:
                # Supplementary bonus page for 9 or 10 page preference
                section = f"Joyful Reflection {idx+1}"
                text = f"As afternoon gave way to dusk, {character_name} and {supporting_characters} sang a sweet melody that echoed through the hills, reminding everyone that love and learning never end."
                prompt = f"{art_style} of {character_name} ({character_desc}) singing happily beside {supporting_characters} under a warm pink and violet sunset sky."

            pages_output.append({
                "page_number": idx + 1,
                "text": text,
                "illustration_prompt": prompt
            })

        return {
            "title": title,
            "cover_title": title,
            "age_group": age_group,
            "theme": theme,
            "character_name": character_name,
            "character_desc": character_desc,
            "supporting_characters": supporting_characters,
            "moral": moral,
            "pages": pages_output
        }
