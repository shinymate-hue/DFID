import hashlib
import argparse
import sys

def load_hashes(file_path):
    """
    해시값이 저장된 파일을 읽어와서 set(집합) 형태로 반환합니다.
    set을 사용하면 리스트(list)보다 검색 속도가 훨씬 빠릅니다.
    """
    hashes_to_find = set() # 중복을 제거하고 검색 속도를 높이기 위해 set 사용
    
    try:
        # with 구문을 사용하면 작업이 끝난 후 파일이 자동으로 닫힙니다.
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                # 줄바꿈 문자를 제거하고, 안전하게 소문자로 통일하여 저장합니다.
                hashes_to_find.add(line.strip().lower())
        return hashes_to_find
        
    except FileNotFoundError:
        print(f"[!] 에러: 해시 파일을 찾을 수 없습니다. 경로를 확인해 주세요: {file_path}")
        sys.exit(1) # 에러 발생 시 안전하게 프로그램 종료
    except Exception as e:
        print(f"[!] 에러: 해시 파일을 읽는 중 알 수 없는 문제가 발생했습니다: {e}")
        sys.exit(1)

def crack_passwords(target_hashes, wordlist_path):
    """
    워드리스트 파일을 읽어 각 단어의 MD5 해시를 계산한 뒤,
    target_hashes에 해당 해시값이 존재하는지 대조합니다.
    """
    found_count = 0
    
    try:
        # 'rb'(바이트 읽기) 모드로 열어 문자열 인코딩 에러를 방지합니다.
        with open(wordlist_path, "rb") as wordlist_file:
            for word_bytes in wordlist_file:
                # 줄바꿈 문자 등 공백 제거
                word_bytes = word_bytes.rstrip()

                # 바이트 데이터의 MD5 해시를 계산하고 16진수(hex) 문자열로 변환
                hashed_entry = hashlib.md5(word_bytes).hexdigest()

                # 계산된 해시가 찾고자 하는 해시 목록(set)에 있는지 확인 (매우 빠른 연산)
                if hashed_entry in target_hashes:
                    try:
                        # 일치한다면 바이트 배열을 ascii(또는 utf-8) 문자열로 디코딩
                        word_string = word_bytes.decode('utf-8')
                        print(f"[+] 비밀번호 발견! | 해시: {hashed_entry} -> 비밀번호: {word_string}")
                        found_count += 1
                    except UnicodeDecodeError:
                        print(f"[!] 비밀번호를 찾았으나 문자열로 디코딩할 수 없습니다. (Hex: {word_bytes.hex()})")

    except FileNotFoundError:
        print(f"[!] 에러: 워드리스트 파일을 찾을 수 없습니다. 경로를 확인해 주세요: {wordlist_path}")
        sys.exit(1)
    except Exception as e:
        print(f"[!] 에러: 워드리스트를 처리하는 중 문제가 발생했습니다: {e}")
        sys.exit(1)
        
    return found_count

def main():
    # argparse를 설정하여 명령줄에서 인자를 받습니다.
    parser = argparse.ArgumentParser(description='워드리스트를 사용하여 MD5 해시 비밀번호를 크랙합니다.')
    
    # -w (필수): 워드리스트 파일
    parser.add_argument('-w', '--wordlist', dest='wordlist', required=True, help='사용할 워드리스트 파일 경로')
    # -t (선택): 해시 파일 (기본값 설정)
    parser.add_argument('-t', '--target', dest='target', default='password-hashes.txt', help='크랙할 해시가 담긴 파일 (기본값: password-hashes.txt)')

    args = parser.parse_args()

    print(f"[*] 워드리스트 파일: {args.wordlist}")
    print(f"[*] 타겟 해시 파일: {args.target}")
    print("-" * 50)

    # 1. 파일에서 해시 목록 불러오기
    target_hashes = load_hashes(args.target)
    
    if not target_hashes:
        print("[-] 타겟 해시 파일이 비어있습니다. 프로그램을 종료합니다.")
        sys.exit(0)
        
    print(f"[*] 총 {len(target_hashes)}개의 해시를 로드했습니다. 크래킹을 시작합니다...")

    # 2. 워드리스트와 대조하여 크랙 시도
    found_count = crack_passwords(target_hashes, args.wordlist)
    
    # 3. 결과 요약
    print("-" * 50)
    print(f"[*] 작업 완료. 총 {found_count}개의 비밀번호를 찾았습니다.")

# 스크립트가 직접 실행될 때만 main() 함수를 호출합니다.
if __name__ == "__main__":
    main()