import hashlib
import argparse
import sys
import re

# ==================================================================================
# CORE LOGIC: Dynamic Hashing & Regex-based Pattern Processing
# ==================================================================================

def hashString(byteEncodedStringToHash, algorithm):
    """
    Takes a byte-encoded string and hashes it using the specified algorithm.
    It uses 'getattr' to dynamically fetch the correct algorithm function from 
    the hashlib library, eliminating the need for long if-else blocks.
    """
    # Normalize the algorithm name (e.g., "SHA-256" -> "sha256")
    algo_name = algorithm.lower().replace("-", "")
    try:
        # Dynamically initialize the hash object (e.g., hashlib.md5())
        hashAlgo = getattr(hashlib, algo_name)()
        hashAlgo.update(byteEncodedStringToHash)
        # Return the resulting hexadecimal string
        return hashAlgo.hexdigest()
    except AttributeError:
        # If the user provides an invalid algorithm, gracefully exit
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

def Next_Character(currentCharacter):
    """
    Determines the next character in the sequence.
    Uses Regular Expressions (regex) to efficiently check if the character 
    is a lowercase letter, uppercase letter, or a number.
    """
    nextCharacter = None
    overflow = False

    # [REGEX APPLIED] Check if the character falls within the a-z or A-Z ranges
    isLowerCaseLetter = bool(re.match(r'[a-z]', currentCharacter))
    isUpperCaseLetter = bool(re.match(r'[A-Z]', currentCharacter))

    if isLowerCaseLetter or isUpperCaseLetter:
        # If it's a letter, convert to lowercase, increment its ASCII value, and convert back
        nextCharacter = chr(ord(currentCharacter.lower()) + 1)
        
        # If it goes past 'z', roll it over to 'a' and trigger an overflow flag
        if nextCharacter > 'z':
            nextCharacter = 'a'
            overflow = True
            
        # Restore the uppercase format if the original character was uppercase
        if isUpperCaseLetter:
            nextCharacter = nextCharacter.upper()
    else:
        # If it's not a letter, assume it is a number (0-9)
        nextInteger = int(currentCharacter) + 1
        # Modulo 10 ensures that 9 + 1 becomes 0 (rolling over)
        nextCharacter = str(nextInteger % 10)
        # Trigger an overflow flag if the number exceeded 9
        overflow = nextInteger > 9
    
    return CharacterResult(nextCharacter, overflow)

def Next_Word(word):
    """
    Acts like a mechanical combination lock or a car's odometer.
    It increments the rightmost character and handles any chain-reaction 
    overflows moving towards the left.
    """
    # Convert string to list for mutability (e.g., "Aaaa00" -> ['A','a','a','a','0','0'])
    charactersInWord = list(word)
    
    # Start at the rightmost index
    characterIndex = len(charactersInWord) - 1
    currentCharacter = charactersInWord[characterIndex]

    # Increment the rightmost character
    nextCharacter = Next_Character(currentCharacter)
    charactersInWord[characterIndex] = nextCharacter.character
    
    # [CASCADE OVERFLOW LOGIC]
    # While there is an overflow and we haven't fallen off the left edge of the word...
    while nextCharacter.overflow and characterIndex > -1:
        # Move one index to the left
        characterIndex = characterIndex - 1 
        
        # If the index goes below 0, we have exhausted all possible combinations
        if characterIndex < 0:
            break
            
        # Grab the character at the new index, increment it, and update the list
        currentCharacter = charactersInWord[characterIndex]
        nextCharacter = Next_Character(currentCharacter)
        charactersInWord[characterIndex] = nextCharacter.character

    # Join the list back into a string. If characterIndex < 0, finished is set to True.
    return WordResult(''.join(charactersInWord), characterIndex < 0)

# ==================================================================================
# EXECUTION MODES: Pattern Brute-force & Wordlist Attack
# ==================================================================================

def TryPatternPasswordHash(start_pattern, target_hash, algorithm):
    """
    Executes the rule-based brute-force (Mask) attack.
    Continuously generates new passwords based on the pattern and compares their hashes.
    """
    print(f"[*] Starting Pattern Attack (Start: {start_pattern}, Target: {target_hash})")
    current = WordResult(start_pattern, False)
    
    # Dictionary to keep track of the attack's progress and results
    patternAttackResult = { "Found": False, "Password": None, "Finished": False }

    # Run the loop until we either find the password or exhaust all combinations
    while not patternAttackResult["Finished"]:
        
        # Check if the 'Next_Word' function reported that there are no combinations left.
        # This is placed at the TOP of the loop so the very last word still gets tested below.
        if current.finished:
            patternAttackResult["Finished"] = True

        # Hash the current word and compare it to our target
        if hashString(current.word.encode(), algorithm) == target_hash:
                # MATCH FOUND! Update the dictionary and the loop will naturally terminate.
                patternAttackResult["Found"] = True
                patternAttackResult["Finished"] = True
                patternAttackResult["Password"] = current.word
        else:
            # NO MATCH. Generate the next combination and loop again.
            current = Next_Word(current.word)

    return patternAttackResult

def TryWordlistPasswordHash(hash_file, wordlist_file, algorithm):
    """
    Executes a dictionary attack using a provided wordlist.
    """
    print(f"[*] Starting Wordlist Attack (Hashes: {hash_file}, Wordlist: {wordlist_file})")
    try:
        # Open both files in 'rb' (read-binary) to prevent UnicodeDecodeErrors from messy wordlists
        with open(wordlist_file, 'rb') as byteEncodedWordlist, open(hash_file, 'rb') as byteEncodedHashlist:
            
            # Read all target hashes into a list, decoding them to standard strings
            passwordHashlist = [h.rstrip().decode() for h in byteEncodedHashlist]
            total_hashes = len(passwordHashlist)

            for byteEncodedWord in byteEncodedWordlist:
                # Clean up newlines/spaces
                byteEncodedWord = byteEncodedWord.rstrip()
                hashedEntry = hashString(byteEncodedWord, algorithm)

                # Iterate over a COPY ([:]) of the list so we can safely remove items from the original
                for hashedPasswordEntry in passwordHashlist[:]: 
                    if hashedEntry == hashedPasswordEntry:
                        print(f"[+] Password Found: {byteEncodedWord.decode()} (Hash: {hashedPasswordEntry})")
                        # Remove the found hash to speed up subsequent lookups
                        passwordHashlist.remove(hashedPasswordEntry)
                
                # If the list is empty, we found all passwords. Break out early.
                if len(passwordHashlist) == 0:
                    break
            
            # Final summary
            if len(passwordHashlist) > 0:
                print(f"[-] Failed to crack {len(passwordHashlist)} hash(es).")
                for unfound in passwordHashlist:
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
        
        TryWordlistPasswordHash(args.hashfile, args.wordlist, args.algo)
        
    elif args.mode == 'pattern':
        # Ensure the user provided the necessary pattern and target for a brute-force attack
        if not args.target or not args.pattern:
            parser.error("Pattern mode requires both '-t' (target hash) and '-p' (start pattern) to be specified.")
        
        result = TryPatternPasswordHash(args.pattern, args.target, args.algo)
        
        # Print the final result of the pattern attack
        if result["Found"]:
            print(f"[+] Password Found: {result['Password']}")
        else:
            print("[-] Password Not Found. The target password does not match the provided pattern format.")
            
    print("-" * 50)

# Standard Python boilerplate to ensure main() runs only when the script is executed directly
if __name__ == "__main__":
    main()