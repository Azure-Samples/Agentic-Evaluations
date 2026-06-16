"""Tool functions for the Multi-Tool Agent."""

from random import randint
from typing import Annotated

from pydantic import Field


def get_weather(
    location: Annotated[str, Field(description="The location to get the weather for.")],
) -> str:
    """Get the weather for a given location."""
    conditions = ["sunny", "cloudy", "rainy", "stormy"]
    return f"The weather in {location} is {conditions[randint(0, 3)]} with a high of {randint(10, 30)}°C."


def get_current_datetime() -> str:
    """Get the current date and time."""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def calculate_sum(
    numbers: Annotated[list[float], Field(description="A list of numbers to sum together.")]
) -> float:
    """Calculate the sum of a list of numbers."""
    return sum(numbers)


def calculate_product(
    numbers: Annotated[list[float], Field(description="A list of numbers to multiply together.")]
) -> float:
    """Calculate the product of a list of numbers."""
    result = 1
    for num in numbers:
        result *= num
    return result


def convert_temperature(
    value: Annotated[float, Field(description="The temperature value to convert.")],
    from_unit: Annotated[str, Field(description="The source unit: 'C' for Celsius, 'F' for Fahrenheit, or 'K' for Kelvin.")],
    to_unit: Annotated[str, Field(description="The target unit: 'C' for Celsius, 'F' for Fahrenheit, or 'K' for Kelvin.")]
) -> str:
    """Convert temperature between Celsius, Fahrenheit, and Kelvin."""
    # Convert to Celsius first
    if from_unit.upper() == 'F':
        celsius = (value - 32) * 5/9
    elif from_unit.upper() == 'K':
        celsius = value - 273.15
    else:
        celsius = value
    
    # Convert from Celsius to target unit
    if to_unit.upper() == 'F':
        result = celsius * 9/5 + 32
    elif to_unit.upper() == 'K':
        result = celsius + 273.15
    else:
        result = celsius
    
    return f"{value}°{from_unit.upper()} = {result:.2f}°{to_unit.upper()}"


def count_words(
    text: Annotated[str, Field(description="The text to analyze.")]
) -> dict:
    """Count words, characters, and sentences in a given text."""
    words = text.split()
    sentences = text.count('.') + text.count('!') + text.count('?')
    
    return {
        "word_count": len(words),
        "character_count": len(text),
        "character_count_no_spaces": len(text.replace(" ", "")),
        "sentence_count": max(sentences, 1)
    }


def generate_uuid() -> str:
    """Generate a random UUID (Universally Unique Identifier)."""
    import uuid
    return str(uuid.uuid4())


def format_json(
    data: Annotated[str, Field(description="The JSON string to format.")],
    indent: Annotated[int, Field(description="Number of spaces for indentation (default: 2)")] = 2
) -> str:
    """Format a JSON string with proper indentation for readability."""
    import json
    try:
        parsed = json.loads(data)
        return json.dumps(parsed, indent=indent)
    except json.JSONDecodeError as e:
        return f"Error parsing JSON: {str(e)}"
