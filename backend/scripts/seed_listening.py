"""
Seed full IELTS Listening test (4 parts, 40 questions) for IELTS Academic Mock #1.

- Generates 4 MP3 audio files via Edge TTS in backend/media/
- Deletes existing Listening sections for this test
- Creates 4 new sections (one per Part)
- Creates 40 questions with answer_key

Usage:
    cd backend
    venv\\Scripts\\python scripts\\seed_listening.py
"""

import asyncio
import sys
import uuid
from pathlib import Path

import edge_tts

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.models.question import Question, QuestionType
from app.models.section import Section, SectionType
from app.models.test import Test

DATABASE_URL = "postgresql+asyncpg://postgres:2770@localhost:5432/ielts_mock"
TEST_TITLE = "IELTS Academic Mock #1"
MEDIA_DIR = Path(__file__).parent.parent / "media"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────────────────────────────────────
#  Audio scripts
# ─────────────────────────────────────────────────────────────────────────────

PART1_SCRIPT = [
    ("en-GB-RyanNeural",
     "Hello, is that Oyster Bay Sailing Club?"),
    ("en-GB-SoniaNeural",
     "Good morning, yes, Oyster Bay Sailing Club, Sarah speaking. How can I help?"),
    ("en-GB-RyanNeural",
     "Hi Sarah, I'm interested in learning to sail. Could you tell me about the courses you offer?"),
    ("en-GB-SoniaNeural",
     "Of course! We have two main courses at the moment. The first is our Taster Day, which is ideal if you've never sailed before. It's a one-day introduction to sailing — you'll get a feel for being on the water and learn the very basics."),
    ("en-GB-RyanNeural",
     "That sounds good. How much does the Taster Day cost?"),
    ("en-GB-SoniaNeural",
     "If you book a place individually, the cost is one hundred and twenty pounds. The sessions are kept quite small — a maximum of eight people per group — so you get plenty of personal attention from the instructor."),
    ("en-GB-RyanNeural",
     "Eight people — that does sound manageable. And is there a more in-depth course for after the Taster Day?"),
    ("en-GB-SoniaNeural",
     "Yes, our Level One course is the natural next step. Over several sessions you'll cover the basic theory — things like understanding wind direction and tides — as well as practical sailing skills. One session is dedicated specifically to weather: reading forecasts and understanding weather patterns is essential information for anyone going out on open water."),
    ("en-GB-RyanNeural",
     "What does the Level One course cost?"),
    ("en-GB-SoniaNeural",
     "The full course is two hundred and sixty pounds. If you're already a member of the club, there's a discount available, so it works out cheaper. The fee is all-inclusive — equipment hire and insurance are all covered — and participants also receive a useful guidebook that you keep afterwards."),
    ("en-GB-RyanNeural",
     "Is there anything to show for completing the course?"),
    ("en-GB-SoniaNeural",
     "Yes, absolutely. You'll receive a certificate at the end of the course, awarded to all participants who complete the programme. It's nationally recognised and useful if you want to progress to more advanced sailing later."),
    ("en-GB-RyanNeural",
     "Excellent. Now, what should I bring if I sign up?"),
    ("en-GB-SoniaNeural",
     "First, participants must be able to swim — that's a safety requirement. You should bring suitable clothing for being outdoors on the water, a towel, and any toiletries such as shampoo, as we do have shower facilities on site."),
    ("en-GB-RyanNeural",
     "Good to know. Are there other facilities at the club itself?"),
    ("en-GB-SoniaNeural",
     "Yes, there is a café at the club which serves hot drinks and light meals — very welcome after a session on the water. We also strongly recommend that before your first practical session you watch our online training videos, which cover the basics and really help you get the most out of your time on the water."),
    ("en-GB-RyanNeural",
     "That's helpful. Is there anywhere to store my belongings while I'm out sailing?"),
    ("en-GB-SoniaNeural",
     "Absolutely. Lockers are available for all course participants, free of charge. You'll be given a key at the start of each session."),
    ("en-GB-RyanNeural",
     "Perfect. I'd like to start with the Taster Day. How do I book?"),
    ("en-GB-SoniaNeural",
     "You can book online through our website, or you can call us back and I can take your details over the phone. We have availability on the fifteenth and the twenty-second of next month."),
    ("en-GB-RyanNeural",
     "I'll go online now. Thank you so much for all the information, Sarah."),
    ("en-GB-SoniaNeural",
     "You're very welcome. We look forward to seeing you on the water!"),
]

PART2_SCRIPT = [
    ("en-GB-SoniaNeural",
     "Hello everyone, and welcome to this talk about working as a makeup trainee in the film and television industry. My name is Diana, and I've spent the past twelve years working as a professional makeup artist, so I hope I can share some useful insights with you today."),
    ("en-GB-SoniaNeural",
     "Let's start with what you should actually expect when you're just starting out. Many people come into this industry with very romantic ideas — they imagine glamour and celebrities. The reality of low budget short films is quite different. You should always expect to receive travel expenses, but don't count on a minimum wage or free meals. Productions at that level rarely offer those. The one consistent thing you'll get is your travel covered."),
    ("en-GB-SoniaNeural",
     "Now, moving up to bigger budget productions is a different story. On big budget films, trainees may get experience of working with different ethnicities. That's one of the most valuable things — you develop real technical skill across a much wider range of skin tones and hair types than you would on a local production. You won't typically get experience of special effects makeup at that stage, and creating a variety of hair styles is usually handled by a separate hair department."),
    ("en-GB-SoniaNeural",
     "One of the most common problems that makeup artists talk about — and this surprises people — is waiting around for hours doing nothing. That's the nature of film sets. There's a lot of standing by. Dealing with difficult directors does happen occasionally, and yes, sometimes supervisors can be demanding, but the real drain on your energy is simply the downtime."),
    ("en-GB-SoniaNeural",
     "Meeting famous actors — what's that like for the first time? Most people feel very shy. You're suddenly in very close physical proximity to someone you've only ever seen on a screen. It can feel overwhelming. I didn't feel proud or disappointed — just very, very shy. That feeling does pass with experience."),
    ("en-GB-SoniaNeural",
     "Now let me give you some practical advice. What should be in your makeup kit? My advice is: always carry a basic kit with you. Every single day, wherever you go. Not the most expensive products — the basics. And don't rely on other artists to check your kit. Keep it organised yourself."),
    ("en-GB-SoniaNeural",
     "And about your portfolio: it's essential, but be selective. Only include a small selection of photos — your absolute best work. You might be tempted to fill it with everything you've done, but casting directors and heads of department look at portfolios very quickly. Make every image count. And always get permission to use photos from a shoot before including them."),
    ("en-GB-SoniaNeural",
     "Finally, let's talk about the specific skills required for different duties. Pressing an actor — preparing their skin and applying base makeup before filming — this requires you to be well-organised above everything else. You need to have everything ready and know exactly what you're doing before the actor sits down. There's no time to search for products. Continuity work, which means matching makeup exactly between shots that might be filmed days apart, demands that you are flexible. Schedules change, lighting changes, and you have to adapt instantly. And general makeup assistance — helping senior artists, setting up, cleaning — this is all about working quickly. Speed and efficiency matter here more than anything else. I'd also add that shade documentation — the accurate recording of every product and colour shade used in a look — is a duty where being well-organised is absolutely essential. Those records may be needed weeks or even months later to recreate a look precisely."),
    ("en-GB-SoniaNeural",
     "Thank you very much for listening. I hope this has given you a realistic picture of what to expect, and I wish you the very best in building your careers."),
]

PART3_SCRIPT = [
    ("en-AU-NatashaNeural",
     "So, I attended that public lecture on marine biodiversity last week. The one by Professor Gould. Did you go?"),
    ("en-GB-RyanNeural",
     "I did, yes. It was quite something. What did you think had the greatest impact on the audience?"),
    ("en-AU-NatashaNeural",
     "Honestly, I think it was the broad focus of the examples he used — he drew on cases from every ocean on the planet, not just local ones. That gave it a global feel that really resonated. And the references to local problems helped too, but I think the broad examples was the main thing."),
    ("en-GB-RyanNeural",
     "Interesting. I was more struck by the type of issues he discussed — it wasn't just about fish stocks, it covered coral bleaching, microplastics, invasive species. The breadth of topics was impressive. I thought that had the greatest impact."),
    ("en-AU-NatashaNeural",
     "Fair enough. He didn't really make practical suggestions for solutions though, did he? And I thought the implications for government policy were a bit underdeveloped."),
    ("en-GB-RyanNeural",
     "Agreed on both counts. Anyway — what about the research project our supervisor mentioned? The team at the Marine Institute."),
    ("en-AU-NatashaNeural",
     "Yes! What impressed me most about that project was the use of new technology. They've deployed autonomous underwater drones to map reef systems at a resolution that was simply impossible before."),
    ("en-GB-RyanNeural",
     "Really? I was most impressed by the extensive statistical evidence they compiled — years of data across multiple sites. That's what gives the findings real credibility."),
    ("en-AU-NatashaNeural",
     "Good point. The team's previous successes didn't really come up in the presentation, and the geographical scale was large but that's increasingly standard now. It was definitely the technology for me."),
    ("en-GB-RyanNeural",
     "Let me ask you something. Our professor gave us a list of resources to review for the project. I want to get your opinion on each of them."),
    ("en-AU-NatashaNeural",
     "Sure. Go ahead."),
    ("en-GB-RyanNeural",
     "First — the article on invasive lionfish in the Atlantic."),
    ("en-AU-NatashaNeural",
     "Hmm. I found it rather predictable to be useful, honestly. We already know the basic story. It doesn't add anything new."),
    ("en-GB-RyanNeural",
     "I agree — it's not telling us anything we don't already know. What about the documentary on microplastics?"),
    ("en-AU-NatashaNeural",
     "That one aims at a very specialist audience. It's technically dense — not suitable for a general overview. Good for depth, but limited scope."),
    ("en-GB-RyanNeural",
     "I agree. The podcast on ocean pollution?"),
    ("en-AU-NatashaNeural",
     "It's now rather outdated. The data is from several years ago and the field has moved on significantly."),
    ("en-GB-RyanNeural",
     "Yes, same impression. The book on coastal ecosystems?"),
    ("en-AU-NatashaNeural",
     "I thought it was an effective description of a new danger — the chapter on seagrass loss was particularly good. I'd recommend it."),
    ("en-GB-RyanNeural",
     "Agreed, that was excellent. The article on marine toxicity?"),
    ("en-AU-NatashaNeural",
     "That one suggests possible ways to improve the situation, which is exactly what we need for the policy section of our report."),
    ("en-GB-RyanNeural",
     "Perfect. And the podcast on floating marine cities?"),
    ("en-AU-NatashaNeural",
     "This gives a clear explanation of the problems — really accessible and well-structured. Good for background reading."),
    ("en-GB-RyanNeural",
     "Great. I think we've got a solid reading list now. Let's divide these up and start this week."),
    ("en-AU-NatashaNeural",
     "Sounds good. I'll take the book and the toxicity article. You start with the documentary and the podcast on pollution."),
]

PART4_SCRIPT = [
    ("en-GB-RyanNeural",
     "Good morning everyone. Today's lecture is about rubber — specifically, where it comes from, why it matters, and what challenges face the industry that produces it. Rubber is one of three resources considered absolutely essential for industrial civilisation. The other two are steel and fossil fuels. Without rubber, modern transportation and manufacturing as we know them would not function."),
    ("en-GB-RyanNeural",
     "There are two types of rubber: natural rubber and synthetic rubber. Let's start with natural rubber. Natural rubber mainly comes from the Para rubber tree, which was originally native to the Amazon basin but is now cultivated extensively in South-East Asia — particularly in Malaysia, Indonesia, and Thailand."),
    ("en-GB-RyanNeural",
     "The supply of natural rubber is limited for several important reasons. First, the growth of the tree is slow — it takes around seven years before a Para rubber tree is mature enough to be tapped for latex. This long lead time makes it very difficult to respond quickly to changes in demand. Second, production cannot easily be adjusted because of increasing or decreasing demand. Unlike a factory that can simply run extra shifts, you cannot accelerate or slow a rubber plantation on short notice. Third, the tree only grows near the equator, in a tropical belt roughly ten degrees either side — limiting which countries can produce it at all. Fourth, extracting the latex from rubber trees is extremely labour intensive. Workers must make precise cuts in the bark early in the morning before the heat causes the latex to thicken. And fifth, it is very difficult to store rubber after production. Latex degrades relatively quickly and must be processed promptly, adding logistical complexity to the supply chain."),
    ("en-GB-RyanNeural",
     "In recent years new threats to the natural rubber supply have emerged. The first is a lack of genetic diversity among cultivated trees, leading to danger of a disease caused by a fungal pathogen. Because virtually all commercial trees descend from a very small number of seedlings brought from Brazil in the nineteenth century, the entire global crop is genetically almost identical. A single airborne fungus could devastate the supply. Second, there has been a shift to the cultivation of palm oil in many traditional rubber-growing areas, as palm oil is currently more profitable. And third, extreme weather events — intensified by climate change — are disrupting harvests with increasing frequency."),
    ("en-GB-RyanNeural",
     "Now let us turn to synthetic rubber. Synthetic rubber may be used for many parts and cooking utensils, and it has found widespread application in everyday consumer products. However, it is less durable than natural rubber — it wears out faster under stress and heat. And critically, it is unsuitable for many purposes, including the tyres of large aircraft. The combination of heat, pressure, and flexing during take-off and landing requires natural rubber's unique properties. There is simply no viable synthetic substitute for aircraft tyres."),
    ("en-GB-RyanNeural",
     "Finally, researchers are actively investigating an alternative source of natural rubber. A wild flower — a type of dandelion found in Central Asia — has rubber in its roots. Unlike the Para rubber tree, this dandelion can be grown in many locations across different climate zones and does not require the good soil quality that tropical rubber cultivation demands. If this alternative can be scaled up, it could significantly reduce the world's dependence on South-East Asian plantations and provide a buffer against disease and climate disruption."),
    ("en-GB-RyanNeural",
     "To summarise the key points: natural rubber remains indispensable despite significant supply constraints; synthetic rubber fills many needs but cannot replace natural rubber in critical applications; and new biological sources offer promising but as yet unproven alternatives. For next week, please read chapter seven of your textbook and look at the supplementary article on the Leaf Blight fungus I have uploaded to the course portal. Thank you."),
]


# ─────────────────────────────────────────────────────────────────────────────
#  TTS generation
# ─────────────────────────────────────────────────────────────────────────────

async def generate_audio(lines: list[tuple[str, str]], output_path: Path) -> None:
    """Concatenate multiple TTS lines into a single MP3 file."""
    import tempfile, os
    tmp_files = []
    for i, (voice, text) in enumerate(lines):
        tmp = Path(tempfile.gettempdir()) / f"tts_part_{output_path.stem}_{i}.mp3"
        communicate = edge_tts.Communicate(text, voice, rate="-5%")
        await communicate.save(str(tmp))
        tmp_files.append(tmp)

    # Concatenate all mp3 chunks into one file by simple binary concat
    # (MP3 binary concat works fine for sequential speech)
    with output_path.open("wb") as out:
        for f in tmp_files:
            out.write(f.read_bytes())
    for f in tmp_files:
        f.unlink(missing_ok=True)
    print(f"  OK  Saved {output_path} ({output_path.stat().st_size // 1024} KB)")


# ─────────────────────────────────────────────────────────────────────────────
#  Part 1: compound question data (table + notes-card)
# ─────────────────────────────────────────────────────────────────────────────

# Each cell is either a plain string or a list of segments:
#   {"text": "..."} — literal text (supports \n for line breaks)
#   {"gap": "N"}    — inline input whose answer is stored on Q with gap_key=="N"

PART1_TABLE = {
    "title": "Oyster Bay Sailing Club Courses",
    "headers": ["Name of course", "What you learn", "Cost", "Other information"],
    "rows": [
        [
            "Taster Day",
            "introduction to sailing",
            "£120 if booking one place",
            [
                {"text": "small groups (max "},
                {"gap": "1"},
                {"text": " people)"},
            ],
        ],
        [
            "Level 1",
            [
                {"text": "• basic theory e.g. understanding "},
                {"gap": "2"},
                {"text": " and tides\n• basic sailing skills including "},
                {"gap": "3"},
                {"text": " information"},
            ],
            [
                {"text": "• £260\n• "},
                {"gap": "4"},
                {"text": " available for club members\n• all-inclusive (plus a useful "},
                {"gap": "5"},
                {"text": ")"},
            ],
            [
                {"text": "a "},
                {"gap": "6"},
                {"text": " at the end of the course for all participants"},
            ],
        ],
    ],
}

PART1_NOTES = {
    "title": "General Information",
    "items": [
        "Participants must be able to swim.",
        [
            {"text": "Bring suitable clothing, a "},
            {"gap": "7"},
            {"text": " and toiletries (e.g. shampoo)."},
        ],
        [{"text": "There is a "}, {"gap": "8"}, {"text": " at the club."}],
        [{"text": "Online training "}, {"gap": "9"}, {"text": " are recommended."}],
        [{"gap": "10"}, {"text": " are available for course participants."}],
    ],
}


# ─────────────────────────────────────────────────────────────────────────────
#  Question definitions
# ─────────────────────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────────────────────
#  Part 2: shared matching-dropdown data (Duties)
# ─────────────────────────────────────────────────────────────────────────────

PART2_DUTIES = {
    "options_pool": [
        "A. being well-organised",
        "B. being flexible",
        "C. working quickly",
    ],
    "group_title": "Duties",
    "instruction": "What ability is required for each of the following duties?\nChoose the correct letter, A-C, next to Questions 17-20.",
}

# ─────────────────────────────────────────────────────────────────────────────
#  Part 3: shared pair and matching-dropdown data
# ─────────────────────────────────────────────────────────────────────────────

PART3_FEATURES_PAIR = {
    "pair_question": "Which TWO features of the lecture on ocean biodiversity had the greatest impact on the students?",
    "options": [
        "A. the references to local problems",
        "B. the broad focus of the examples",
        "C. the practical suggestions for solutions",
        "D. the type of issues discussed",
        "E. the implications for government policy",
    ],
    "instruction": "Choose TWO letters, A-E.",
}

PART3_PROJECT_PAIR = {
    "pair_question": "Which TWO details about the research project particularly impressed the students?",
    "options": [
        "A. the team's previous successes",
        "B. its wide geographical scale",
        "C. the use of new technology",
        "D. the extensive statistical evidence",
        "E. the large range of specialists involved",
    ],
    "instruction": "Choose TWO letters, A-E.",
}

PART3_OPINIONS = {
    "options_pool": [
        "A. This is aimed at a very specialist audience.",
        "B. This is now rather outdated.",
        "C. This was an effective description of a new danger.",
        "D. This suggests possible ways to improve the situation.",
        "E. This does not give a balanced account.",
        "F. This is too predictable to be useful.",
        "G. This gives insufficient evidence for its claims.",
        "H. This gives a clear explanation of the problems.",
    ],
    "group_title": "Resources",
    "instruction": "What is the students' opinion of each of the following resources related to ocean biodiversity?\nChoose the correct letter, A-H, next to Questions 25-30.",
}

# ─────────────────────────────────────────────────────────────────────────────
#  Part 4: structured notes-card with sub-headings (Sources of rubber)
# ─────────────────────────────────────────────────────────────────────────────
# Items can be:
#   str                              — plain text / bullet
#   {"heading": "..."}              — bold sub-section heading
#   [{"text": "..."}, {"gap": "N"}] — bullet with inline gap

PART4_NOTES = {
    "title": "Sources of rubber",
    "items": [
        "Three resources which are essential for industrial civilisation",
        [{"text": "• "}, {"gap": "31"}],
        "• fossil fuels",
        "• rubber",
        {"heading": "Natural rubber"},
        "This mainly comes from the Para rubber tree, now cultivated in South-East Asia. The supply is limited because",
        [{"text": "• the growth of the tree is "}, {"gap": "32"}],
        [{"text": "• production cannot easily be adjusted because of increasing or decreasing "}, {"gap": "33"}],
        [{"text": "• the tree only grows near the "}, {"gap": "34"}],
        "• extracting the latex (rubber) is labour intensive",
        [{"text": "• it is very difficult to "}, {"gap": "35"}, {"text": " rubber after production"}],
        {"heading": "New threats include"},
        [{"text": "• lack of genetic diversity, leading to danger of a disease caused by a "}, {"gap": "36"}],
        "• a shift to the cultivation of palm oil",
        [{"text": "• extreme "}, {"gap": "37"}, {"text": " events"}],
        {"heading": "Synthetic rubber"},
        "• may be used for engine parts and cooking utensils",
        [{"text": "• is less "}, {"gap": "38"}, {"text": " than natural rubber"}],
        "• is unsuitable for many purposes e.g. the tyres of aircraft",
        {"heading": "An alternative source of natural rubber"},
        [{"text": "• A wild flower (a type of dandelion) has rubber in its "}, {"gap": "39"}],
        [{"text": "• It can be grown in many locations and does not require good "}, {"gap": "40"}],
    ],
}


# Set of part numbers to seed (keeps others intact when running the script)
PARTS_TO_SEED: set[int] = {2, 3, 4}

QUESTIONS: dict[int, list[dict]] = {
    # ── PART 1 — Table completion (Q1-6) + Notes card (Q7-10) ────────────────
    1: [
        {
            "order": 1,
            "question_type": QuestionType.GAP_FILL,
            "content": {
                "part": 1,
                "table_id": "p1_oyster",
                "gap_key": "1",
                "table": PART1_TABLE,
                "instruction": "Complete the table below.\nWrite ONE WORD AND/OR A NUMBER for each answer.",
            },
            "answer_key": {"correct": ["8", "eight"]},
        },
        {
            "order": 2,
            "question_type": QuestionType.GAP_FILL,
            "content": {
                "part": 1,
                "table_id": "p1_oyster",
                "gap_key": "2",
                "table": PART1_TABLE,
            },
            "answer_key": {"correct": "wind"},
        },
        {
            "order": 3,
            "question_type": QuestionType.GAP_FILL,
            "content": {
                "part": 1,
                "table_id": "p1_oyster",
                "gap_key": "3",
                "table": PART1_TABLE,
            },
            "answer_key": {"correct": "weather"},
        },
        {
            "order": 4,
            "question_type": QuestionType.GAP_FILL,
            "content": {
                "part": 1,
                "table_id": "p1_oyster",
                "gap_key": "4",
                "table": PART1_TABLE,
            },
            "answer_key": {"correct": "discount"},
        },
        {
            "order": 5,
            "question_type": QuestionType.GAP_FILL,
            "content": {
                "part": 1,
                "table_id": "p1_oyster",
                "gap_key": "5",
                "table": PART1_TABLE,
            },
            "answer_key": {"correct": "guidebook"},
        },
        {
            "order": 6,
            "question_type": QuestionType.GAP_FILL,
            "content": {
                "part": 1,
                "table_id": "p1_oyster",
                "gap_key": "6",
                "table": PART1_TABLE,
            },
            "answer_key": {"correct": "certificate"},
        },
        {
            "order": 7,
            "question_type": QuestionType.GAP_FILL,
            "content": {
                "part": 1,
                "notes_id": "p1_general",
                "gap_key": "7",
                "notes": PART1_NOTES,
                "instruction": "Complete the notes below.\nWrite ONE WORD ONLY for each answer.",
            },
            "answer_key": {"correct": "towel"},
        },
        {
            "order": 8,
            "question_type": QuestionType.GAP_FILL,
            "content": {
                "part": 1,
                "notes_id": "p1_general",
                "gap_key": "8",
                "notes": PART1_NOTES,
            },
            "answer_key": {"correct": "cafe"},
        },
        {
            "order": 9,
            "question_type": QuestionType.GAP_FILL,
            "content": {
                "part": 1,
                "notes_id": "p1_general",
                "gap_key": "9",
                "notes": PART1_NOTES,
            },
            "answer_key": {"correct": "videos"},
        },
        {
            "order": 10,
            "question_type": QuestionType.GAP_FILL,
            "content": {
                "part": 1,
                "notes_id": "p1_general",
                "gap_key": "10",
                "notes": PART1_NOTES,
            },
            "answer_key": {"correct": "lockers"},
        },
    ],

    # ── PART 2 — MCQ 3-option (Q11-16) + matching-dropdown (Q17-20) ─────────
    2: [
        {
            "order": 11,
            "question_type": QuestionType.MCQ,
            "content": {
                "part": 2,
                "section_title": "Working as a makeup trainee",
                "question": "What should trainees always expect to get when working on low-budget short films?",
                "options": ["A. travel expenses", "B. a minimum wage", "C. meals"],
            },
            "answer_key": {"correct": "A. travel expenses"},
        },
        {
            "order": 12,
            "question_type": QuestionType.MCQ,
            "content": {
                "part": 2,
                "question": "According to the speaker, on big-budget films trainees may get experience of",
                "options": [
                    "A. makeup for special effects",
                    "B. working with different ethnicities",
                    "C. creating a variety of hair styles",
                ],
            },
            "answer_key": {"correct": "B. working with different ethnicities"},
        },
        {
            "order": 13,
            "question_type": QuestionType.MCQ,
            "content": {
                "part": 2,
                "question": "The speaker says a problem for makeup artists is",
                "options": [
                    "A. dealing with difficult directors",
                    "B. being shouted at by their supervisor",
                    "C. waiting around for hours doing nothing",
                ],
            },
            "answer_key": {"correct": "C. waiting around for hours doing nothing"},
        },
        {
            "order": 14,
            "question_type": QuestionType.MCQ,
            "content": {
                "part": 2,
                "question": "How did the speaker feel when she met famous actors for the first time?",
                "options": ["A. very shy", "B. very proud", "C. very disappointed"],
            },
            "answer_key": {"correct": "A. very shy"},
        },
        {
            "order": 15,
            "question_type": QuestionType.MCQ,
            "content": {
                "part": 2,
                "question": "What advice does the speaker give about makeup kits?",
                "options": [
                    "A. Always carry a basic kit with you",
                    "B. Only buy the best products for a makeup kit",
                    "C. Ask other makeup artists to check your kit",
                ],
            },
            "answer_key": {"correct": "A. Always carry a basic kit with you"},
        },
        {
            "order": 16,
            "question_type": QuestionType.MCQ,
            "content": {
                "part": 2,
                "question": "What advice does the speaker give about creating a portfolio?",
                "options": [
                    "A. Keep spontaneous clips and shots",
                    "B. Only include a small selection of photos",
                    "C. Get permission to use photos",
                ],
            },
            "answer_key": {"correct": "C. Get permission to use photos"},
        },
        {
            "order": 17,
            "question_type": QuestionType.MCQ,
            "content": {
                "part": 2,
                "matching_id": "p2_duties",
                "label": "Pressing an actor",
                **PART2_DUTIES,
            },
            "answer_key": {"correct": "A"},
        },
        {
            "order": 18,
            "question_type": QuestionType.MCQ,
            "content": {
                "part": 2,
                "matching_id": "p2_duties",
                "label": "Continuity",
                **PART2_DUTIES,
            },
            "answer_key": {"correct": "B"},
        },
        {
            "order": 19,
            "question_type": QuestionType.MCQ,
            "content": {
                "part": 2,
                "matching_id": "p2_duties",
                "label": "General",
                **PART2_DUTIES,
            },
            "answer_key": {"correct": "C"},
        },
        {
            "order": 20,
            "question_type": QuestionType.MCQ,
            "content": {
                "part": 2,
                "matching_id": "p2_duties",
                "label": "Shade documentation",
                **PART2_DUTIES,
            },
            "answer_key": {"correct": "A"},
        },
    ],

    # ── PART 3 — Choose-TWO pairs (Q21-24) + matching-dropdown (Q25-30) ─────
    3: [
        {
            "order": 21,
            "question_type": QuestionType.MULTI_SELECT,
            "content": {
                "part": 3,
                "pair_id": "p3_features",
                **PART3_FEATURES_PAIR,
            },
            "answer_key": {"correct": "B"},
        },
        {
            "order": 22,
            "question_type": QuestionType.MULTI_SELECT,
            "content": {
                "part": 3,
                "pair_id": "p3_features",
                **PART3_FEATURES_PAIR,
            },
            "answer_key": {"correct": "D"},
        },
        {
            "order": 23,
            "question_type": QuestionType.MULTI_SELECT,
            "content": {
                "part": 3,
                "pair_id": "p3_project",
                **PART3_PROJECT_PAIR,
            },
            "answer_key": {"correct": "C"},
        },
        {
            "order": 24,
            "question_type": QuestionType.MULTI_SELECT,
            "content": {
                "part": 3,
                "pair_id": "p3_project",
                **PART3_PROJECT_PAIR,
            },
            "answer_key": {"correct": "D"},
        },
        {
            "order": 25,
            "question_type": QuestionType.MCQ,
            "content": {
                "part": 3,
                "matching_id": "p3_opinions",
                "label": "Article on invasive lionfish",
                **PART3_OPINIONS,
            },
            "answer_key": {"correct": "F"},
        },
        {
            "order": 26,
            "question_type": QuestionType.MCQ,
            "content": {
                "part": 3,
                "matching_id": "p3_opinions",
                "label": "Documentary on microplastics",
                **PART3_OPINIONS,
            },
            "answer_key": {"correct": "A"},
        },
        {
            "order": 27,
            "question_type": QuestionType.MCQ,
            "content": {
                "part": 3,
                "matching_id": "p3_opinions",
                "label": "Podcast on ocean pollution",
                **PART3_OPINIONS,
            },
            "answer_key": {"correct": "B"},
        },
        {
            "order": 28,
            "question_type": QuestionType.MCQ,
            "content": {
                "part": 3,
                "matching_id": "p3_opinions",
                "label": "Book on coastal ecosystems",
                **PART3_OPINIONS,
            },
            "answer_key": {"correct": "C"},
        },
        {
            "order": 29,
            "question_type": QuestionType.MCQ,
            "content": {
                "part": 3,
                "matching_id": "p3_opinions",
                "label": "Article on marine toxicity",
                **PART3_OPINIONS,
            },
            "answer_key": {"correct": "D"},
        },
        {
            "order": 30,
            "question_type": QuestionType.MCQ,
            "content": {
                "part": 3,
                "matching_id": "p3_opinions",
                "label": "Podcast on floating marine cities",
                **PART3_OPINIONS,
            },
            "answer_key": {"correct": "H"},
        },
    ],

    # ── PART 4 — Notes-card with sub-headings (Q31-40) ────────────────────────
    4: [
        {
            "order": 31,
            "question_type": QuestionType.GAP_FILL,
            "content": {
                "part": 4,
                "notes_id": "p4_rubber",
                "gap_key": "31",
                "notes": PART4_NOTES,
                "instruction": "Complete the notes below.\nWrite ONE WORD ONLY for each answer.",
            },
            "answer_key": {"correct": "steel"},
        },
        {
            "order": 32,
            "question_type": QuestionType.GAP_FILL,
            "content": {
                "part": 4,
                "notes_id": "p4_rubber",
                "gap_key": "32",
                "notes": PART4_NOTES,
            },
            "answer_key": {"correct": "slow"},
        },
        {
            "order": 33,
            "question_type": QuestionType.GAP_FILL,
            "content": {
                "part": 4,
                "notes_id": "p4_rubber",
                "gap_key": "33",
                "notes": PART4_NOTES,
            },
            "answer_key": {"correct": "demand"},
        },
        {
            "order": 34,
            "question_type": QuestionType.GAP_FILL,
            "content": {
                "part": 4,
                "notes_id": "p4_rubber",
                "gap_key": "34",
                "notes": PART4_NOTES,
            },
            "answer_key": {"correct": "equator"},
        },
        {
            "order": 35,
            "question_type": QuestionType.GAP_FILL,
            "content": {
                "part": 4,
                "notes_id": "p4_rubber",
                "gap_key": "35",
                "notes": PART4_NOTES,
            },
            "answer_key": {"correct": "store"},
        },
        {
            "order": 36,
            "question_type": QuestionType.GAP_FILL,
            "content": {
                "part": 4,
                "notes_id": "p4_rubber",
                "gap_key": "36",
                "notes": PART4_NOTES,
            },
            "answer_key": {"correct": ["fungus", "fungal"]},
        },
        {
            "order": 37,
            "question_type": QuestionType.GAP_FILL,
            "content": {
                "part": 4,
                "notes_id": "p4_rubber",
                "gap_key": "37",
                "notes": PART4_NOTES,
            },
            "answer_key": {"correct": "weather"},
        },
        {
            "order": 38,
            "question_type": QuestionType.GAP_FILL,
            "content": {
                "part": 4,
                "notes_id": "p4_rubber",
                "gap_key": "38",
                "notes": PART4_NOTES,
            },
            "answer_key": {"correct": "durable"},
        },
        {
            "order": 39,
            "question_type": QuestionType.GAP_FILL,
            "content": {
                "part": 4,
                "notes_id": "p4_rubber",
                "gap_key": "39",
                "notes": PART4_NOTES,
            },
            "answer_key": {"correct": "roots"},
        },
        {
            "order": 40,
            "question_type": QuestionType.GAP_FILL,
            "content": {
                "part": 4,
                "notes_id": "p4_rubber",
                "gap_key": "40",
                "notes": PART4_NOTES,
            },
            "answer_key": {"correct": "soil"},
        },
    ],
}


PART_META = {
    1: {
        "order": 1,
        "audio_file": "listening_part1.mp3",
        "script": PART1_SCRIPT,
        "passage_title": "Part 1 — Oyster Bay Sailing Club Enquiry",
        "duration": 40,
    },
    2: {
        "order": 2,
        "audio_file": "listening_part2.mp3",
        "script": PART2_SCRIPT,
        "passage_title": "Part 2 — Working as a Makeup Trainee",
        "duration": 40,
    },
    3: {
        "order": 3,
        "audio_file": "listening_part3.mp3",
        "script": PART3_SCRIPT,
        "passage_title": "Part 3 — Marine Biodiversity Discussion",
        "duration": 40,
    },
    4: {
        "order": 4,
        "audio_file": "listening_part4.mp3",
        "script": PART4_SCRIPT,
        "passage_title": "Part 4 — Sources of Rubber (Lecture)",
        "duration": 40,
    },
}


def script_to_passage(script: list[tuple[str, str]]) -> str:
    """Convert [(voice, text), ...] to a readable audioscript."""
    speaker_map = {
        "en-GB-SoniaNeural": "Sarah (Club Administrator)",
        "en-GB-RyanNeural": "Caller / Student / Lecturer",
        "en-AU-NatashaNeural": "Natasha (Student)",
    }
    lines = []
    for voice, text in script:
        speaker = speaker_map.get(voice, voice)
        lines.append(f"[{speaker}]: {text}")
    return "\n\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
#  DB seeding
# ─────────────────────────────────────────────────────────────────────────────

async def main() -> None:
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Find test
        result = await session.execute(select(Test).where(Test.title == TEST_TITLE))
        test = result.scalar_one_or_none()
        if test is None:
            print(f"ERROR: Test '{TEST_TITLE}' not found in DB.")
            return

        print(f"Found test: {test.title} (id={test.id})")

        # Delete only the listening sections that we're going to regenerate
        result = await session.execute(
            select(Section).where(
                Section.test_id == test.id,
                Section.type == SectionType.LISTENING,
            )
        )
        existing = result.scalars().all()
        deleted = 0
        for sec in existing:
            if sec.order not in PARTS_TO_SEED:
                continue  # leave other parts untouched
            await session.execute(
                delete(Question).where(Question.section_id == sec.id)
            )
            await session.delete(sec)
            deleted += 1
        await session.flush()
        print(f"Deleted {deleted} existing Listening section(s) for parts {sorted(PARTS_TO_SEED)}.")

        # Generate audio + create sections + questions (only for PARTS_TO_SEED)
        for part_num, meta in PART_META.items():
            if part_num not in PARTS_TO_SEED:
                print(f"\n[PART {part_num}] Skipping (not in PARTS_TO_SEED).")
                continue
            audio_path = MEDIA_DIR / meta["audio_file"]
            print(f"\n[PART {part_num}] Generating audio -> {audio_path.name} ...")
            await generate_audio(meta["script"], audio_path)

            passage_text = script_to_passage(meta["script"])

            section = Section(
                id=uuid.uuid4(),
                test_id=test.id,
                type=SectionType.LISTENING,
                order=meta["order"],
                duration_minutes=meta["duration"],
                audio_url=f"/media/{meta['audio_file']}",
                passage=passage_text,
            )
            session.add(section)
            await session.flush()  # get section.id

            for q_data in QUESTIONS[part_num]:
                q = Question(
                    id=uuid.uuid4(),
                    section_id=section.id,
                    question_type=q_data["question_type"],
                    order=q_data["order"],
                    content=q_data["content"],
                    answer_key=q_data["answer_key"],
                )
                session.add(q)

            print(
                f"  OK  Section created (id={section.id}), "
                f"{len(QUESTIONS[part_num])} questions added."
            )

        await session.commit()
        print(f"\nDONE  Seeded parts {sorted(PARTS_TO_SEED)} successfully.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
