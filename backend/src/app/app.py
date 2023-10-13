import yaml
import os
import logging
import tiktoken
from typing import List

from backend.src.utils.completion_messages import Messages
from backend.src.flashcard.flashcard import Flashcard
from backend.src.flashcard_deck.flashcard_deck import FlashcardDeck
from backend.src.flashcard_generator.flashcard_generator import FlashcardGenerator
from backend.src.utils.global_helpers import format_num, write_to_log_and_print
from backend.src.text_splitting import text_split

# Import custom exceptions
from backend.src.custom_exceptions.custom_exceptions import ConfigLoadingError, PromptSizeError, UnsupportedLanguageError

import yaml
import os
import logging
import tiktoken
from typing import List

from backend.src.utils.completion_messages import Messages
from backend.src.flashcard.flashcard import Flashcard
from backend.src.flashcard_deck.flashcard_deck import FlashcardDeck
from backend.src.flashcard_generator.flashcard_generator import FlashcardGenerator
from backend.src.utils.global_helpers import format_num, write_to_log_and_print, inset_into_string, read_file
from backend.src.text_splitting import text_split

# Import custom exceptions
from backend.src.custom_exceptions.custom_exceptions import ConfigLoadingError, PromptSizeError, UnsupportedLanguageError


class FlashcardApp:
    def __init__(self, config: dict):
        self.config = config
        self.backend_root_dir = backend_root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        self.model_name = "gpt-3.5-turbo"    # Default, may be changed by the program, depending on the input size.
        self.generation_mode = self.config['flashcard_generation']['mode']
        if self.generation_mode not in FlashcardGenerator.GENERATION_MODE:
            raise ConfigLoadingError(f"Invalid flashcard type: {self.generation_mode}. Expected one of {FlashcardGenerator.GENERATION_MODE}.")

        # Initialize Language of theis flashcard app
        if self.config["flashcard_generation"]["lang"] == "English":
            self.lang = "ENG"
        elif self.config["flashcard_generation"]["lang"] == "German":
            self.lang = "GER"
        else:
            raise UnsupportedLanguageError(f"The specified language '{self.config['flashcard_generation']['lang']}' is not supported or does not "
                                           f"exist.")

        # Initialize the components of the message send to the OpenAI API
        self.system_prompt = read_file(os.path.join(self.backend_root_dir, "prompt/system/generation_mode", self.generation_mode, f"{self.lang}.txt"))
        self.example_user = read_file(os.path.join(self.backend_root_dir, "prompt/example/", self.config['flashcard_generation']['example_prompt'],
                                                   self.lang,
                                                   "example_user.txt"))
        self.example_assistant = read_file(
            os.path.join(self.backend_root_dir, "prompt/example/", self.config['flashcard_generation']['example_prompt'],
                         self.lang,
                         "example_assistant.txt"))
        self.additional_prompt = read_file(
            os.path.join(self.backend_root_dir, "prompt/additional/", self.config['flashcard_generation']['additional_prompt'],
                         f"{self.lang}.txt"))

    def run(self, text_input: str):
        # TODO: Add language detection

        # Initialize flashcard generator
        flashcard_generator = FlashcardGenerator(os.getenv('OPENAI_API_KEY'), self.config["model"], self.generation_mode)

        flashcards: List[Flashcard] = []  # List to collect flashcards from each run

        prompt_limit_4k = self.config["tokens"]["4k_model"]["prompt_limit"]
        prompt_limit_16k = self.config["tokens"]["16k_model"]["prompt_limit"]

        # Initialize messages sent to the OpenAI API
        messages = Messages(
            self.system_prompt,
            self.example_user,
            self.example_assistant,
            inset_into_string(self.additional_prompt, text_input, 0)
        )
        # Calculate total prompt size
        total_prompt_size = self._calculate_total_prompt_size(messages)
        formatted_total_prompt_size = format_num(total_prompt_size)
        write_to_log_and_print(f"Total message length (calculated): {formatted_total_prompt_size} tokens")

        # Run short texts with 4k model
        if total_prompt_size < prompt_limit_4k:
            write_to_log_and_print("Using 4k model...\n")
            # Add language instructions to the text inputs
            print(f"Using gpt-3.5-turbo for total prompt size.")
            max_tokens = 4000 - prompt_limit_4k
            flashcards += flashcard_generator.generate_flashcards("gpt-3.5-turbo", messages, max_tokens)

        # TODO: Optimize parameters, plus the 16k code is buggy -.-
        # Run medium-sized texts with 16k model
        # elif total_prompt_size < prompt_limit_16k:
        #     write_to_log("Using 16k model...\n")
        #     # Add language instructions to the text inputs
        #     messages.insert_text_into_message('text_input', self.additional_prompt, 0)
        #     completion_token_limit = 16000 - prompt_limit_16k
        #     print(f"Using gpt-3.5-turbo-16k for total prompt size.")
        #     self.config["model"]["name"] = "gpt-3.5-turbo-16k"
        #     self.config["tokens"]["completion_limit"] = completion_token_limit
        #     flashcards += self._generate_flashcards(messages)

        # Run long text using test splitting
        else:
            write_to_log_and_print(f"Using text splitting using {self.model_name}...\n")

            # Split the text into fragments
            base_prompt_size = self._calculate_base_prompt_size(messages, self.additional_prompt)
            print(f"Base prompt size: {base_prompt_size}")
            try:
                fragment_list = text_split.split_text(self.model_name, text_input, base_prompt_size, self.config["tokens"])
            except PromptSizeError as e:
                logging.error(f"Prompt size error occurred: {str(e)}")
                print(f"Terminating the program due to the following PromptSizeError: {str(e)}")
                exit(1)

            count = 1  # Counter for debug print statements
            for text_fragment in fragment_list:
                write_to_log_and_print(f'\nProcessing text fragment No {count}')
                count += 1

                # Generate a new Messages for the new shorter text_fragment
                new_messages = Messages(
                    messages.system,
                    messages.example_user,
                    messages.example_assistant,
                    inset_into_string(self.additional_prompt, text_fragment, 0)
                )

                sub_prompt_size = self._calculate_total_prompt_size(new_messages)
                formatted_sub_prompt_size = format_num(sub_prompt_size)
                write_to_log_and_print(f"Calculated prompt size: {formatted_sub_prompt_size} tokens")
                max_tokens = 4000 - sub_prompt_size

                # Generate flashcards and add them to the flashcard list
                new_cards = flashcard_generator.generate_flashcards("gpt-3.5-turbo", new_messages, max_tokens)
                flashcards += new_cards
                for flashcard in new_cards:
                    print(flashcard.as_csv())

        flashcard_deck = FlashcardDeck(flashcards)
        return flashcard_deck

    def _calculate_total_prompt_size(self, messages: Messages, *additional_strings) -> int:
        """Calculates the total prompt size based on the message content."""
        encoding = tiktoken.encoding_for_model(self.model_name)
        # There are 18 additional tokens in the prompt due to the list format
        base_count = 18 + sum(
            [len(encoding.encode(message['content'])) + len(encoding.encode(message['role'])) for message in
             messages]
        )

        # Calculate the tokens for additional strings
        additional_count = sum([len(encoding.encode(s)) for s in additional_strings])
        return base_count + additional_count

    def _calculate_base_prompt_size(self, messages: Messages, *additional_strings) -> int:
        encoding = tiktoken.encoding_for_model(self.model_name)
        # There are 18 additional tokens in the prompt due to the list format
        message_list = messages.as_message_list()  # Call the as_message_list method to get the list of messages
        base_count = 18 + sum(
            [len(encoding.encode(message['content'])) + len(encoding.encode(message['role']))
             for message in message_list[:-1]]  # Slice to skip the last message containing the text_input
        )

        # Calculate the tokens for additional strings
        additional_count = sum([len(encoding.encode(s)) for s in additional_strings])
        return base_count + additional_count

    @staticmethod
    def _save_flashcards_as_csv(flashcards: List[Flashcard], csv_path: str):
        """Saves the generated flashcards as a CSV file."""
        deck = FlashcardDeck(flashcards)
        deck.save_as_csv(csv_path)

# todo: Check run_config for specified export format and add conditional statement
# todo: Write Anki Exporter to optionally export the csv flashcards directly to the users Anki workspace, if connected