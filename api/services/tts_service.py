"""Síntese de voz via Microsoft Edge TTS (gratuito, sem API key).

Usado pelo modo Live do app (voz da IA no Chrome). O Flutter Web não
consegue chamar o WebSocket da Microsoft direto (WSS retorna 403 para
Origin de browser), então o backend sintetiza e devolve o MP3.

Cache em disco por hash (texto+voz): saudações e respostas repetidas
não re-sintetizam.
"""
import asyncio
import hashlib
from pathlib import Path

import edge_tts

DEFAULT_VOICE = "pt-BR-FranciscaNeural"
MAX_CHARS = 1800

CACHE_DIR = Path(__file__).resolve().parent.parent.parent / "tts_cache"
CACHE_DIR.mkdir(exist_ok=True)


def sanitize_voice(voice: str | None) -> str:
    """Só permite vozes pt-BR Neural; qualquer outra cai na padrão."""
    if voice and voice.startswith("pt-BR-") and voice.endswith("Neural"):
        return voice
    return DEFAULT_VOICE


def _cache_key(text: str, voice: str) -> str:
    return hashlib.sha256(f"{voice}|{text}".encode("utf-8")).hexdigest()


async def _synthesize(text: str, voice: str) -> bytes:
    communicate = edge_tts.Communicate(text, voice)
    buf = bytearray()
    async for chunk in communicate.stream():
        if chunk.get("type") == "audio":
            buf += chunk.get("data", b"")
    return bytes(buf)


def synthesize_mp3(text: str, voice: str | None = None) -> bytes:
    """Retorna o MP3 (bytes). Levanta ValueError se texto vazio/sem áudio."""
    clean = (text or "").strip()
    if not clean:
        raise ValueError("Texto vazio para síntese.")
    clean = clean[:MAX_CHARS]
    voice = sanitize_voice(voice)

    cached = CACHE_DIR / f"{_cache_key(clean, voice)}.mp3"
    if cached.exists():
        return cached.read_bytes()

    audio = asyncio.run(_synthesize(clean, voice))
    if not audio:
        raise ValueError("Edge TTS não retornou áudio.")

    cached.write_bytes(audio)
    return audio
