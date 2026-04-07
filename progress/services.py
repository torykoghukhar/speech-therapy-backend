"""
Services for analyzing pronunciation using Azure Speech service.
"""

import logging
import os
import re
import tempfile
from difflib import SequenceMatcher

import torch
import librosa
from pydub import AudioSegment
from transformers import Wav2Vec2Processor, Wav2Vec2Model
import azure.cognitiveservices.speech as speechsdk

from django.conf import settings

logger = logging.getLogger(__name__)

processor = Wav2Vec2Processor.from_pretrained("facebook/wav2vec2-base")
model = Wav2Vec2Model.from_pretrained("facebook/wav2vec2-base")


def get_embedding(audio_path):
    """
    Get Wav2Vec2 embedding for an audio file.
    """
    speech, _ = librosa.load(audio_path, sr=16000)

    inputs = processor(speech, sampling_rate=16000, return_tensors="pt")

    with torch.no_grad():
        outputs = model(**inputs)

    embedding = outputs.last_hidden_state.mean(dim=1)

    return embedding


def wav2vec_similarity(user_path, ref_path):
    """
    Calculate similarity between two audio files using Wav2Vec2 embeddings.
    """
    emb1 = get_embedding(user_path)
    emb2 = get_embedding(ref_path)

    v1 = emb1.flatten()
    v2 = emb2.flatten()

    similarity = torch.dot(v1, v2) / (
        torch.norm(v1) * torch.norm(v2)
    )

    return round(float(similarity.item() * 100), 2)


def compute_wav2vec_score(wav_path, reference_audio_path):
    """
    Compute the Wav2Vec2 similarity score between a user's audio and a reference audio.
    """
    if reference_audio_path and os.path.exists(reference_audio_path):
        try:
            score = wav2vec_similarity(wav_path, reference_audio_path)
            logger.info("WAV2VEC SCORE: %s", score)
            return score
        except Exception as e:  # pylint: disable=broad-except
            logger.warning("WAV2VEC ERROR: %s", str(e))
            return 0

    logger.warning("No reference audio for WAV2VEC")
    return 0


def normalize_sound_text(text):
    """
    Normalize sound expressions like:
    "мяу-мяу" → "мяу мяу"
    "мяу  мяу" → "мяу мяу"
    """
    text = text.lower()

    text = text.replace("-", " ")
    text = re.sub(r"\s+", " ", text).strip()

    return text


def phoneme_analysis(expected, recognized):
    """
    Analyze phoneme-level differences between expected and recognized text.
    """
    result = []
    errors = []

    for i, char in enumerate(expected):
        actual = recognized[i] if i < len(recognized) else ""

        is_error = char != actual

        result.append({
            "expected": char,
            "actual": actual,
            "is_error": is_error
        })

        if is_error:
            if char.strip() and char.isalpha():
                errors.append(char)

    return result, list(set(errors))


def analyze_pronunciation(audio_path: str, reference_text: str):
    """
    Analyze pronunciation using Azure Speech service.
    """

    logger.info("ANALYZE START")
    logger.info("Audio path: %s", audio_path)
    logger.info("Reference text: %s", reference_text)

    try:
        speech_config = speechsdk.SpeechConfig(
            subscription=settings.AZURE_SPEECH_KEY,
            region=settings.AZURE_SPEECH_REGION,
        )

        audio_config = speechsdk.audio.AudioConfig(filename=audio_path)

        recognizer_plain = speechsdk.SpeechRecognizer(
            speech_config=speech_config,
            audio_config=audio_config,
            language="uk-UA",
        )

        stt_result = recognizer_plain.recognize_once()

        recognized_text = stt_result.text.lower().strip()

        recognized_text = re.sub(r"[^\w\s]", "", recognized_text).strip()

        logger.info("PURE STT: %s", recognized_text)

        if not recognized_text:
            logger.warning("Empty STT → fallback to pronunciation only")

            pronunciation_config = speechsdk.PronunciationAssessmentConfig(
                reference_text=reference_text,
                grading_system=speechsdk.PronunciationAssessmentGradingSystem.HundredMark,
                granularity=speechsdk.PronunciationAssessmentGranularity.Phoneme,
                enable_miscue=True,
            )

            recognizer = speechsdk.SpeechRecognizer(
                speech_config=speech_config,
                audio_config=audio_config,
                language="uk-UA",
            )

            pronunciation_config.apply_to(recognizer)

            result = recognizer.recognize_once()

            pronunciation_result = speechsdk.PronunciationAssessmentResult(result)

            return {
                "accuracy": pronunciation_result.accuracy_score,
                "fluency": pronunciation_result.fluency_score,
                "completeness": pronunciation_result.completeness_score,
                "recognized_text": "",
            }

        pronunciation_config = speechsdk.PronunciationAssessmentConfig(
            reference_text=reference_text,
            grading_system=speechsdk.PronunciationAssessmentGradingSystem.HundredMark,
            granularity=speechsdk.PronunciationAssessmentGranularity.Phoneme,
            enable_miscue=True,
        )

        recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config,
            audio_config=audio_config,
            language="uk-UA",
        )

        pronunciation_config.apply_to(recognizer)

        result = recognizer.recognize_once()

        logger.info("Azure result reason: %s", result.reason)

        if result.reason != speechsdk.ResultReason.RecognizedSpeech:
            logger.warning("Speech not recognized")
            return {
                "accuracy": 0,
                "fluency": 0,
                "completeness": 0,
                "recognized_text": recognized_text,
            }

        pronunciation_result = speechsdk.PronunciationAssessmentResult(result)

        logger.info("Pronunciation accuracy: %s", pronunciation_result.accuracy_score)

        return {
            "accuracy": pronunciation_result.accuracy_score,
            "fluency": pronunciation_result.fluency_score,
            "completeness": pronunciation_result.completeness_score,
            "recognized_text": recognized_text,
        }

    except Exception as e:  # pylint: disable=broad-except
        logger.error("ERROR: %s", str(e))
        return {
            "accuracy": 0,
            "fluency": 0,
            "completeness": 0,
            "recognized_text": "",
        }


def calculate_final_score(
    exercise_type,
    recognized,
    similarity,
    azure_score,
    wav2vec_score,
):
    """
    Calculate final accuracy score based on exercise type and analysis results.
    """
    text_score = similarity * 100

    logger.info("EXERCISE TYPE: %s", exercise_type)

    if exercise_type == "word":

        if not recognized:
            logger.warning("EMPTY RECOGNIZED → fallback (word)")
            return 0.6 * azure_score + 0.4 * wav2vec_score

        if similarity < 0.6:
            logger.warning("WRONG WORD DETECTED")
            return similarity * 40

        return (
            0.6 * azure_score +
            0.3 * text_score +
            0.1 * wav2vec_score
        )

    if exercise_type == "sound":

        logger.info("SOUND MODE SCORING")

        if not recognized:
            logger.warning("EMPTY RECOGNIZED → fallback (sound)")
            return wav2vec_score

        return (
            0.6 * wav2vec_score +
            0.4 * text_score
        )

    logger.warning("UNKNOWN TYPE → fallback")
    return text_score


def calculate_accuracy_from_audio(
    audio_file, reference_text,
    reference_audio_path,
    exercise_type
):  # pylint: disable=too-many-locals
    """
    Saves audio temporarily and calculates pronunciation accuracy.
    """

    if not audio_file:
        logger.warning("No audio file provided")
        return {
            "accuracy": 0,
            "fluency": 0,
            "completeness": 0,
        }

    logger.info("FILE RECEIVED: %s", audio_file.name)
    logger.info("FILE TYPE: %s", audio_file.content_type)

    webm_path = None
    wav_path = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
            for chunk in audio_file.chunks():
                tmp.write(chunk)
            webm_path = tmp.name

        logger.info("WEBM SAVED: %s", webm_path)

        wav_path = webm_path.replace(".webm", ".wav")

        audio = AudioSegment.from_file(webm_path, format="webm")
        audio = audio.set_frame_rate(16000).set_channels(1)
        audio.export(wav_path, format="wav")
        logger.info("CONVERTED TO WAV: %s", wav_path)

        analysis = analyze_pronunciation(wav_path, reference_text)
        logger.info("ANALYSIS RESULT: %s", analysis)

        recognized = analysis.get("recognized_text", "").lower().strip()
        expected = reference_text.lower().strip()

        if exercise_type == "sound":
            recognized = normalize_sound_text(recognized)
            expected = normalize_sound_text(expected)

        logger.info("NORMALIZED EXPECTED: %s", expected)
        logger.info("NORMALIZED RECOGNIZED: %s", recognized)

        similarity = SequenceMatcher(None, recognized, expected).ratio()
        logger.info("SIMILARITY: %s", similarity)

        azure_score = analysis.get("accuracy", 0)

        phoneme_details, weak_phonemes = phoneme_analysis(expected, recognized)

        logger.info("PHONEME DETAILS: %s", phoneme_details)
        logger.info("WEAK PHONEMES: %s", weak_phonemes)

        wav2vec_score = compute_wav2vec_score(
            wav_path,
            reference_audio_path,
        )

        final_score = calculate_final_score(
            exercise_type,
            recognized,
            similarity,
            azure_score,
            wav2vec_score,
        )

        logger.info("FINAL SCORE: %s", final_score)

        return {
            "accuracy": round(final_score, 2),
            "wav2vec_score": wav2vec_score,
            "azure_score": azure_score,
            "similarity": round(similarity, 2),
            "recognized_text": recognized,
            "fluency": analysis.get("fluency", 0),
            "completeness": analysis.get("completeness", 0),
            "phoneme_analysis": phoneme_details,
            "weak_phonemes": weak_phonemes,
        }

    except Exception as e:  # pylint: disable=broad-except
        logger.error("ERROR: %s", str(e))
        return {
            "accuracy": 0,
            "fluency": 0,
            "completeness": 0,
        }

    finally:
        if webm_path and os.path.exists(webm_path):
            os.remove(webm_path)
            logger.info("WEBM REMOVED: %s", webm_path)

        if wav_path and os.path.exists(wav_path):
            os.remove(wav_path)
            logger.info("WAV REMOVED: %s", wav_path)
