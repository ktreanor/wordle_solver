import os
import wordfreq

from itertools import chain
from collections import Counter


class WordleSover:

    # Valid words are all the words that the game accepts as guesses
    __valid_words = []
    __working_list = []

    # Dictionaries used for recommendation strategies
    __letter_count = {}
    __scored_words = {}

    def __init__(self):
        # Get the path for the valid words csv
        valid_words_file = os.path.join(os.path.dirname(__file__), "valid-words.csv")

        # Open the valid words file and load into the list
        with open(valid_words_file) as valid_words:
            self.__valid_words.extend(valid_words.read().splitlines())

        # Prepare all the lists and dictionaries to play
        self.__prepare_game()

    # region - Scoring Functions

    def __prepare_game(self) -> None:
        """
        Gets everything set up for playing the game, loads the dictionaries and clears the working list
        """
        # Clear the working list
        self.__working_list.clear()

        # Start the working list with all the words in the valid words list
        self.__working_list.extend(self.__valid_words)

        # Create the initial work scoring used in the recommendations
        self.__score_words()

    def __get_letter_usage(self):
        """
        Creates a dictionary for each letter with how often it's used in the remaining working list

        :return: The dictionary histogram of the letters and their count in the working list
        """

        # The from_iterable function will turn all the words into a single list of letters, then the counter creates a dictionary with the count of each letter
        return Counter(chain.from_iterable(self.__working_list))

    def __get_word_score(self, word: str) -> int:
        """
        Returns a score for the word depending on how frequent the letters it contains are used in the remaining potential answers

        :param word: The word you wish to score
        :return: The score of the word
        """
        score = 0

        # Remove all duplicate letters in the word then turn it into a list (Removing duplicates avoids making recommendations with multiple e's for example)
        for letter in list(set(word)):
            score += self.__letter_count[letter]

        # Give common words a slightly higher score to increase their likelihood of being recommended
        score += self.__get_frequency_score(word)
        return score

    def __get_frequency_score(self, word: str) -> int:
        """
        Returns a value depending on how common the word is used in the english language

        :param word: The word you wish to score
        :return: The score of the word
        """

        # Bit of a magic number here, but after running a lot of simulations multiplying the word frequency by 2 gave the highest win rate
        return wordfreq.zipf_frequency(word, "en") * 2

    def __score_words(self):
        """
        Loops through all the words in the working list and scores them based on letter frequency and how common the word is in the english language
        """

        # Clear the old values
        self.__letter_count.clear()
        self.__scored_words.clear()

        self.__letter_count = self.__get_letter_usage()

        # Loops through the working list and creates a dictionary with the word's score
        for word in self.__working_list:
            self.__scored_words[word] = self.__get_word_score(word)

    # endregion

    # region - Filter Functions

    def __gray_letter(self, letter) -> None:
        """
        Filters the working list when a letter in a guess is marked as grey, meaning it doesn't exist in the puzzle word

        :param letter: Letter that doesn't exist in the puzzle word
        """
        temp_list = []

        # Loop through all the words in the working list and find only those that do NOT have the letter
        for word in self.__working_list:
            if letter not in word:
                temp_list.append(word)

        # update the working list
        self.__working_list.clear()
        self.__working_list.extend(temp_list)

    def __green_letter(self, letter, location) -> None:
        """
        Filters the working list when a letter in a guess is marked as green, meaning it is in the right spot of the puzzle word

        :param letter: Letter in the correct location of the puzzle word
        :param location: Location that the letter was used
        """
        temp_list = []

        # Loop through all the words in the working list and find only those that have the letter in the given spot
        for word in self.__working_list:
            if word[location] == letter:
                temp_list.append(word)

        # update the working list
        self.__working_list.clear()
        self.__working_list.extend(temp_list)

    def __yellow_letter(self, letter, location) -> None:
        """
        Filters the working list when a letter in a guess is marked as yellow, meaning it is in the puzzle word, but not in the spot guessed

        :param letter: Letter in the correct location of the puzzle word
        :param location: Location that the letter was used
        """
        temp_list = []

        # Loop through all the words in the working list and find words that do NOT have the letter in that spot.
        for word in self.__working_list:
            if word[location] != letter:
                # Make sure the letter appears somewhere else in the word
                if letter in word:
                    temp_list.append(word)

        # update the working list and clear the temp list
        self.__working_list.clear()
        self.__working_list.extend(temp_list)

    def __refine_working_list(self, guess, result_key) -> None:
        """
        Filters the working list based on a guessed word, and the result key returned from the puzzle.

        :param guess: The word guessed by the user
        :param result_key: The key returned by the puzzle consisting of - if the letter doesn't appear in the word, g if it is in the right spot, and y if it exists in the puzzle word but is in the wrong location
        """
        # Loop through all 5 letters result_key and perform the proper function
        for index in range(0, 5):
            if (result_key[index]) == "-":
                self.__gray_letter(guess[index])
            elif (result_key[index]) == "y":
                self.__yellow_letter(guess[index], index)
            else:
                self.__green_letter(guess[index], index)

        # Rescore the words to take into account the change in letter distribution
        self.__score_words()

    # endregion

    # region - Play Functions

    def __get_recommendation(self, recommendations: int):
        """
        Returns the top recommendations for the next guess

        :param recommendations: How many recommendations the user would like to see
        """
        return dict(
            sorted(self.__scored_words.items(), key=lambda item: item[1], reverse=True)[
                :recommendations
            ]
        )

    def play(self, recommendations: int) -> None:
        """
        Play wordle

        :param recommendations: How many recommendations the user would like to see
        """
        # The user gets 6 tries at the word
        for guess_number in range(0, 6):
            print(
                f"\nAttempt {guess_number+1} with a possible {len(self.__working_list)} words, the best words to play are:\n"
            )

            print("   Word    Frequency")
            print("   =================")

            top_recommendations = self.__get_recommendation(recommendations)
            for rec_word in top_recommendations:
                print(f" - {rec_word} | {self.__get_frequency_score(rec_word):.1f}")

            guess = input("\nYour Guess: ")

            if guess_number == 0:
                result_key = input(
                    "\nType the color coded reply from wordle\n - for Grey\n y for Yellow\n g for Green\n\nResponse from Wordle: "
                )
            else:
                result_key = input("\nResponse from Wordle: ")

            self.__refine_working_list(guess, result_key)

        if guess_number >= 5:
            print(f"Sorry you lost")

    # endregion


if __name__ == "__main__":
    wordle = WordleSover()
    wordle.play(4)
