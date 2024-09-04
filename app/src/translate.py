from deep_translator import GoogleTranslator
import src.variables as variables
import threading
import unidecode
import json
import time
import os


TRANSLATING = False


def Initialize():
    global translator
    languages = GetAvailableLanguages()
    language_is_valid = False
    for language in languages:
        if str(languages[language]) == str(variables.LANGUAGE):
            language_is_valid = True
            break
    if language_is_valid == False:
        variables.LANGUAGE = "en"
    translator = GoogleTranslator(source="en", target=variables.LANGUAGE)

    if os.path.exists(f"{variables.PATH}cache/Translations/{variables.LANGUAGE}.json"):
        with open(f"{variables.PATH}cache/Translations/{variables.LANGUAGE}.json", "r") as f:
            try:
                file = json.load(f)
            except:
                file = {}
                with open(f"{variables.PATH}cache/Translations/{variables.LANGUAGE}.json", "w") as f:
                    json.dump({}, f, indent=4)
            variables.TRANSLATION_CACHE = file


def TranslateThread(text):
    global TRANSLATING
    while TRANSLATING:
        time.sleep(0.1)
    TRANSLATING = True
    variables.POPUP = ["Translating...", 0, 0.5]
    translation = translator.translate(text)
    variables.TRANSLATION_CACHE[text] =  unidecode.unidecode(translation)
    TRANSLATING = False
    return translation


def TranslationRequest(text):
    threading.Thread(target=TranslateThread, args=(text,), daemon=True).start()


def Translate(text):
    if variables.LANGUAGE == "en":
        return text
    elif text in variables.TRANSLATION_CACHE:
        translation = variables.TRANSLATION_CACHE[text]
        return translation
    elif TRANSLATING:
        return text
    else:
        if text != "":
            TranslationRequest(text)
        return text


def GetAvailableLanguages():
    languages = GoogleTranslator().get_supported_languages(as_dict=True)
    formatted_languages = {}
    for language in languages:
        formatted_language = ""
        for i, part in enumerate(str(language).split("(")):
            formatted_language += ("(" if i > 0 else "") + part.capitalize()
        formatted_languages[formatted_language] = languages[language]
    return formatted_languages


def SaveCache():
    if variables.LANGUAGE != "en":
        if os.path.exists(f"{variables.PATH}cache/Translations") == False:
            os.makedirs(f"{variables.PATH}cache/Translations")
        with open(f"{variables.PATH}cache/Translations/{variables.LANGUAGE}.json", "w") as f:
            json.dump(variables.TRANSLATION_CACHE, f, indent=4)