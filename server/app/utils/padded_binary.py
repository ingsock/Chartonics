import math

def padded_binary(number: int, width: int) -> str:
  """Converts an integer to its binary representation, left-padded with zeros.

  Args:
    number: The integer to convert.
    width: The desired total width of the binary string (including padding).

  Returns:
    A string containing the left-padded binary representation of the number.

  Raises:
    ValueError: If the specified width is insufficient to represent the number
                in binary, or if the number is negative.
  """
  if number < 0:
    raise ValueError("Input number cannot be negative.")

  # Calculate the minimum width required for the number itself
  # Handle the edge case where number is 0
  min_width = math.ceil(math.log2(number + 1)) if number > 0 else 1

  if width < min_width:
      raise ValueError(f"Width {width} is too small to represent {number}. "
                       f"Minimum width required is {min_width}.")

  # Convert the number to binary and remove the '0b' prefix
  binary_representation = bin(number)[2:]

  # Pad the binary string with leading zeros to the desired width
  padded_binary_string = binary_representation.zfill(width)

  return padded_binary_string
