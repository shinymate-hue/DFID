import hashlib
import argparse
import sys
import re


# ==================================================================================
# CORE LOGIC: Dynamic Hashing & Regex-based Pattern Processing
# ==================================================================================


def hash_string(byte_encoded_string_to_hash, algorithm):
    """
    Takes a byte-encoded string and hashes it using the specified algorithm.
    It uses 'hashlib.new()' to dynamically initialize the hash object, 
    which is the standard and most Pythonic way to handle dynamic hashes.
    """
    # Normalize the algorithm name (e.g., "SHA-256" -> "sha256")
    algo_name = algorithm.lower().replace("-", "")
    try:
        # Dynamically initialize the hash object using hashlib.new()
        hash_algo = hashlib.new(algo_name)
        
        # Feed the byte string into the hash object
        hash_algo.update(byte_encoded_string_to_hash)
        
        # Return the resulting hexadecimal string
        return hash_algo.hexdigest()
        
    except ValueError:
        # [CRITICAL CHANGE] hashlib.new() raises a ValueError (not AttributeError) 
        # when an unsupported algorithm name is provided.
        print(f"[!] Error: Unsupported hash algorithm specified. ({algorithm})")
        sys.exit(1)

class CharacterResult:
    """
    A data container holding the result of incrementing a single character.
    'overflow' becomes True when a character reaches its limit (e.g., 'z' or '9')
    and rolls back to the beginning ('a' or '0'), signaling the next dial to spin.
    """
    def __init__(self, char, overflow):
        self.character = char
        self.overflow = overflow


class WordResult:
    """
    A data container holding the completely updated word.
    'finished' becomes True when all combinations for the given pattern 
    have been exhausted (i.e., the leftmost dial triggers an overflow).
    """
    def __init__(self, word, finished):
        self.word = word
        self.finished = finished


def next_character(current_character):
    """
    Determines the next character in the sequence.
    Uses Regular Expressions (regex) to efficiently check if the character 
    is a lowercase letter, uppercase letter, or a number.
    """
    next_char = None
    overflow = False

    # [REGEX APPLIED] Check if the character falls within the a-z or A-Z ranges
    is_lower_case_letter = bool(re.match(r'[a-z]', current_character))
    is_upper_case_letter = bool(re.match(r'[A-Z]', current_character))

    if is_lower_case_letter or is_upper_case_letter:
        # If it's a letter, convert to lowercase, increment its ASCII value, and convert back
        next_char = chr(ord(current_character.lower()) + 1)
        
        # If it goes past 'z', roll it over to 'a' and trigger an overflow flag
        if next_char > 'z':
            next_char = 'a'
            overflow = True
            
        # Restore the uppercase format if the original character was uppercase
        if is_upper_case_letter:
            next_char = next_char.upper()
    else:
        # If it's not a letter, assume it is a number (0-9)
        next_integer = int(current_character) + 1
        # Modulo 10 ensures that 9 + 1 becomes 0 (rolling over)
        next_char = str(next_integer % 10)
        # Trigger an overflow flag if the number exceeded 9
        overflow = next_integer > 9
    
    return CharacterResult(next_char, overflow)


def next_word(word):
    """
    Acts like a mechanical combination lock or a car's odometer.
    It increments the rightmost character and handles any chain-reaction 
    overflows moving towards the left.
    """
    # Convert string to list for mutability (e.g., "Aaaa00" -> ['A','a','a','a','0','0'])
    characters_in_word = list(word)
    
    # Start at the rightmost index
    character_index = len(characters_in_word) - 1
    current_character = characters_in_word[character_index]

    # Increment the rightmost character
    next_char_result = next_character(current_character)
    characters_in_word[character_index] = next_char_result.character
    
    # [CASCADE OVERFLOW LOGIC]
    # While there is an overflow and we haven't fallen off the left edge of the word...
    while next_char_result.overflow and character_index > -1:
        # Move one index to the left
        character_index -= 1 
        
        # If the index goes below 0, we have exhausted all possible combinations
        if character_index < 0:
            break
            
        # Grab the character at the new index, increment it, and update the list
        current_character = characters_in_word[character_index]
        next_char_result = next_character(current_character)
        characters_in_word[character_index] = next_char_result.character

    # Join the list back into a string. If character_index < 0, finished is set to True.
    return WordResult(''.join(characters_in_word), character_index < 0)


# ==================================================================================
# EXECUTION MODES: Pattern Brute-force & Wordlist Attack
# ==================================================================================


def try_pattern_password_hash(start_pattern, target_hash, algorithm):
    """
    Executes the rule-based brute-force (Mask) attack.
    Continuously generates new passwords based on the pattern and compares their hashes.
    """
    print(f"[*] Starting Pattern Attack (Start: {start_pattern}, Target: {target_hash})")
    current = WordResult(start_pattern, False)
    
    # Dictionary to keep track of the attack's progress and results
    pattern_attack_result = {"found": False, "password": None, "finished": False}

    # Run the loop until we either find the password or exhaust all combinations
    while not pattern_attack_result["finished"]:
        
        # Check if the 'next_word' function reported that there are no combinations left.
        # This is placed at the TOP of the loop so the very last word still gets tested below.
        if current.finished:
            pattern_attack_result["finished"] = True

        # Hash the current word and compare it to our target
        if hash_string(current.word.encode(), algorithm) == target_hash:
            # MATCH FOUND! Update the dictionary and the loop will naturally terminate.
            pattern_attack_result["found"] = True
            pattern_attack_result["finished"] = True
            pattern_attack_result["password"] = current.word
        else:
            # NO MATCH. Generate the next combination and loop again.
            current = next_word(current.word)

    return pattern_attack_result


def try_wordlist_password_hash(hash_file, wordlist_file, algorithm):
    """
    Executes a dictionary attack using a provided wordlist.
    """
    print(f"[*] Starting Wordlist Attack (Hashes: {hash_file}, Wordlist: {wordlist_file})")
    try:
        # Open both files in 'rb' (read-binary) to prevent UnicodeDecodeErrors from messy wordlists
        with open(wordlist_file, 'rb') as byte_encoded_wordlist, \
             open(hash_file, 'rb') as byte_encoded_hashlist:
            
            # Read all target hashes into a list, decoding them to standard strings
            password_hash_list = [h.rstrip().decode() for h in byte_encoded_hashlist]
            total_hashes = len(password_hash_list)

            for byte_encoded_word in byte_encoded_wordlist:
                # Clean up newlines/spaces
                byte_encoded_word = byte_encoded_word.rstrip()
                hashed_entry = hash_string(byte_encoded_word, algorithm)

                # Iterate over a COPY ([:]) of the list so we can safely remove items from the original
                for hashed_password_entry in password_hash_list[:]: 
                    if hashed_entry == hashed_password_entry:
                        print(f"[+] Password Found: {byte_encoded_word.decode()} (Hash: {hashed_password_entry})")
                        # Remove the found hash to speed up subsequent lookups
                        password_hash_list.remove(hashed_password_entry)
                
                # PEP 8 check for empty list. If empty, we found all passwords. Break out early.
                if not password_hash_list:
                    break
            
            # Final summary
            if password_hash_list:
                print(f"[-] Failed to crack {len(password_hash_list)} hash(es).")
                for unfound in password_hash_list:
                    print(f"    -> Unfound hash: {unfound}")
            else:
                print(f"[*] Success! All {total_hashes} hashes were successfully cracked.")

    except FileNotFoundError as e:
        print(f"[!] Error: File not found. Please check your path. ({e.filename})")
        sys.exit(1)


# ==================================================================================
# MAIN FUNCTION: Command Line Interface (CLI) Setup
# ==================================================================================


def main():
    # Set up argparse to handle flags and user input smoothly
    parser = argparse.ArgumentParser(
        description="Advanced Password Cracker (Supports Pattern Brute-force & Wordlist Attacks)",
        epilog="Usage Examples:\n"
               "  Wordlist Attack: python script.py -m wordlist -f hashes.txt -w rockyou.txt\n"
               "  Pattern Attack:  python script.py -m pattern -p Aaaa00 -t 3dec5fccd33913e15aa9e352ab59a1da",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    # Required Mode Selection
    parser.add_argument('-m', '--mode', choices=['pattern', 'wordlist'], required=True, 
                        help="Select execution mode: 'pattern' or 'wordlist'")
    
    # Optional Algorithm Selection
    parser.add_argument('-a', '--algo', default='md5', 
                        help="Hash algorithm to use (Default: md5. e.g., sha256, sha512)")
    
    # Arguments specifically for Wordlist Mode
    parser.add_argument('-f', '--hashfile', help="Path to the file containing hashes (Required for wordlist mode)")
    parser.add_argument('-w', '--wordlist', help="Path to the wordlist dictionary (Required for wordlist mode)")
    
    # Arguments specifically for Pattern Mode
    parser.add_argument('-t', '--target', help="Single target hash to crack (Required for pattern mode)")
    parser.add_argument('-p', '--pattern', help="Starting pattern, e.g., Aaaa00 (Required for pattern mode)")
    
    # -------------------------------------------------------------------------
    # If the user runs the script without any arguments, automatically print 
    # the help menu instead of throwing a generic missing argument error.
    # -------------------------------------------------------------------------
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
        
    # Parse the user's inputs
    args = parser.parse_args()
    print("-" * 50)
    
    # Route the execution based on the selected mode
    if args.mode == 'wordlist':
        # Ensure the user provided the necessary files for a wordlist attack
        if not args.hashfile or not args.wordlist:
            parser.error("Wordlist mode requires both '-f' (hash file) and '-w' (wordlist file) to be specified.")
        
        try_wordlist_password_hash(args.hashfile, args.wordlist, args.algo)
        
    elif args.mode == 'pattern':
        # Ensure the user provided the necessary pattern and target for a brute-force attack
        if not args.target or not args.pattern:
            parser.error("Pattern mode requires both '-t' (target hash) and '-p' (start pattern) to be specified.")
        
        result = try_pattern_password_hash(args.pattern, args.target, args.algo)
        
        # Print the final result of the pattern attack
        if result["found"]:
            print(f"[+] Password Found: {result['password']}")
        else:
            print("[-] Password Not Found. The target password does not match the provided pattern format.")
            
    print("-" * 50)


# Standard Python boilerplate to ensure main() runs only when the script is executed directly
if __name__ == "__main__":
    main()