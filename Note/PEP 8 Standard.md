파이썬의 공식 스타일 가이드인 **PEP 8**에서 요청하신 주요 항목들에 대한 핵심 요약과 예제입니다.

### 1. 들여쓰기 (Indentation)

* **원칙:** 공백(Space) **4칸**을 사용합니다. 탭(Tab)보다는 공백 사용을 권장하며, 두 방식을 섞어서 사용하면 안 됩니다.
* **예제:**
```python
# 올바름: 4칸 들여쓰기
def my_function():
    if True:
        print("Hello")

```

### 2. 공백 (Whitespace)

* **원칙:** 불필요한 공백은 피하되, 가독성을 위해 연산자 주변에 한 칸씩 사용합니다. 괄호 바로 안쪽에는 공백을 넣지 않습니다.
* **예제:**
```python
# 올바름
x = (y + z) * (a - b)

# 잘못됨
x = ( y + z ) * ( a-b ) 

```

### 3. 빈 줄 (Blank Lines)

* **원칙:** 최상위(Top-level) 함수와 클래스 정의 사이에는 **두 줄**을 띄웁니다. 클래스 내부의 메서드 사이에는 **한 줄**을 띄웁니다.
* **예제:**
```python
class MyClass:
    def method_one(self):
        pass

    def method_two(self):
        pass


def top_level_function():
    pass

```

### 4. 임포트 (Imports)

* **원칙:** 각 임포트는 별도의 줄에 작성하며, 파일의 맨 위(모듈 설명 및 docstring 다음)에 위치시킵니다.
* **예제:**
```python
# 올바름
import os
import sys
from subprocess import Popen, PIPE

```

### 5. 문자열 따옴표 (String Quotations)

* **원칙:** 작은따옴표(`'`)와 큰따옴표(`"`) 중 어느 것을 사용해도 무방하지만, 하나를 선택해 일관되게 사용합니다. 문자열 내에 따옴표가 포함된 경우, 백슬래시(`\`) 대신 다른 종류의 따옴표를 사용하여 가독성을 높입니다.
* **예제:**
```python
# 가독성 좋은 예
print("It's a beautiful day") 

```

### 6. 네이밍 컨벤션 (Naming Conventions)

* **클래스:** `CapWords` (PascalCase) 방식을 사용합니다.
* **변수:** `lower_case_with_underscores` (snake_case) 방식을 사용합니다.
* **상수:** `UPPER_CASE_WITH_UNDERSCORES` (대문자 스네이크 케이스)를 사용합니다.

### 7. 함수 이름 (Function Names)

* **원칙:** 변수와 마찬가지로 **소문자**로 작성하며, 가독성을 위해 필요한 경우 **밑줄(`_`)**로 단어를 구분합니다.
* **예제:**
```python
def calculate_total_price(amount, tax):
    return amount + tax

```
