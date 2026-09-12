import os
import glob
from datetime import datetime
from core.gemini_client import generate_text


# ============================================================
# AI KHOJ — TITLE + HOOK AGENT v1
# ============================================================




# ============================================================
# FIND LATEST RESEARCH REPORT
# ============================================================


def main():
    research_files = glob.glob("outputs/research/research_*.md")

    if not research_files:
        print("❌ Koi research report nahi mili.")
        print("Pehle Research Analyzer run karo.")
        raise SystemExit(1)

    latest_report = max(research_files, key=os.path.getmtime)

    print("🎯 AI KHOJ — TITLE + HOOK AGENT v1")
    print("=" * 55)
    print(f"📄 Latest research report:")
    print(latest_report)


    # ============================================================
    # READ RESEARCH
    # ============================================================

    try:
        with open(latest_report, "r", encoding="utf-8") as file:
            research = file.read()
    except Exception as e:
        print(f"❌ Research report read nahi ho payi: {e}")
        raise SystemExit(1)

    print(f"📊 Research characters: {len(research)}")


    # ============================================================
    # GEMINI REQUEST
    # ============================================================

    prompt = f"""
    You are the YouTube Title + Hook Agent for a Hindi/Hinglish
    faceless YouTube channel called "AI Khoj".

    Channel promise:
    "AI की वो जानकारी जो आसानी से नहीं मिलती।"

    Target audience:
    Beginners and intermediate AI users in India.

    Content focus:
    1. AI Agents
    2. Hidden / lesser-known AI tools
    3. Practical AI use cases and earning opportunities

    Your task is to convert the research report below into
    high-quality YouTube packaging.

    IMPORTANT:
    - Do NOT invent facts.
    - Use only information present in the research report.
    - Avoid misleading claims.
    - Avoid fake urgency.
    - Avoid exaggerated income promises.
    - Titles should create curiosity without becoming dishonest clickbait.
    - Language should be natural Hindi/Hinglish.
    - Keep titles suitable for a faceless YouTube channel.
    - Think like an experienced Indian YouTube creator.

    Generate exactly this structure:

    TITLE OPTIONS
    1. [title]
    2. [title]
    3. [title]
    4. [title]
    5. [title]

    For each title provide:
    - Curiosity Score: /10
    - Clickbait Risk: Low/Medium/High
    - Why it works: one short sentence

    HOOK OPTIONS
    1. [hook]
    2. [hook]
    3. [hook]

    Each hook should be suitable for the first 15–25 seconds
    of a YouTube video.

    THUMBNAIL TEXT
    1. [short text]
    2. [short text]
    3. [short text]

    BEST PACKAGE
    Best Title:
    Best Hook:
    Best Thumbnail Text:

    REASON:
    Explain in 2–3 short sentences why this combination is
    the strongest for AI Khoj.

    RESEARCH REPORT:
    ----------------
    {research}
    ----------------
    """


    try:
        output = generate_text(
            prompt,
            timeout=120
        )

    except Exception as e:
        print(f"❌ Gemini generation error: {e}")
        raise SystemExit(1)


    # ============================================================
    # SAVE OUTPUT
    # ============================================================

    output_dir = "outputs/title_hook"
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(
        output_dir,
        f"title_hook_{timestamp}.md"
    )

    header = f"""# AI Khoj — Title + Hook Report

    **Research Source:** {latest_report}

    **Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

    ---

    """

    try:
        with open(output_file, "w", encoding="utf-8") as file:
            file.write(header)
            file.write(output)
    except Exception as e:
        print(f"❌ Output save nahi ho paya: {e}")
        raise SystemExit(1)


    # ============================================================
    # DISPLAY RESULT
    # ============================================================

    print("=" * 55)
    print("✅ Title + Hook generation complete!")
    print(f"💾 Output saved to:")
    print(output_file)
    print("=" * 55)

    print("\n" + output)


if __name__ == "__main__":
    main()
