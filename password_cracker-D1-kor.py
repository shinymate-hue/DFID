# 다중 해시 알고리즘과 패턴 대입 공격을 구현한 코드입니다.
# 새로운 MD5 해시를 테스트용으로 만들고 싶다면 리눅스 터미널에서 다음 명령어를 사용할 수 있습니다:
#    echo -n word | md5sum - -t -z
# SHA-512의 경우:
#    echo -n word | sha512sum - -t -z

from curses.ascii import isupper # (참고: 현재 코드에서는 실제로 사용되지 않는 라이브러리입니다)
import hashlib # 해시 암호화를 수행하기 위한 파이썬 내장 라이브러리

# ----------------------------------------------------------------------------------
# 기본 설정 변수들 (나중에는 사용자 입력이나 sys.argv로 받을 수 있습니다)
# ----------------------------------------------------------------------------------
passwordHashFileame = "password-hashes.txt" # 풀고자 하는 해시들이 들어있는 파일
hashAlgorithm = "md5"                       # 사용할 해시 알고리즘 (md5 또는 sha512)
wordlistFilenmae = "/usr/share/wordlists/rockyou.txt" # 사전 공격에 사용할 단어장 경로

crackType = "pattern"           # 공격 방식 선택: "pattern" (패턴 공격) 또는 "wordlist" (사전 공격)
passwordPattern = "Aaaa00"      # 패턴 공격을 시작할 첫 출발점 (형식 지정)

# 테스트용 타겟 해시: "Pass55"라는 단어를 MD5로 해시한 값입니다.
passwordHash = "3dec5fccd33913e15aa9e352ab59a1da" 


def hashString(byteEncodedStringToHash, algorithm):
    """
    바이트 형태의 문자열과 알고리즘 이름을 받아서 해시값으로 변환해주는 함수입니다.
    """
    if(algorithm == 'sha512'):
        # 사용자가 sha512를 지정했다면 SHA-512 알고리즘 사용
        hashAlgo = hashlib.sha512(byteEncodedStringToHash)
    else:
        # 그 외의 경우(기본값) MD5 알고리즘 사용
        hashAlgo = hashlib.md5(byteEncodedStringToHash)

    # 생성된 해시 객체를 16진수 문자열(예: '3dec5f...')로 반환합니다.
    return hashAlgo.hexdigest()

##################################################################################################
##################################################################################################
#                                   알고리즘 기본 원리 (패턴 공격)
#
# 이 알고리즘은 제공된 패턴의 가장 오른쪽 글자부터 시작해서 왼쪽으로 이동하며 
# 문자를 계속해서 1씩 증가시키는 방식(자동차의 주행거리계 원리)으로 작동합니다.
#
# 1. 가장 오른쪽 글자를 '현재 문자'로 잡고 시작합니다.
#      a. 다음 순서의 문자로 1 증가시킵니다. (예: a -> b, 1 -> 2)
# 2. 문자를 증가시켰을 때 '올림(overflow)'이 발생했다면 (예: z -> a, 9 -> 0)
#      a. 바로 왼쪽 자릿수로 이동합니다. 만약 더 이상 왼쪽으로 갈 수 없다면(인덱스 < 0), 패턴을 모두 소진한 것입니다.
#      b. '현재 문자'를 방금 이동한 왼쪽 문자로 갱신하고 다시 1을 증가시킵니다.
#
##################################################################################################
##################################################################################################

class CharacterResult:
    """
    개별 글자 하나를 증가시켰을 때의 결과를 담는 상자(클래스)입니다.
    overflow(올림) 개념: 글자가 'z'나 '9'처럼 끝에 도달해서 다시 처음('a'나 '0')으로 
    돌아갔을 때 True가 되어 왼쪽 자릿수를 올려야 함을 알려줍니다.
    """
    def __init__(self, char, overflow):
        self.character = char     # 바뀐 새로운 글자
        self.overflow = overflow  # 올림 발생 여부 (True/False)

class WordResult:
    """
    패턴에 따라 단어 전체를 변환했을 때의 결과를 담는 상자입니다.
    finished(완료) 개념: 주어진 패턴으로 만들 수 있는 모든 경우의 수를 다 시도했을 때 True가 됩니다.
    """
    def __init__(self, word, finished):
        self.word = word          # 바뀐 새로운 단어 전체
        self.finished = finished  # 모든 경우의 수 탐색 완료 여부 (True/False)


def Next_Character(currentCharacter):
    """
    현재 글자를 받아서 '다음 순서의 글자'가 무엇인지 계산하여 반환합니다.
    무차별 대입 공격이므로 문자는 정해진 순서대로 바뀌어야 합니다.
    """
    nextCharacter = None
    overflow = False # 기본적으로 올림은 발생하지 않았다고 가정합니다.

    # 현재 문자가 소문자인지, 대문자인지 판별하여 True/False를 저장합니다.
    # 문자의 ASCII 코드 값을 비교하여 범위를 확인합니다. (정규표현식을 사용하지 않은 원본 방식)
    isLowerCaseLetter = currentCharacter >= 'a' and currentCharacter <= 'z'
    isUpperCaseLetter = currentCharacter >= 'A' and currentCharacter <= 'Z'

    if isLowerCaseLetter or isUpperCaseLetter:
        # 알파벳(소/대문자)인 경우: 무조건 소문자로 바꾼 뒤 숫자로 변환(ord)하여 1을 더하고, 
        # 다시 문자(chr)로 되돌립니다. (예: 'a' -> 'b')
        nextCharacter = chr(ord(currentCharacter.lower()) + 1)

        # 문자가 'z'를 넘어갔다면, 다시 'a'로 되돌리고 올림(overflow)이 발생했다고 표시합니다.
        if(nextCharacter > 'z'):
            nextCharacter = 'a'
            overflow = True

        # 원래 글자가 대문자였다면, 소문자로 계산했던 결과를 다시 대문자로 되돌려줍니다.
        if isUpperCaseLetter:
            nextCharacter = nextCharacter.upper()
    else:
        # 알파벳이 아니라면 숫자라고 가정합니다. (0~9)
        # 문자를 정수(int)로 변환한 뒤 1을 더합니다.
        nextInteger = int(currentCharacter) + 1
        
        # 10으로 나눈 나머지(%)를 구합니다. 이렇게 하면 9+1=10이 되어도 0으로 돌아갑니다.
        nextCharacter = str(nextInteger % 10)
        
        # 더한 값이 9를 초과했다면(즉, 10이 되었다면) 올림(overflow)이 발생한 것입니다.
        overflow = nextInteger > 9
    
    # 바뀐 문자와 올림 발생 여부를 CharacterResult 객체에 담아 반환합니다.
    return CharacterResult(nextCharacter, overflow)


def Next_Word(word):
    """
    위에서 만든 Next_Character 함수를 활용하여 단어 전체를 다음 단계로 변화시킵니다.
    """
    # 단어(문자열)를 수정하기 쉽도록 글자 단위로 쪼개서 리스트로 만듭니다. (예: ['A', 'a', 'a', 'a', '0', '0'])
    charactersInWord = list(word)

    # 가장 오른쪽 끝 글자부터 시작하기 위해 인덱스를 구합니다. (전체 길이 - 1)
    characterIndex = charactersInWord.__len__() - 1
    currentCharacter = charactersInWord[characterIndex]

    # 가장 오른쪽 글자를 1 증가시킵니다.
    nextCharacter = Next_Character(currentCharacter)

    # 리스트에 있던 기존 글자를 새로 바뀐 글자로 교체합니다.
    charactersInWord[characterIndex] = nextCharacter.character
    
    # -------------------------------------------------------------------------
    # 연쇄 올림 처리 (while 루프)
    # 방금 글자를 증가시켰는데 올림(overflow)이 발생했다면, 왼쪽 글자도 올려주어야 합니다.
    # 인덱스가 -1보다 큰 동안(즉, 단어의 맨 앞자리를 벗어나지 않는 동안) 계속 왼쪽으로 이동합니다.
    # -------------------------------------------------------------------------
    while nextCharacter.overflow and characterIndex > -1:
        # 왼쪽 글자로 인덱스를 이동시킵니다.
        # (학생들이 고치도록 낸 문제: 여기서 -1을 지워버리면 무한 루프 에러가 납니다)
        characterIndex = characterIndex - 1 

        # 새로 이동한 위치의 글자를 '현재 문자'로 설정합니다.
        currentCharacter = charactersInWord[characterIndex]

        # 그 왼쪽 글자도 1 증가시킵니다.
        nextCharacter = Next_Character(currentCharacter)
    
        # 변경된 글자를 리스트에 업데이트합니다.
        charactersInWord[characterIndex] = nextCharacter.character

    # 리스트를 다시 하나로 합쳐서 문자열로 만듭니다. (''.join)
    # 만약 characterIndex가 0보다 작아졌다면(-1), 맨 앞자리까지 다 돌았다는 뜻이므로 finished=True가 됩니다.
    # (학생들이 고치도록 낸 문제: < 0 을 > 0 으로 바꾸면 로직 오류가 발생합니다)
    return WordResult(''.join(charactersInWord), characterIndex < 0) 


def TryPatternPasswordHash(fmt, passwordHash):
    """
    생성된 패턴 단어들을 해시로 변환해가며 타겟 해시와 일치하는지 무한히 검사하는 함수입니다.
    """
    # 최초 시작점 패턴을 WordResult 상자에 담습니다.
    current = WordResult(fmt, False)

    # 결과를 저장할 딕셔너리입니다. (찾았는지 여부, 찾은 비밀번호, 작업 완료 여부)
    patternAttackResult = { "Found": False, "Password": None, "Finished": False }

    # 작업이 완료될 때까지(Finished == True가 될 때까지) 계속 반복합니다.
    while(patternAttackResult["Finished"] == False):
        
        # Next_Word에서 더 이상 바꿀 조합이 없다고 판단(finished=True)했다면, 
        # 반복문을 종료할 수 있도록 상태를 변경합니다.
        if(current.finished):
            patternAttackResult["Finished"] = True

        # 현재 단어를 해시로 만들어서 우리가 찾는 비밀번호 해시와 비교합니다.
        if(hashString(current.word.encode(), hashAlgorithm) == passwordHash):
                # 일치한다면! 정답을 찾았으므로 결과를 저장하고 반복문을 끝냅니다.
                patternAttackResult["Found"] = True
                patternAttackResult["Finished"] = True
                patternAttackResult["Password"] = current.word
        else:
            # 일치하지 않는다면 다음 단어 조합을 가져와서 루프를 다시 돕니다.
            current = Next_Word(current.word)

        ######################################################################################
        # [주의] 아래 코드를 주석 해제하면 발생하는 논리 오류(Logic Error)에 대한 설명:
        # else문에서 다음 단어(current)를 가져왔는데, 만약 그 단어가 마지막 단어(finished=True)라면, 
        # 아래 코드가 실행되면서 즉시 루프가 끝나버립니다. 
        # 즉, '마지막으로 만들어진 단어'는 해시 비교(if문)를 거치지 못하고 프로그램이 종료되는 버그가 생깁니다.
        #
        # if(current.finished):
        #    patternAttackResult["Finished"] = True
        ######################################################################################

    return patternAttackResult


def TryWordlistPasswordHash():
    """
    이전 버전에서 사용했던 '사전 대입 공격(Wordlist Attack)' 로직을 함수 하나로 묶어둔 것입니다.
    """
    byteEncodedWordlist = open(wordlistFilenmae, 'rb')
    byteEncodedHashlist = open(passwordHashFileame, 'rb')

    passwordHashlist = []
    # 타겟 해시들을 리스트에 담습니다.
    for passwordHash in byteEncodedHashlist:
        passwordHashlist.append(passwordHash.rstrip().decode())

    # 단어장의 단어를 하나씩 꺼내어 해시로 만들고 비교합니다.
    for byteEncodedWord in byteEncodedWordlist:
        byteEncodedWord = byteEncodedWord.rstrip()
        hashedEntry = hashString(byteEncodedWord, hashAlgorithm)

        for hashedPasswordEntry in passwordHashlist:
            if(hashedEntry == hashedPasswordEntry):
                print("Password Found: ", byteEncodedWord.decode(), " for hash: ", hashedPasswordEntry)
                # 찾은 해시는 목록에서 제거하여 속도를 높입니다.
                passwordHashlist.remove(hashedPasswordEntry)
        
        # 해시를 모두 찾았다면 조기 종료합니다.
        if (len(passwordHashlist) == 0):
            break;

    # 끝까지 못 찾은 해시가 있다면 화면에 출력합니다.
    if(len(passwordHashlist) > 0):
        for unfoundEntry in passwordHashlist:
            print ("No password found for: ", unfoundEntry)


# ==================================================================================
# 프로그램 메인 실행 부
# ==================================================================================
# 처음에 설정한 crackType 변수값에 따라 어떤 공격 방식을 사용할지 결정합니다.

if(crackType == "wordlist"):
    # 사전 공격 모드 실행
    TryWordlistPasswordHash()
    
elif(crackType == "pattern"):
    # 패턴 공격 모드 실행 (패턴 시작점과 타겟 해시를 넘겨줍니다)
    patternAttackResult = TryPatternPasswordHash(passwordPattern, passwordHash)
    
    # 결과를 반환받아 화면에 출력합니다.
    if(patternAttackResult["Found"]):
        print("Password Found: ", patternAttackResult["Password"])
    else:
        print ("Password Not Found")
        
else:
    # 잘못된 타입이 입력되었을 경우 에러 메시지를 출력합니다.
    print("Invalid password crack type supplied. Use either 'pattern' or 'wordlist'")