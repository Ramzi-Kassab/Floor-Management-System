"""
Text Processing Tools Service

Text case conversion, formatting, encoding, word count, diff, etc.
"""

import base64
import hashlib
import re
from typing import Tuple, List
import difflib


class TextToolsService:
    """
    Service for text processing operations.
    """

    @classmethod
    def change_case(cls, text: str, case_type: str) -> str:
        """
        Convert text case.

        Args:
            text: Input text
            case_type: Type of case conversion
                - 'upper': UPPER CASE
                - 'lower': lower case
                - 'title': Title Case
                - 'sentence': Sentence case
                - 'camel': camelCase
                - 'pascal': PascalCase
                - 'snake': snake_case
                - 'kebab': kebab-case

        Returns:
            Converted text

        Example:
            result = TextToolsService.change_case("hello world", "title")
            # Returns: "Hello World"
        """
        if case_type == 'upper':
            return text.upper()

        elif case_type == 'lower':
            return text.lower()

        elif case_type == 'title':
            return text.title()

        elif case_type == 'sentence':
            # Capitalize first letter of each sentence
            sentences = re.split(r'([.!?]\s+)', text)
            result = []
            for i, sentence in enumerate(sentences):
                if i % 2 == 0 and sentence:  # Actual sentence, not delimiter
                    result.append(sentence[0].upper() + sentence[1:].lower() if len(sentence) > 1 else sentence.upper())
                else:
                    result.append(sentence)
            return ''.join(result)

        elif case_type == 'camel':
            # camelCase
            words = re.findall(r'[A-Za-z0-9]+', text)
            if not words:
                return text
            return words[0].lower() + ''.join(word.capitalize() for word in words[1:])

        elif case_type == 'pascal':
            # PascalCase
            words = re.findall(r'[A-Za-z0-9]+', text)
            return ''.join(word.capitalize() for word in words)

        elif case_type == 'snake':
            # snake_case
            words = re.findall(r'[A-Za-z0-9]+', text)
            return '_'.join(word.lower() for word in words)

        elif case_type == 'kebab':
            # kebab-case
            words = re.findall(r'[A-Za-z0-9]+', text)
            return '-'.join(word.lower() for word in words)

        else:
            raise ValueError(f"Unknown case type: {case_type}")

    @classmethod
    def count_words(cls, text: str) -> dict:
        """
        Count words, characters, lines, and paragraphs in text.

        Args:
            text: Input text

        Returns:
            Dict with counts

        Example:
            counts = TextToolsService.count_words("Hello world\\nNew line")
            # Returns: {'words': 4, 'characters': 21, 'lines': 2, ...}
        """
        # Word count
        words = re.findall(r'\b\w+\b', text)
        word_count = len(words)

        # Character counts
        char_count = len(text)
        char_no_spaces = len(text.replace(' ', '').replace('\n', '').replace('\t', ''))

        # Line count
        lines = text.split('\n')
        line_count = len(lines)

        # Paragraph count (groups of non-empty lines)
        paragraphs = [p for p in text.split('\n\n') if p.strip()]
        paragraph_count = len(paragraphs)

        # Sentence count
        sentences = re.split(r'[.!?]+', text)
        sentence_count = len([s for s in sentences if s.strip()])

        return {
            'words': word_count,
            'characters': char_count,
            'characters_no_spaces': char_no_spaces,
            'lines': line_count,
            'paragraphs': paragraph_count,
            'sentences': sentence_count,
        }

    @classmethod
    def text_diff(cls, text1: str, text2: str, output_format: str = 'unified') -> str:
        """
        Compare two texts and show differences.

        Args:
            text1: First text
            text2: Second text
            output_format: Output format ('unified', 'context', 'html')

        Returns:
            Diff output string

        Example:
            diff = TextToolsService.text_diff("Hello world", "Hello there")
        """
        lines1 = text1.splitlines(keepends=True)
        lines2 = text2.splitlines(keepends=True)

        if output_format == 'unified':
            diff = difflib.unified_diff(lines1, lines2, lineterm='')
            return '\n'.join(diff)

        elif output_format == 'context':
            diff = difflib.context_diff(lines1, lines2, lineterm='')
            return '\n'.join(diff)

        elif output_format == 'html':
            diff = difflib.HtmlDiff()
            return diff.make_file(lines1, lines2)

        else:
            raise ValueError(f"Unknown output format: {output_format}")

    @classmethod
    def encode_decode(cls, text: str, operation: str, encoding: str = 'utf-8') -> str:
        """
        Encode or decode text.

        Args:
            text: Input text
            operation: Operation type
                - 'base64_encode'
                - 'base64_decode'
                - 'url_encode'
                - 'url_decode'
                - 'html_escape'
                - 'html_unescape'
            encoding: Text encoding (default: utf-8)

        Returns:
            Encoded/decoded text

        Example:
            encoded = TextToolsService.encode_decode("Hello", "base64_encode")
            # Returns: "SGVsbG8="
        """
        import urllib.parse
        import html

        if operation == 'base64_encode':
            return base64.b64encode(text.encode(encoding)).decode('ascii')

        elif operation == 'base64_decode':
            return base64.b64decode(text).decode(encoding)

        elif operation == 'url_encode':
            return urllib.parse.quote(text)

        elif operation == 'url_decode':
            return urllib.parse.unquote(text)

        elif operation == 'html_escape':
            return html.escape(text)

        elif operation == 'html_unescape':
            return html.unescape(text)

        else:
            raise ValueError(f"Unknown operation: {operation}")

    @classmethod
    def generate_hash(cls, text: str, algorithm: str = 'sha256') -> str:
        """
        Generate hash of text.

        Args:
            text: Input text
            algorithm: Hash algorithm (md5, sha1, sha256, sha512)

        Returns:
            Hex digest of hash

        Example:
            hash_value = TextToolsService.generate_hash("password", "sha256")
        """
        text_bytes = text.encode('utf-8')

        if algorithm == 'md5':
            return hashlib.md5(text_bytes).hexdigest()
        elif algorithm == 'sha1':
            return hashlib.sha1(text_bytes).hexdigest()
        elif algorithm == 'sha256':
            return hashlib.sha256(text_bytes).hexdigest()
        elif algorithm == 'sha512':
            return hashlib.sha512(text_bytes).hexdigest()
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")

    @classmethod
    def find_replace(
        cls,
        text: str,
        find: str,
        replace: str,
        case_sensitive: bool = True,
        whole_word: bool = False
    ) -> Tuple[str, int]:
        """
        Find and replace text.

        Args:
            text: Input text
            find: Text to find
            replace: Replacement text
            case_sensitive: Case-sensitive search
            whole_word: Match whole words only

        Returns:
            Tuple of (result_text, replacement_count)

        Example:
            result, count = TextToolsService.find_replace(
                "Hello world", "world", "there"
            )
        """
        flags = 0 if case_sensitive else re.IGNORECASE

        if whole_word:
            pattern = r'\b' + re.escape(find) + r'\b'
        else:
            pattern = re.escape(find)

        result = re.sub(pattern, replace, text, flags=flags)
        count = len(re.findall(pattern, text, flags=flags))

        return result, count

    @classmethod
    def remove_duplicates(cls, text: str, by: str = 'lines') -> str:
        """
        Remove duplicate lines or words.

        Args:
            text: Input text
            by: Remove duplicates by ('lines' or 'words')

        Returns:
            Text with duplicates removed

        Example:
            result = TextToolsService.remove_duplicates(
                "line1\\nline2\\nline1",
                by='lines'
            )
        """
        if by == 'lines':
            lines = text.split('\n')
            seen = set()
            unique_lines = []
            for line in lines:
                if line not in seen:
                    seen.add(line)
                    unique_lines.append(line)
            return '\n'.join(unique_lines)

        elif by == 'words':
            words = text.split()
            seen = set()
            unique_words = []
            for word in words:
                if word not in seen:
                    seen.add(word)
                    unique_words.append(word)
            return ' '.join(unique_words)

        else:
            raise ValueError(f"Unknown by parameter: {by}")

    @classmethod
    def sort_lines(cls, text: str, reverse: bool = False, case_sensitive: bool = True) -> str:
        """
        Sort lines alphabetically.

        Args:
            text: Input text
            reverse: Sort in reverse order
            case_sensitive: Case-sensitive sorting

        Returns:
            Sorted text

        Example:
            sorted_text = TextToolsService.sort_lines("zebra\\napple\\nbanana")
        """
        lines = text.split('\n')

        if case_sensitive:
            sorted_lines = sorted(lines, reverse=reverse)
        else:
            sorted_lines = sorted(lines, key=str.lower, reverse=reverse)

        return '\n'.join(sorted_lines)

    @classmethod
    def extract_emails(cls, text: str) -> List[str]:
        """
        Extract email addresses from text.

        Args:
            text: Input text

        Returns:
            List of email addresses found

        Example:
            emails = TextToolsService.extract_emails(
                "Contact: john@example.com or jane@test.org"
            )
        """
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        return re.findall(email_pattern, text)

    @classmethod
    def extract_urls(cls, text: str) -> List[str]:
        """
        Extract URLs from text.

        Args:
            text: Input text

        Returns:
            List of URLs found

        Example:
            urls = TextToolsService.extract_urls(
                "Visit https://example.com or http://test.org"
            )
        """
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        return re.findall(url_pattern, text)

    @classmethod
    def extract_phone_numbers(cls, text: str) -> List[str]:
        """
        Extract phone numbers from text.

        Args:
            text: Input text

        Returns:
            List of phone numbers found

        Example:
            phones = TextToolsService.extract_phone_numbers(
                "Call +971-50-123-4567 or 0501234567"
            )
        """
        # Matches various phone number formats
        phone_pattern = r'[\+]?[(]?[0-9]{1,4}[)]?[-\s\.]?[(]?[0-9]{1,4}[)]?[-\s\.]?[0-9]{1,5}[-\s\.]?[0-9]{1,5}'
        return re.findall(phone_pattern, text)
