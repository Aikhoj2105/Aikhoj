import os
import json
import time
import urllib.request
import urllib.parse
import urllib.error


MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")

MAX_RETRIES = 3
INITIAL_BACKOFF = 2


def _get_api_key():
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY नहीं मिला. "
            "पहले environment variable set करें."
        )

    return api_key


def _build_url():
    api_key = _get_api_key()

    return (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{MODEL}:generateContent"
        f"?key={urllib.parse.quote(api_key)}"
    )


def _extract_text(result):
    try:
        return result["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError):
        raise RuntimeError(
            "Gemini से expected response नहीं मिला:\n"
            + json.dumps(result, indent=2, ensure_ascii=False)
        )


def _generate(prompt, timeout=120, temperature=None, response_mime_type=None):
    payload = {
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

    generation_config = {}

    if temperature is not None:
        generation_config["temperature"] = temperature

    if response_mime_type:
        generation_config["responseMimeType"] = response_mime_type

    if generation_config:
        payload["generationConfig"] = generation_config

    data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        _build_url(),
        data=data,
        headers={
            "Content-Type": "application/json"
        },
        method="POST"
    )

    last_error = None

    for attempt in range(MAX_RETRIES + 1):
        try:
            with urllib.request.urlopen(
                request,
                timeout=timeout
            ) as response:

                result = json.loads(
                    response.read().decode("utf-8")
                )

            return result

        except urllib.error.HTTPError as e:
            error_body = e.read().decode(
                "utf-8",
                errors="ignore"
            )

            last_error = RuntimeError(
                f"Gemini API HTTP {e.code}: {error_body}"
            )

            # Retry only temporary/rate-limit errors.
            if e.code not in (429, 500, 502, 503, 504):
                raise last_error

            if attempt >= MAX_RETRIES:
                raise last_error

            wait_time = INITIAL_BACKOFF * (2 ** attempt)

            print(
                f"⚠️ Gemini HTTP {e.code}. "
                f"Retry {attempt + 1}/{MAX_RETRIES} "
                f"in {wait_time}s..."
            )

            time.sleep(wait_time)

        except urllib.error.URLError as e:
            last_error = RuntimeError(
                f"Network error: {e.reason}"
            )

            if attempt >= MAX_RETRIES:
                raise last_error

            wait_time = INITIAL_BACKOFF * (2 ** attempt)

            print(
                f"⚠️ Network error. "
                f"Retry {attempt + 1}/{MAX_RETRIES} "
                f"in {wait_time}s..."
            )

            time.sleep(wait_time)

        except TimeoutError as e:
            last_error = RuntimeError(
                f"Gemini request timeout: {e}"
            )

            if attempt >= MAX_RETRIES:
                raise last_error

            wait_time = INITIAL_BACKOFF * (2 ** attempt)

            print(
                f"⚠️ Timeout. "
                f"Retry {attempt + 1}/{MAX_RETRIES} "
                f"in {wait_time}s..."
            )

            time.sleep(wait_time)

    raise last_error or RuntimeError("Gemini request failed.")


def generate_text(prompt, timeout=120, temperature=None):
    """
    Send a text prompt to Gemini and return generated text.
    """

    result = _generate(
        prompt=prompt,
        timeout=timeout,
        temperature=temperature
    )

    return _extract_text(result)


def generate_json(prompt, timeout=120, temperature=None):
    """
    Send a prompt to Gemini and request a JSON response.
    Returns the JSON response as text.
    """

    result = _generate(
        prompt=prompt,
        timeout=timeout,
        temperature=temperature,
        response_mime_type="application/json"
    )

    return _extract_text(result)
