from gemini_client import generate_text


def main():
    print("\n🧪 AI KHOJ — GEMINI CLIENT TEST")
    print("=" * 45)

    prompt = (
        "Reply with exactly this sentence: "
        "AI Khoj Gemini Client is working!"
    )

    try:
        result = generate_text(prompt)

        print("\n🤖 Gemini Response:")
        print(result)

        print("\n✅ Gemini client test successful!")

    except Exception as e:
        print("\n❌ Test failed:")
        print(e)


if __name__ == "__main__":
    main()

