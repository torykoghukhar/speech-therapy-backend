"""
Services for analyzing pronunciation using Azure Speech service.
"""

import logging
import os
import re
import tempfile
from difflib import SequenceMatcher
import azure.cognitiveservices.speech as speechsdk
from pydub import AudioSegment
from django.conf import settings

logger = logging.getLogger(__name__)


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


def calculate_accuracy_from_audio(audio_file, reference_text):
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

        logger.info("EXPECTED: %s", expected)
        logger.info("RECOGNIZED: %s", recognized)

        similarity = SequenceMatcher(None, recognized, expected).ratio()

        logger.info("SIMILARITY: %s", similarity)

        phoneme_score = analysis.get("accuracy", 0)

        final_score = phoneme_score * similarity

        logger.info("FINAL SCORE: %s", final_score)

        return {
            "accuracy": round(final_score, 2),
            "raw_accuracy": phoneme_score,
            "similarity": round(similarity, 2),
            "recognized_text": recognized,
            "fluency": analysis.get("fluency", 0),
            "completeness": analysis.get("completeness", 0),
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
