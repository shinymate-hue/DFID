import hashlib
import argparse
import sys

def load_hashes(file_path):
    """
    Reads a file containing hashes and returns them as a set.
    Using a set significantly improves search speed (O(1) average time complexity)
    compared to a list (O(N)).
    """
    hashes_to_find = set()
    
    try:
        # Context manager (with) ensures the file is automatically closed after reading.
        # 
        # [WHY USE 'encoding="utf-8"' HERE?]
        # If we do not specify the encoding, Python defaults to the operating system's 
        # default encoding (e.g., CP949 on Windows, UTF-8 on Linux/macOS). 
        # By explicitly setting 'utf-8', we force Python to read the file using the 
        # universal UTF-8 standard regardless of the OS running the script. 
        # This guarantees cross-platform compatibility and prevents UnicodeDecodeErrors 
        # if the hash file was generated on a different operating system.
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                # Strip newline characters and convert to lowercase for consistent comparison
                hashes_to_find.add(line.strip().lower())
        return hashes_to_find
        
    except FileNotFoundError:
        print(f"[!] Error: Hash file not found. Please check the path: {file_path}")
        sys.exit(1)
    except Exception as e:
        print(f"[!] Error: An unknown error occurred while reading the hash file: {e}")
        sys.exit(1)

def crack_passwords(target_hashes, wordlist_path):
    """
    Reads a wordlist file byte-by-byte, calculates the MD5 hash of each word,
    and checks if it exists in the target_hashes set.
    """
    found_count = 0
    
    try:
        # We open the wordlist in 'rb' (read-binary) mode.
        # Real-world wordlists often contain corrupted, non-UTF-8, or unexpected 
        # byte sequences. Reading in binary prevents Python from crashing with a 
        # UnicodeDecodeError and provides the raw bytes that hashlib.md5() requires.
        with open(wordlist_path, "rb") as wordlist_file:
            for word_bytes in wordlist_file:
                # Remove trailing whitespaces/newlines from the byte string
                word_bytes = word_bytes.rstrip()

                # Calculate the MD5 hash of the raw bytes and convert to a hex string
                hashed_entry = hashlib.md5(word_bytes).hexdigest()

                # Fast lookup: check if the calculated hash is in our target set
                if hashed_entry in target_hashes:
                    try:
                        # [WHY USE 'decode("utf-8")' HERE?]
                        # At this point, 'word_bytes' is a raw byte string (e.g., b'password123').
                        # To print it cleanly to the screen for the user to read, we need to 
                        # translate (decode) those machine bytes back into a human-readable string.
                        # Since UTF-8 is the dominant character encoding standard globally, 
                        # decoding it as UTF-8 is the safest and most standard way to convert 
                        # the raw bytes back into readable text.
                        word_string = word_bytes.decode('utf-8')
                        print(f"[+] Password Found! | Hash: {hashed_entry} -> Password: {word_string}")
                        found_count += 1
                    except UnicodeDecodeError:
                        # If the cracked password contains strange bytes that aren't valid UTF-8,
                        # we catch the error and print the raw hex representation instead.
                        print(f"[!] Password found, but could not be decoded as text. (Hex: {word_bytes.hex()})")

    except FileNotFoundError:
        print(f"[!] Error: Wordlist file not found. Please check the path: {wordlist_path}")
        sys.exit(1)
    except Exception as e:
        print(f"[!] Error: An issue occurred while processing the wordlist: {e}")
        sys.exit(1)
        
    return found_count

def main():
    # Setup argparse to handle command-line arguments gracefully
    parser = argparse.ArgumentParser(description='Crack MD5 hashes using a dictionary attack.')
    
    # -w (Required): Path to the wordlist file
    parser.add_argument('-w', '--wordlist', dest='wordlist', required=True, help='Path to the wordlist file')
    # -t (Optional): Path to the target hash file (Defaults to 'password-hashes.txt')
    parser.add_argument('-t', '--target', dest='target', default='password-hashes.txt', help='File containing hashes to crack (Default: password-hashes.txt)')

    args = parser.parse_args()

    print(f"[*] Wordlist file: {args.wordlist}")
    print(f"[*] Target hash file: {args.target}")
    print("-" * 50)

    # 1. Load hashes from the target file
    target_hashes = load_hashes(args.target)
    
    if not target_hashes:
        print("[-] The target hash file is empty. Exiting program.")
        sys.exit(0)
        
    print(f"[*] Loaded {len(target_hashes)} hashes. Starting the cracking process...")

    # 2. Compare against the wordlist to crack passwords
    found_count = crack_passwords(target_hashes, args.wordlist)
    
    # 3. Print summary of the operation
    print("-" * 50)
    print(f"[*] Job completed. Found a total of {found_count} passwords.")

# Ensure the main() function is called only when the script is executed directly
if __name__ == "__main__":
    main()