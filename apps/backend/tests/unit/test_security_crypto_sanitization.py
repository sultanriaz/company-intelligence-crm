import pytest
from app.security.crypto import encrypt_secret, decrypt_secret
from app.security.sanitization import sanitize_html_to_clean_text, sanitize_input_string


def test_aes_gcm_encryption_and_decryption_roundtrip():
    secret = "sk_live_very_secret_api_key_123456789"
    encrypted = encrypt_secret(secret)
    assert encrypted != secret
    assert len(encrypted) > 20

    decrypted = decrypt_secret(encrypted)
    assert decrypted == secret


def test_aes_gcm_empty_string():
    assert encrypt_secret("") == ""
    assert decrypt_secret("") == ""


def test_aes_gcm_tampered_ciphertext_fails():
    encrypted = encrypt_secret("my-api-key")
    # Tamper with the base64 ciphertext
    tampered = encrypted[:-2] + "=="
    with pytest.raises(ValueError, match="Failed to decrypt secret"):
        decrypt_secret(tampered)


def test_sanitize_html_removes_scripts_and_styles():
    dirty_html = """
    <html>
        <head>
            <style>body { color: red; }</style>
            <script>alert('xss');</script>
        </head>
        <body>
            <h1>Welcome to Acme Corp</h1>
            <p>We build &amp; sell cloud software.</p>
            <iframe src="https://evil.com"></iframe>
        </body>
    </html>
    """
    cleaned = sanitize_html_to_clean_text(dirty_html)
    assert "alert" not in cleaned
    assert "body { color: red; }" not in cleaned
    assert "Welcome to Acme Corp" in cleaned
    assert "We build & sell cloud software." in cleaned


def test_sanitize_html_empty_and_truncation():
    assert sanitize_html_to_clean_text("") == ""
    long_html = "<p>" + ("A" * 100) + "</p>"
    truncated = sanitize_html_to_clean_text(long_html, max_chars=50)
    assert "[Content truncated due to size limits]" in truncated


def test_sanitize_input_string_strips_control_characters():
    assert sanitize_input_string(None) == ""
    dirty = "Hello\x00World\x07!\nLine 2"
    cleaned = sanitize_input_string(dirty)
    assert "\x00" not in cleaned
    assert "\x07" not in cleaned
    assert "HelloWorld!\nLine 2" == cleaned
