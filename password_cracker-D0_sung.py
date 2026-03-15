# This is the implementation of the list of hashes
# to create a new md5 to use, you can use the following command
#    echo -n word | md5sum - -t -z

import hashlib
import sys # Added to use sys.argv and sys.exit()

# Default values
passwordHashFilename = "password-hashes.txt"
wordlistFilename = "/usr/share/wordlists/rockyou.txt"

# -------------------------------------------------------------------------
# Assignment Requirement: Implementing Use Cases 1 ~ 4 using sys.argv
# -------------------------------------------------------------------------
# Check the length of sys.argv. (sys.argv[0] is the script filename itself, 
# so it is included in the total length.)
num_args = len(sys.argv)

if num_args == 1:
    # Use Case 1: No Parameters
    # Use the default values, so we do nothing and just pass.
    pass 

elif num_args == 2:
    # Use Case 2: 1 Parameter (Specify hash file path)
    passwordHashFilename = sys.argv[1]

elif num_args == 3:
    # Use Case 3: 2 Parameters (Specify both hash file and wordlist paths)
    passwordHashFilename = sys.argv[1]
    wordlistFilename = sys.argv[2]

else:
    # Use Case 4: 3 or More Parameters
    # Print the expected usage and exit the program.
    print("Expected Usage:")
    print(f"  [Use Case 1] Default: python {sys.argv[0]}")
    print(f"  [Use Case 2] Custom Hash file: python {sys.argv[0]} <path_to_password_hash_file>")
    print(f"  [Use Case 3] Custom Hash & Wordlist: python {sys.argv[0]} <path_to_password_hash_file> <path_to_wordlist_file>")
    sys.exit(1)
# -------------------------------------------------------------------------

# The 'b' option is important to ensure that the file is open as a byte stream.
# without the 'b' option, some files may have non-utf8 representable 
# characters that will fail the opening
# The use of the prefix "byteEncoded" is to reinforce the concept that we 
# are dealing with a byte encoded file being read
byteEncodedWordlist = open(wordlistFilename, 'rb')
byteEncodedHashlist = open(passwordHashFilename, 'rb')

passwordHashlist = []
for passwordHash in byteEncodedHashlist:
    passwordHashlist.append(passwordHash.rstrip().decode())

# This function takes a string (byte encoded) to be hashed.
def hashString(byteEncodedStringToHash):
    # using the md5 hashing algorithm
    hashAlgo = hashlib.md5(byteEncodedStringToHash)
    return hashAlgo.hexdigest()

for byteEncodedWord in byteEncodedWordlist:
    # At this point, the text is the full line (inclusive of the \n at the end of the file)
    # As the password is unlikely to be "abcdef\n", and is not the intention of the wordlist
    # this needs to be stripped.
    
    byteEncodedWord = byteEncodedWord.rstrip()
    
    ############################################################################################
    # IMPORTANT NOTE ABOUT PRINT: If you are printing a byte array/byte encoded string you will
    # notice the output being something like b'abcdef\n'
    # it is important to realise that the b'' is not part of the actual string, it's part of the
    # python representation of the string when printing.
    ############################################################################################

    # Calls our function that will hash a byte array (our byte encoded string)
    # important to remember that we are already receiving the "hexdigest" from
    # this function. We could have returned the hashAlgo directly from the
    # hashString function, and called the hexdigest() here.
    hashedEntry = hashString(byteEncodedWord)

    for hashedPasswordEntry in passwordHashlist:
        # Does the comparison against the supplied (hard-coded md5) and our calculated one
        # Again, if we didn't call hexdigest at any point, we will never get a match

        if(hashedEntry == hashedPasswordEntry):
            # Print the found password
            print("Password Found: ", byteEncodedWord.decode(), " for hash: ", hashedPasswordEntry)

            # This ensures that we don't attempt to match password hashes we've already found the
            # password for. We will also use this outside the 'inner' for-loop to end execution once
            # we don't have any more hashes to crack.
            passwordHashlist.remove(hashedPasswordEntry)
    
    # If we don't have any more hashes to find, break out of the for-loop
    if (len(passwordHashlist) == 0):
        break

# Once the previous for-loop is finished, we *should* have nothing in the passwordHashlist, unless we didn't find
# a matching hash. This is because we remove the hash when we find the matching password.
if(len(passwordHashlist) > 0):
    # Therefore, if we have entries in this list, it means we didn't find them.
    for unfoundEntry in passwordHashlist:
        print ("No password found for: ", unfoundEntry)