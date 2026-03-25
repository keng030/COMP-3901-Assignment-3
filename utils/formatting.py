# Helper function to make text bold.

def make_bold(text):
    """
    Clever hack: Converts standard text to Unicode mathematical sans-serif bold characters.
    This allows us to show bold text inside a standard Gradio plain Textbox!
    """
    result = ""
    for char in str(text):
        if 'A' <= char <= 'Z':
            result += chr(ord(char) - ord('A') + 0x1D5D4)
        elif 'a' <= char <= 'z':
            result += chr(ord(char) - ord('a') + 0x1D5EE)
        elif '0' <= char <= '9':
            result += chr(ord(char) - ord('0') + 0x1D7EC)
        else:
            result += char 
    return result