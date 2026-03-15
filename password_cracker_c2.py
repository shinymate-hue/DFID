import hashlib
import argparse
import sys

def load_hashes(file_path):
    """
    Reads a file containing hashes and returns them as a set.
    Using a set significantly improves search speed (O(1) average time complexity).
    """
    hashes_to_find = set()
    
    try:
        # Context manager (with) ensures the file is automatically closed.
        # 
        # [WHY USE 'encoding="utf-8"' HERE?]
        # If we do not specify the encoding, Python defaults to the OS's default 
        # (e.g., CP949 on Windows). By explicitly setting 'utf-8', we guarantee 
        # cross-platform compatibility and prevent UnicodeDecodeErrors if the 
        # hash file was generated on a different operating system.
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                hashes_to_find.add(line.strip().lower())
        return hashes_to_find
        
    except FileNotFoundError:
        print(f"[!] Error: Hash file not found. Please check the path: {file_path}")
        sys.exit(1)
    except Exception as e:
        print(f"[!] Error: An unknown error occurred while reading the hash file: {e}")
        sys.exit(1)

def hash_string(byte_encoded_string_to_hash, hash_function):
    """
    Calculates the hash of a byte string using the specified algorithm dynamically.
    Uses 'getattr' to avoid hardcoded if-elif-else statements.
    """
    # Normalize the algorithm name to match hashlib attributes 
    # (e.g., user inputs "SHA-256" -> changes to "sha256")
    normalized_algo = hash_function.lower().replace("-", "")

    try:
        # [EXTENSION QUESTION: USING getattr]
        # Instead of doing: if algo == "md5": func = hashlib.md5 ...
        # 'getattr(hashlib, "sha256")' acts exactly like typing 'hashlib.sha256'.
        # This dynamically fetches the correct function object from the hashlib library.
        hash_constructor = getattr(hashlib, normalized_algo)
        
        # Initialize the hash object (e.g., hashlib.md5())
        hash_algorithm = hash_constructor()
        
        # Feed the byte string into the hash object
        hash_algorithm.update(byte_encoded_string_to_hash)
        
        # Return the resulting hex string
        return hash_algorithm.hexdigest()
        
    except AttributeError:
        # If getattr fails to find the algorithm in hashlib, it throws an AttributeError.
        # We catch it here to handle unsupported user inputs gracefully.
        print(f"[!] Error: Unsupported or invalid hash algorithm '{hash_function}'.")
        print(f"    Available algorithms usually include: md5, sha1, sha256, sha512")
        sys.exit(1)

def crack_passwords(target_hashes, wordlist_path, algorithm):
    """
    Reads a wordlist file byte-by-byte, hashes each word using the chosen algorithm,
    and checks if it exists in the target_hashes set.
    """
    found_count = 0
    
    try:
        # Open in 'rb' (read-binary) mode to prevent UnicodeDecodeErrors from 
        # corrupted/weird characters in massive real-world wordlists.
        with open(wordlist_path, "rb") as wordlist_file:
            for word_bytes in wordlist_file:
                # Remove trailing whitespaces/newlines from the byte string
                word_bytes = word_bytes.rstrip()

                # Call our new dynamic hash function
                hashed_entry = hash_string(word_bytes, algorithm)

                # Fast lookup: check if the calculated hash is in our target set
                if hashed_entry in target_hashes:
                    try:
                        # [WHY USE 'decode("utf-8")' HERE?]
                        # 'word_bytes' is raw machine data. To print it nicely to the screen,
                        # we translate (decode) it into a human-readable UTF-8 string.
                        word_string = word_bytes.decode('utf-8')
                        print(f"[+] Password Found! | Hash: {hashed_entry} -> Password: {word_string}")
                        found_count += 1
                    except UnicodeDecodeError:
                        # If the cracked password is not valid UTF-8 text, print its hex instead.
                        print(f"[!] Password found, but could not be decoded as text. (Hex: {word_bytes.hex()})")

    except FileNotFoundError:
        print(f"[!] Error: Wordlist file not found: {wordlist_path}")
        sys.exit(1)
    except Exception as e:
        print(f"[!] Error: An issue occurred while processing the wordlist: {e}")
        sys.exit(1)
        
    return found_count

def main():
    parser = argparse.ArgumentParser(description='Crack hashes using a dictionary attack.')
    
    # -w (Required): Path to the wordlist file
    parser.add_argument('-w', '--wordlist', dest='wordlist', required=True, 
                        help='Path to the wordlist file')
    # -t (Optional): Path to the target hash file
    parser.add_argument('-t', '--target', dest='target', default='password-hashes.txt', 
                        help='File containing hashes to crack (Default: password-hashes.txt)')
    
    # -a (Optional): Algorithm to use (Default: md5)
    parser.add_argument('-a', '--algorithm', dest='algorithm', default='md5', 
                        help='Hash algorithm to use (e.g., md5, sha256, sha512). Default: md5')

    args = parser.parse_args()

    print(f"[*] Wordlist file: {args.wordlist}")
    print(f"[*] Target hash file: {args.target}")
    print(f"[*] Hash Algorithm: {args.algorithm.upper()}")
    print("-" * 50)

    # 1. Load hashes from the target file
    target_hashes = load_hashes(args.target)
    
    if not target_hashes:
        print("[-] The target hash file is empty. Exiting program.")
        sys.exit(0)
        
    print(f"[*] Loaded {len(target_hashes)} hashes. Starting the cracking process...")

    # 2. Compare against the wordlist to crack passwords using the chosen algorithm
    found_count = crack_passwords(target_hashes, args.wordlist, args.algorithm)
    
    # 3. Print summary of the operation
    print("-" * 50)
    print(f"[*] Job completed. Found a total of {found_count} passwords.")

if __name__ == "__main__":
    main()