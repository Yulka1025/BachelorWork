from django.conf import settings
from openai import OpenAI


class OpenAITMenuConsultant:
    """
    A class to handle translation of dictionary content using OpenAI's API.

    Attributes:
        api_key (str): The API key for accessing OpenAI services.
        client (OpenAI): The OpenAI client instance.
    """

    def __init__(
        self,
        user_message: str,
    ):
        """
        Initializes the OpenAITranslator with the given API key and languages.

        Args:
            api_key (str): The API key for accessing OpenAI services.
        """
        self.user_message = user_message
        self.client = OpenAI(api_key=settings.OPENAI_API_TOKEN)

    def translate_dict(self, input_dict: dict) -> dict:
        """
        Translates the values of a dictionary from the source language to the target language.

        Args:
            input_dict (dict): The dictionary with string values to be translated.

        Returns:
            dict: A dictionary with translated values.
        """
        items = [
            f"{key}: {value}"
            for key, value in input_dict.items()
            if isinstance(value, str)
        ]
        text_to_translate = "\n".join(items)

        translated_text = self._translate_text(text_to_translate)

        translated_lines = translated_text.split("\n")
        translated_dict = {}
        for line in translated_lines:
            if ": " in line:
                key, value = line.split(": ", 1)
                translated_dict[key] = value
            else:
                print(f"Warning: Could not parse line: {line}")

        for key, value in input_dict.items():
            if key not in translated_dict:
                translated_dict[key] = value

        return translated_dict

    def _translate_text(self, text: str) -> str:
        """
        Translates a given text from the source language to the target language using OpenAI's API.

        Args:
            text (str): The text to be translated.

        Returns:
            str: The translated text.
        """
        try:
            prompt = (
                f"Ти онлайн консультант по меню в онлайн доставці їжі."
                f"я буду надавати тобі наші страви і напої у вигляді а ти будеш відповідати на питання про них або надавати рекомендації про них"
                f"Якщо тобі пишуть з інщою метою там маєш відмовитись"
            )

            completion = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "Ти консультант по меню в онлайн доставці їжі.",
                    },
                    {"role": "user", "content": prompt},
                ],
            )

            return dict(completion.choices[0].message).get("content", text)
        except Exception as e:
            print(f"Error during translation: {e}")
            return text
