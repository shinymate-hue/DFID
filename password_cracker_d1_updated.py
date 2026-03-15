import hashlib
import argparse
import sys
import re

# ==================================================================================
# 핵심 로직 (정규표현식을 사용한 패턴 판별 및 해시 함수)
# ==================================================================================

def hashString(byteEncodedStringToHash, algorithm):
    """지정된 알고리즘을 사용하여 바이트 문자열을 해시값으로 변환합니다."""
    algo_name = algorithm.lower().replace("-", "")
    try:
        hashAlgo = getattr(hashlib, algo_name)()
        hashAlgo.update(byteEncodedStringToHash)
        return hashAlgo.hexdigest()
    except AttributeError:
        print(f"[!] 에러: 지원하지 않는 해시 알고리즘입니다. ({algorithm})")
        sys.exit(1)

class CharacterResult:
    def __init__(self, char, overflow):
        self.character = char
        self.overflow = overflow

class WordResult:
    def __init__(self, word, finished):
        self.word = word
        self.finished = finished

def Next_Character(currentCharacter):
    """정규표현식을 사용하여 문자를 판별하고 다음 문자로 증가시킵니다."""
    nextCharacter = None
    overflow = False

    isLowerCaseLetter = bool(re.match(r'[a-z]', currentCharacter))
    isUpperCaseLetter = bool(re.match(r'[A-Z]', currentCharacter))

    if isLowerCaseLetter or isUpperCaseLetter:
        nextCharacter = chr(ord(currentCharacter.lower()) + 1)
        if nextCharacter > 'z':
            nextCharacter = 'a'
            overflow = True
        if isUpperCaseLetter:
            nextCharacter = nextCharacter.upper()
    else:
        nextInteger = int(currentCharacter) + 1
        nextCharacter = str(nextInteger % 10)
        overflow = nextInteger > 9
    
    return CharacterResult(nextCharacter, overflow)

def Next_Word(word):
    """단어의 맨 오른쪽 끝에서부터 자릿수를 올려가며 다음 단어 조합을 생성합니다."""
    charactersInWord = list(word)
    characterIndex = len(charactersInWord) - 1
    currentCharacter = charactersInWord[characterIndex]

    nextCharacter = Next_Character(currentCharacter)
    charactersInWord[characterIndex] = nextCharacter.character
    
    while nextCharacter.overflow and characterIndex > -1:
        characterIndex = characterIndex - 1 
        
        if characterIndex < 0:
            break
            
        currentCharacter = charactersInWord[characterIndex]
        nextCharacter = Next_Character(currentCharacter)
        charactersInWord[characterIndex] = nextCharacter.character

    return WordResult(''.join(charactersInWord), characterIndex < 0)

# ==================================================================================
# 공격 모드별 실행 함수
# ==================================================================================

def TryPatternPasswordHash(start_pattern, target_hash, algorithm):
    """패턴 대입 공격을 수행합니다."""
    print(f"[*] 패턴 공격 시작 (시작점: {start_pattern}, 타겟: {target_hash})")
    current = WordResult(start_pattern, False)
    patternAttackResult = { "Found": False, "Password": None, "Finished": False }

    while not patternAttackResult["Finished"]:
        if current.finished:
            patternAttackResult["Finished"] = True

        if hashString(current.word.encode(), algorithm) == target_hash:
                patternAttackResult["Found"] = True
                patternAttackResult["Finished"] = True
                patternAttackResult["Password"] = current.word
        else:
            current = Next_Word(current.word)

    return patternAttackResult

def TryWordlistPasswordHash(hash_file, wordlist_file, algorithm):
    """단어장(사전) 대입 공격을 수행합니다."""
    print(f"[*] 사전 공격 시작 (해시 파일: {hash_file}, 단어장: {wordlist_file})")
    try:
        with open(wordlist_file, 'rb') as byteEncodedWordlist, open(hash_file, 'rb') as byteEncodedHashlist:
            passwordHashlist = [h.rstrip().decode() for h in byteEncodedHashlist]
            total_hashes = len(passwordHashlist)

            for byteEncodedWord in byteEncodedWordlist:
                byteEncodedWord = byteEncodedWord.rstrip()
                hashedEntry = hashString(byteEncodedWord, algorithm)

                for hashedPasswordEntry in passwordHashlist[:]: 
                    if hashedEntry == hashedPasswordEntry:
                        print(f"[+] Password Found: {byteEncodedWord.decode()} (Hash: {hashedPasswordEntry})")
                        passwordHashlist.remove(hashedPasswordEntry)
                
                if len(passwordHashlist) == 0:
                    break
            
            if len(passwordHashlist) > 0:
                print(f"[-] 남은 {len(passwordHashlist)}개의 해시에 대한 비밀번호를 찾지 못했습니다.")
                for unfound in passwordHashlist:
                    print(f"    -> 못 찾은 해시: {unfound}")
            else:
                print(f"[*] 축하합니다! {total_hashes}개의 해시를 모두 크랙했습니다.")

    except FileNotFoundError as e:
        print(f"[!] 에러: 파일을 찾을 수 없습니다. 경로를 확인해주세요. ({e.filename})")
        sys.exit(1)

# ==================================================================================
# 메인 함수 (Command Line Arguments 파싱)
# ==================================================================================

def main():
    parser = argparse.ArgumentParser(
        description="고급 패스워드 크래커 (패턴 기반 무차별 대입 및 사전 공격 지원)",
        epilog="예시:\n"
               "  사전 공격: python script.py -m wordlist -f hashes.txt -w rockyou.txt\n"
               "  패턴 공격: python script.py -m pattern -p Aaaa00 -t 3dec5fccd33913e15aa9e352ab59a1da",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    parser.add_argument('-m', '--mode', choices=['pattern', 'wordlist'], required=True, 
                        help="실행 모드 선택: 'pattern' 또는 'wordlist'")
    parser.add_argument('-a', '--algo', default='md5', 
                        help="해시 알고리즘 (기본값: md5. 예: sha256, sha512)")
    
    parser.add_argument('-f', '--hashfile', help="크랙할 해시들이 담긴 파일 경로 (wordlist 모드 필수)")
    parser.add_argument('-w', '--wordlist', help="사용할 단어장 파일 경로 (wordlist 모드 필수)")
    
    parser.add_argument('-t', '--target', help="크랙할 단일 타겟 해시값 (pattern 모드 필수)")
    parser.add_argument('-p', '--pattern', help="패턴 공격 시작점 (예: Aaaa00) (pattern 모드 필수)")
    
    # -------------------------------------------------------------------------
    # 추가된 부분: 사용자가 스크립트 이름만 입력하고 아무 인자도 넣지 않았을 때
    # 에러를 발생시키기 전에 전체 도움말(Help)을 출력하고 종료합니다.
    # -------------------------------------------------------------------------
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
        
    args = parser.parse_args()
    print("-" * 50)
    
    if args.mode == 'wordlist':
        if not args.hashfile or not args.wordlist:
            parser.error("wordlist 모드에서는 '-f (해시 파일)'와 '-w (단어장)' 위치를 반드시 지정해야 합니다.")
        
        TryWordlistPasswordHash(args.hashfile, args.wordlist, args.algo)
        
    elif args.mode == 'pattern':
        if not args.target or not args.pattern:
            parser.error("pattern 모드에서는 '-t (타겟 해시)'와 '-p (시작 패턴)'을 반드시 지정해야 합니다.")
        
        result = TryPatternPasswordHash(args.pattern, args.target, args.algo)
        
        if result["Found"]:
            print(f"[+] Password Found: {result['Password']}")
        else:
            print("[-] Password Not Found.")
            
    print("-" * 50)

if __name__ == "__main__":
    main()