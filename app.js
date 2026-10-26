/**
 * StorySprout AI - Client-Side Interactive Engine
 * Handles Browser Speech Synthesis (Web Speech API), live word counts,
 * image upload previews, prompt copying, and accessible UI interactions.
 */

// Global Speech Synthesis Controller
let currentUtterance = null;

function speakText(text) {
  if (!('speechSynthesis' in window)) {
    alert("Sorry, your browser does not support the Web Speech API. You can use the generated MP3 audio file instead!");
    return;
  }

  // Cancel any ongoing speech
  window.speechSynthesis.cancel();

  if (!text || !text.trim()) {
    return;
  }

  const cleanText = text.trim();
  const utterance = new SpeechSynthesisUtterance(cleanText);
  currentUtterance = utterance;

  // Gentle, friendly pacing for children's reading
  utterance.rate = 0.92;
  utterance.pitch = 1.05;

  // Select warm, natural English voice if available
  const voices = window.speechSynthesis.getVoices();
  const preferredVoice = voices.find(v => 
    v.lang.startsWith('en') && (v.name.includes('Natural') || v.name.includes('Google') || v.name.includes('Samantha') || v.name.includes('Karen'))
  );
  if (preferredVoice) {
    utterance.voice = preferredVoice;
  }

  utterance.onstart = function() {
    console.log("Started reading aloud...");
  };

  utterance.onerror = function(e) {
    console.warn("Speech synthesis notice:", e);
  };

  window.speechSynthesis.speak(utterance);
}

function stopSpeech() {
  if ('speechSynthesis' in window) {
    window.speechSynthesis.cancel();
  }
}

// Live Word Count Calculator
function updateWordCount(textarea) {
  const badge = document.getElementById('wordCountBadge');
  if (!badge) return;
  const words = textarea.value.trim() ? textarea.value.trim().split(/\s+/).length : 0;
  badge.innerText = `Words: ${words}`;
}

// Image File Upload Preview
function previewUploadImage(input) {
  const previewBox = document.getElementById('uploadPreviewBox');
  const previewImg = document.getElementById('uploadPreviewImg');
  if (input.files && input.files[0]) {
    const file = input.files[0];
    
    // Check 5MB limit
    if (file.size > 5 * 1024 * 1024) {
      alert("File size exceeds 5MB limit. Please select a smaller image.");
      input.value = "";
      if (previewBox) previewBox.style.display = 'none';
      return;
    }

    const reader = new FileReader();
    reader.onload = function(e) {
      if (previewImg && previewBox) {
        previewImg.src = e.target.result;
        previewBox.style.display = 'block';
      }
    };
    reader.readAsDataURL(file);
  }
}

// Prompt Library Copy to Clipboard
function copyPrompt(id, btn) {
  const el = document.getElementById('promptText-' + id);
  if (!el) return;
  const text = el.innerText.trim();
  navigator.clipboard.writeText(text).then(() => {
    const orig = btn.innerText;
    btn.innerText = "✓ Copied!";
    btn.style.background = "#2E7D32";
    setTimeout(() => {
      btn.innerText = orig;
      btn.style.background = "";
    }, 2000);
  }).catch(err => {
    console.error("Copy failed: ", err);
  });
}

// Category Filter in Prompt Library
function filterCategory(cat) {
  const cards = document.querySelectorAll('.prompt-card');
  cards.forEach(card => {
    if (cat === 'all' || card.getAttribute('data-category') === cat) {
      card.style.display = 'flex';
    } else {
      card.style.display = 'none';
    }
  });
}

// Form Submission Spinner & Lockout
document.addEventListener("DOMContentLoaded", function() {
  const storyForm = document.getElementById("storyForm");
  const submitBtn = document.getElementById("submitBtn");

  if (storyForm && submitBtn) {
    storyForm.addEventListener("submit", function() {
      submitBtn.disabled = true;
      submitBtn.innerHTML = "🌱 Weaving Your Story...";
    });
  }

  // Auto load speech synthesis voices on Chrome/Firefox
  if ('speechSynthesis' in window) {
    window.speechSynthesis.onvoiceschanged = function() {
      window.speechSynthesis.getVoices();
    };
  }
});
