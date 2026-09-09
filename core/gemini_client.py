import os
import json
import urllib.request
import urllib.parse
import urllib.error


MODEL = "gemini-3.5-flash"
API_KEY = os.getenv("GEMINI_API_KEY")

API_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"{MODEL}:generateContent"
)


def generate_text(prompt, timeout=120):
    """
    Send a text prompt to Gemini and return the generated text.
    """

    if not API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY नहीं मिला. "
            "पहले environment variable set करें."
        )

    url = f"{API_URL}?key={urllib.parse.quote(API_KEY)}"

    data = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    }

    request = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers={
            "Content-Type": "application/json"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=timeout
        ) as response:

            result = json.loads(
                response.read().decode("utf-8")
            )

    except urllib.error.HTTPError as e:
        error_body = e.read().decode(
            "utf-8",
            errors="ignore"
        )

        raise RuntimeError(
            f"Gemini API HTTP {e.code}: {error_body}"
        )

    except urllib.error.URLError as e:
        raise RuntimeError(
            f"Network error: {e.reason}"
        )

    try:
        return result["candidates"][0]["content"]["parts"][0]["text"]

    except (KeyError, IndexError, TypeError):
        raise RuntimeError(
            "Gemini से expected response नहीं मिला:\n"
            + json.dumps(result, indent=2)
        )
