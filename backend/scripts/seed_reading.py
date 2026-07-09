"""
Seed Reading passages 2 and 3 into IELTS Academic Mock #1.

Usage:
    cd backend
    python scripts/seed_reading.py
"""

import asyncio
import sys
import uuid
from pathlib import Path

# Allow importing from app/
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.models.question import Question, QuestionType
from app.models.section import Section, SectionType
from app.models.test import Test

DATABASE_URL = "postgresql+asyncpg://postgres:2770@localhost:5432/ielts_mock"
TEST_TITLE = "IELTS Academic Mock #1"

# ── Passage texts ─────────────────────────────────────────────────────────────

PASSAGE_2_TEXT = """\
The History of Chocolate

A. The story of chocolate begins more than three thousand years ago in the tropical rainforests of Mesoamerica. The ancient Maya civilisation cultivated the cacao tree, known scientifically as Theobroma cacao, and regarded its beans as possessing almost supernatural qualities. Archaeological evidence from Maya sites suggests that cacao was consumed as early as 1900 BCE, initially in the form of a fermented beverage made from the pulp of the cacao fruit rather than the beans themselves. The Maya considered cacao a divine gift, and it featured prominently in their religious ceremonies and mythology.

B. Beyond its spiritual significance, cacao beans served a remarkably practical economic function in Maya society. The beans were used as a form of currency, accepted in trade transactions throughout the region. Historical accounts describe merchants counting out beans to pay for goods, and it is recorded that a rabbit could be purchased for ten beans, while the services of a porter for a day cost one hundred beans. This dual role of cacao as both sacred substance and monetary unit elevated its status considerably within Mesoamerican cultures, a position it would maintain through the subsequent Aztec civilisation.

C. When Spanish conquistadors arrived in Mexico in the early sixteenth century, they encountered the Aztec emperor Montezuma II consuming prodigious quantities of a bitter cacao beverage called xocolatl. Hernán Cortés and his soldiers initially found the drink unpalatable, but they recognised its commercial potential. By the 1580s, cacao beans and the knowledge of how to process them had been transported to Spain, where the drink was modified by the addition of sugar, vanilla, and cinnamon to suit European preferences. For nearly a century, Spain managed to keep the existence of chocolate largely secret from the rest of Europe, giving it a significant economic advantage in the growing trade.

D. The introduction of sugar proved transformative for chocolate's appeal across Europe. As sugar became increasingly available from Caribbean plantations throughout the seventeenth century, sweetened chocolate drinks spread rapidly among the aristocracy and wealthy classes. Chocolate houses emerged in London, Amsterdam, and Paris as fashionable meeting places where the drink was consumed and business conducted. The beverage's reputation as a health tonic—physicians of the era claimed it aided digestion, strengthened the heart, and restored vigour—further accelerated its popularity among those who could afford it.

E. The transition from liquid to solid chocolate represented a revolutionary development in the nineteenth century. In 1828, the Dutch chemist Coenraad van Houten invented a hydraulic press that could separate cacao butter from the roasted cacao beans, producing a dry powder that mixed more easily with water. This process, known as Dutching, made chocolate far more versatile. Then in 1875, the Swiss chocolatier Daniel Peter successfully combined cacao with condensed milk that had been developed by his neighbour Henri Nestlé, thereby creating the first commercially viable milk chocolate. The smoother, sweeter product proved enormously popular and laid the foundation for the modern confectionery industry.

F. Today, cacao cultivation is concentrated primarily in West Africa, with Côte d'Ivoire and Ghana together accounting for approximately sixty per cent of the world's supply. The global chocolate industry generates revenues exceeding one hundred billion dollars annually, yet the farmers who grow the cacao typically receive only a tiny fraction of this value. Studies have repeatedly documented the prevalence of poverty among cacao-farming communities, and investigations have uncovered the use of child labour on numerous plantations. Corporations and governments have pledged to address these issues through certification schemes and fair-trade programmes, but critics argue that systemic change remains elusive.

G. The relationship between chocolate and human health has been the subject of considerable scientific investigation and public debate. Research has identified flavanols in dark chocolate as compounds with potential cardiovascular benefits, including the reduction of blood pressure and improvement of blood flow. However, most mass-market chocolate products contain relatively low concentrations of these beneficial compounds due to processing methods that reduce their potency. Moreover, the high sugar and fat content of many chocolate products contributes to concerns about obesity and metabolic disease. The health narrative surrounding chocolate thus remains genuinely complex, defying simple characterisation as either harmful or beneficial.\
"""

PASSAGE_3_TEXT = """\
Artificial Intelligence in Healthcare

The integration of artificial intelligence into medical practice represents one of the most significant technological shifts in the history of medicine. While the relationship between computing and healthcare extends back several decades, the recent convergence of vast datasets, unprecedented computational power, and sophisticated machine learning algorithms has created capabilities that would have seemed implausible to physicians of the previous generation.

Perhaps the most immediately impactful application of artificial intelligence in medicine has been in the field of diagnostic imaging. Convolutional neural networks—a class of deep learning algorithms—have demonstrated remarkable accuracy in analysing radiological images, pathology slides, and retinal scans. In multiple independent studies, AI systems have matched or exceeded the diagnostic performance of experienced specialist physicians when identifying conditions such as diabetic retinopathy, skin malignancies, and pulmonary nodules on computed tomography scans. A landmark 2019 study published in Nature Medicine reported that a deep learning system detected breast cancer in mammograms with greater accuracy than a panel of six radiologists, reducing both false positive and false negative rates simultaneously.

The pharmaceutical industry has embraced artificial intelligence as a tool for accelerating and reducing the cost of drug discovery. Traditionally, developing a new pharmaceutical compound from initial identification to regulatory approval required fifteen to twenty years and expenditure of approximately two billion dollars, with a failure rate exceeding ninety per cent at the clinical trial stage. AI platforms can now screen billions of potential molecular structures, predict their interactions with biological targets, and identify promising candidates in a fraction of the time required by conventional approaches. During the COVID-19 pandemic, AI tools contributed to the unprecedented speed with which candidate vaccines and therapeutic agents were identified and characterised, though the actual clinical development still required conventional trial processes.

Robotic surgery, guided by artificial intelligence, has extended the precision achievable in operating theatres. Systems such as the da Vinci Surgical System allow surgeons to perform minimally invasive procedures with enhanced dexterity and visualisation, translating the surgeon's hand movements into precise robotic actions at a reduced scale. More advanced AI-assisted systems are being developed that can provide real-time guidance during procedures, alerting surgeons to anatomical structures at risk of inadvertent damage. Proponents argue that such technologies reduce complication rates and facilitate faster patient recovery, though the evidence base for improved outcomes compared with conventional laparoscopic approaches remains mixed in some surgical specialties.

Beyond these high-profile applications, artificial intelligence is being deployed across a wide range of clinical support functions. Natural language processing algorithms can extract clinically relevant information from unstructured medical records, reducing the administrative burden on healthcare professionals. Predictive models identify patients at elevated risk of deterioration, readmission, or the development of conditions such as sepsis, enabling earlier intervention. Personalised treatment algorithms analyse genomic, proteomic, and clinical data to recommend therapies tailored to individual patient characteristics rather than relying solely on population-level evidence.

The deployment of AI in healthcare raises profound ethical and regulatory questions that society is only beginning to address systematically. Issues of algorithmic bias are particularly concerning: AI systems trained predominantly on data from one demographic group may perform less effectively for patients from underrepresented populations, potentially exacerbating existing health disparities. Transparency presents another challenge, as many high-performing AI models operate as opaque black boxes whose reasoning processes cannot readily be explained to clinicians or patients. Questions of accountability when AI-assisted decisions contribute to adverse outcomes remain unresolved in most legal frameworks. Regulatory bodies including the United States Food and Drug Administration and the European Medicines Agency are actively developing frameworks for the evaluation and oversight of AI-based medical devices, but the pace of technological development creates persistent challenges for regulators.

Looking forward, researchers and clinicians express considerable optimism about the potential for AI to address fundamental limitations of current healthcare systems, including the shortage of specialist physicians in underserved regions, the cognitive burden of information overload on clinical decision-making, and the reactive rather than preventative orientation of most healthcare delivery. However, thoughtful observers caution that the translation of algorithmic performance in controlled research settings to genuine improvements in patient outcomes in complex real-world clinical environments has frequently proved more challenging than anticipated. The successful integration of artificial intelligence into healthcare will ultimately depend not only on the sophistication of the underlying technology but also on the careful design of systems that support rather than supplant the clinical judgement and human connection that remain central to effective medical care.\
"""

# ── Question data ──────────────────────────────────────────────────────────────

PASSAGE_2_QUESTIONS = [
    # ── Matching headings Q11–17 ──────────────────────────────────────────────
    {
        "order": 11,
        "question_type": QuestionType.MATCHING,
        "content": {
            "instruction": (
                "Reading Passage 2 has seven paragraphs, A–G. "
                "Choose the correct heading for each paragraph from the list of headings below."
            ),
            "headings": [
                "i. The spread of chocolate to Europe",
                "ii. Modern chocolate manufacturing",
                "iii. Ancient origins of cacao",
                "iv. The role of sugar in chocolate's popularity",
                "v. Health benefits and controversies",
                "vi. Economic impact on producing countries",
                "vii. The invention of milk chocolate",
                "viii. Chocolate as currency",
                "ix. Environmental concerns in cacao farming",
            ],
            "left": ["Paragraph A", "Paragraph B", "Paragraph C", "Paragraph D", "Paragraph E", "Paragraph F", "Paragraph G"],
            "right": [
                "i. The spread of chocolate to Europe",
                "ii. Modern chocolate manufacturing",
                "iii. Ancient origins of cacao",
                "iv. The role of sugar in chocolate's popularity",
                "v. Health benefits and controversies",
                "vi. Economic impact on producing countries",
                "vii. The invention of milk chocolate",
                "viii. Chocolate as currency",
                "ix. Environmental concerns in cacao farming",
            ],
        },
        "answer_key": {
            "answer": {
                "Paragraph A": "iii. Ancient origins of cacao",
                "Paragraph B": "viii. Chocolate as currency",
                "Paragraph C": "i. The spread of chocolate to Europe",
                "Paragraph D": "iv. The role of sugar in chocolate's popularity",
                "Paragraph E": "vii. The invention of milk chocolate",
                "Paragraph F": "vi. Economic impact on producing countries",
                "Paragraph G": "v. Health benefits and controversies",
            }
        },
    },
    # ── Gap fill Q18–22 ───────────────────────────────────────────────────────
    {
        "order": 18,
        "question_type": QuestionType.GAP_FILL,
        "content": {
            "instruction": "Complete the summary below. Choose ONE WORD ONLY from the passage for each answer.",
            "text": "The ancient Maya used cacao beans as a form of ___, accepting them in trade transactions.",
        },
        "answer_key": {"correct": "currency"},
    },
    {
        "order": 19,
        "question_type": QuestionType.GAP_FILL,
        "content": {
            "text": "When chocolate arrived in Europe, it was initially consumed as a ___ rather than eaten solid.",
        },
        "answer_key": {"correct": "drink"},
    },
    {
        "order": 20,
        "question_type": QuestionType.GAP_FILL,
        "content": {
            "text": "The addition of ___ made the drink far more appealing to European aristocratic tastes.",
        },
        "answer_key": {"correct": "sugar"},
    },
    {
        "order": 21,
        "question_type": QuestionType.GAP_FILL,
        "content": {
            "text": "In 1875, Daniel Peter created the first commercially viable ___ chocolate by combining cacao with condensed milk.",
        },
        "answer_key": {"correct": "milk"},
    },
    {
        "order": 22,
        "question_type": QuestionType.GAP_FILL,
        "content": {
            "text": "Today, the majority of the world's cacao supply is grown in ___ Africa.",
        },
        "answer_key": {"correct": "West"},
    },
    # ── MCQ Q23–24 ────────────────────────────────────────────────────────────
    {
        "order": 23,
        "question_type": QuestionType.MCQ,
        "content": {
            "question": "What does the author suggest about modern chocolate production?",
            "options": [
                "It has improved conditions for cacao farmers",
                "It relies heavily on child labour exclusively",
                "It raises both ethical and environmental questions",
                "It is declining due to health concerns",
            ],
        },
        "answer_key": {"answer": "It raises both ethical and environmental questions"},
    },
    {
        "order": 24,
        "question_type": QuestionType.MCQ,
        "content": {
            "question": "According to the passage, what made chocolate more popular across Europe in the seventeenth century?",
            "options": [
                "The invention of solid chocolate bars",
                "The availability of sugar from Caribbean plantations",
                "Spanish merchants promoting it as medicine",
                "The establishment of chocolate factories in London",
            ],
        },
        "answer_key": {"answer": "The availability of sugar from Caribbean plantations"},
    },
]

PASSAGE_3_QUESTIONS = [
    # ── True/False/Not Given Q25–30 ───────────────────────────────────────────
    {
        "order": 25,
        "question_type": QuestionType.TRUE_FALSE_NG,
        "content": {
            "statement": "AI diagnostic systems have been shown to outperform specialist physicians in identifying some medical conditions.",
        },
        "answer_key": {"correct": "True"},
    },
    {
        "order": 26,
        "question_type": QuestionType.TRUE_FALSE_NG,
        "content": {
            "statement": "Traditional drug development from discovery to approval costs approximately five billion dollars.",
        },
        "answer_key": {"correct": "False"},
    },
    {
        "order": 27,
        "question_type": QuestionType.TRUE_FALSE_NG,
        "content": {
            "statement": "The da Vinci Surgical System performs operations entirely without human surgeon involvement.",
        },
        "answer_key": {"correct": "False"},
    },
    {
        "order": 28,
        "question_type": QuestionType.TRUE_FALSE_NG,
        "content": {
            "statement": "AI models trained on data from one demographic group may perform less accurately for other populations.",
        },
        "answer_key": {"correct": "True"},
    },
    {
        "order": 29,
        "question_type": QuestionType.TRUE_FALSE_NG,
        "content": {
            "statement": "Regulatory bodies have already developed comprehensive legal frameworks for AI medical devices.",
        },
        "answer_key": {"correct": "Not Given"},
    },
    {
        "order": 30,
        "question_type": QuestionType.TRUE_FALSE_NG,
        "content": {
            "statement": "The author believes that AI will completely replace human clinical judgement in the near future.",
        },
        "answer_key": {"correct": "False"},
    },
    # ── MCQ Q31–35 ────────────────────────────────────────────────────────────
    {
        "order": 31,
        "question_type": QuestionType.MCQ,
        "content": {
            "question": "According to the passage, what was the significance of the 2019 Nature Medicine study?",
            "options": [
                "It proved that AI could replace all radiologists",
                "It showed an AI system outperformed a panel of radiologists in mammogram analysis",
                "It demonstrated that AI could diagnose any medical condition",
                "It established new regulatory standards for AI in medicine",
            ],
        },
        "answer_key": {"answer": "It showed an AI system outperformed a panel of radiologists in mammogram analysis"},
    },
    {
        "order": 32,
        "question_type": QuestionType.MCQ,
        "content": {
            "question": "What does the passage identify as a major concern regarding AI systems in healthcare?",
            "options": [
                "They are too expensive for hospitals to purchase",
                "They may perform less effectively for underrepresented patient groups",
                "They require too much training data to function",
                "They cannot be used in emergency situations",
            ],
        },
        "answer_key": {"answer": "They may perform less effectively for underrepresented patient groups"},
    },
    {
        "order": 33,
        "question_type": QuestionType.MCQ,
        "content": {
            "question": "Which of the following best describes the author's overall view of AI in healthcare?",
            "options": [
                "Unqualified enthusiasm for the technology's potential",
                "Strong opposition to its use in clinical settings",
                "Cautious optimism tempered by recognition of real challenges",
                "Indifference to whether it is adopted or not",
            ],
        },
        "answer_key": {"answer": "Cautious optimism tempered by recognition of real challenges"},
    },
    {
        "order": 34,
        "question_type": QuestionType.MCQ,
        "content": {
            "question": "What challenge do regulatory bodies face regarding AI medical devices?",
            "options": [
                "Lack of funding for research programmes",
                "Opposition from the medical profession",
                "The pace of technological change outstrips regulatory frameworks",
                "Difficulty in recruiting qualified staff",
            ],
        },
        "answer_key": {"answer": "The pace of technological change outstrips regulatory frameworks"},
    },
    {
        "order": 35,
        "question_type": QuestionType.MCQ,
        "content": {
            "question": "According to the passage, what is the traditional failure rate for pharmaceutical compounds at the clinical trial stage?",
            "options": [
                "Over fifty per cent",
                "Over seventy per cent",
                "Over eighty per cent",
                "Over ninety per cent",
            ],
        },
        "answer_key": {"answer": "Over ninety per cent"},
    },
    # ── Gap fill Q36–40 ───────────────────────────────────────────────────────
    {
        "order": 36,
        "question_type": QuestionType.GAP_FILL,
        "content": {
            "instruction": "Complete the sentences below. Choose ONE WORD ONLY from the passage for each answer.",
            "text": "AI systems that analyse medical images use ___ neural networks, a type of deep learning algorithm.",
        },
        "answer_key": {"correct": "convolutional"},
    },
    {
        "order": 37,
        "question_type": QuestionType.GAP_FILL,
        "content": {
            "text": "The traditional pharmaceutical development process has a failure rate exceeding ___ per cent at the clinical trial stage.",
        },
        "answer_key": {"correct": "ninety"},
    },
    {
        "order": 38,
        "question_type": QuestionType.GAP_FILL,
        "content": {
            "text": "Natural language processing algorithms can reduce the ___ burden on healthcare professionals by extracting information from unstructured records.",
        },
        "answer_key": {"correct": "administrative"},
    },
    {
        "order": 39,
        "question_type": QuestionType.GAP_FILL,
        "content": {
            "text": "Many high-performing AI models are described as opaque ___ whose reasoning processes cannot be explained to clinicians.",
        },
        "answer_key": {"correct": "boxes"},
    },
    {
        "order": 40,
        "question_type": QuestionType.GAP_FILL,
        "content": {
            "text": "The author argues that AI should ___ rather than replace the clinical judgement of medical professionals.",
        },
        "answer_key": {"correct": "support"},
    },
]


# ── Seed logic ────────────────────────────────────────────────────────────────

async def seed() -> None:
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Find the target test
        result = await session.execute(
            select(Test).where(Test.title == TEST_TITLE)
        )
        test = result.scalar_one_or_none()
        if test is None:
            print(f"ERROR: Test '{TEST_TITLE}' not found.")
            return
        print(f"Found test: {test.title} ({test.id})")

        # Check existing reading sections
        result = await session.execute(
            select(Section).where(
                Section.test_id == test.id,
                Section.type == SectionType.READING,
            )
        )
        existing = result.scalars().all()
        existing_orders = {s.order for s in existing}
        print(f"Existing reading sections: {len(existing)} (orders: {sorted(existing_orders)})")

        # ── Passage 2 ────────────────────────────────────────────────────────
        if 3 in existing_orders:
            print("SKIP: Passage 2 (order=3) already exists.")
        else:
            sec2 = Section(
                id=uuid.uuid4(),
                test_id=test.id,
                type=SectionType.READING,
                order=3,
                duration_minutes=20,
                passage=PASSAGE_2_TEXT,
            )
            session.add(sec2)
            await session.flush()  # get sec2.id

            for q_data in PASSAGE_2_QUESTIONS:
                q = Question(
                    id=uuid.uuid4(),
                    section_id=sec2.id,
                    order=q_data["order"],
                    question_type=q_data["question_type"],
                    content=q_data["content"],
                    answer_key=q_data.get("answer_key"),
                )
                session.add(q)

            print(f"Added Passage 2 (id={sec2.id}) with {len(PASSAGE_2_QUESTIONS)} questions (Q11–24).")

        # ── Passage 3 ────────────────────────────────────────────────────────
        if 4 in existing_orders:
            print("SKIP: Passage 3 (order=4) already exists.")
        else:
            sec3 = Section(
                id=uuid.uuid4(),
                test_id=test.id,
                type=SectionType.READING,
                order=4,
                duration_minutes=20,
                passage=PASSAGE_3_TEXT,
            )
            session.add(sec3)
            await session.flush()

            for q_data in PASSAGE_3_QUESTIONS:
                q = Question(
                    id=uuid.uuid4(),
                    section_id=sec3.id,
                    order=q_data["order"],
                    question_type=q_data["question_type"],
                    content=q_data["content"],
                    answer_key=q_data.get("answer_key"),
                )
                session.add(q)

            print(f"Added Passage 3 (id={sec3.id}) with {len(PASSAGE_3_QUESTIONS)} questions (Q25–40).")

        await session.commit()
        print("\nDone. Total reading passages should now be 3 (orders 2, 3, 4).")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
