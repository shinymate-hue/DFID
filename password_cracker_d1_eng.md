Here is the complete story of how the program works, from the moment you press "run" to the moment it either finds the password or gives up.

Imagine you are trying to crack a mechanical combination lock or watching a car's odometer roll over. Let's walk through it step-by-step!

### 🚦 Step 1: Program Starts & Sets the Target

* You run the script. The program checks its settings and enters **"pattern attack"** mode.
* It sets the starting word to **`Aaaa00`**.
* It sets the target hash we want to crack to **`3dec...`** (the hidden password's hash).
* It dives into the `TryPatternPasswordHash` function and starts an endless `while` loop.

### ⚙️ Step 2: The First Try (`Aaaa00`)

* It takes the current word (`Aaaa00`) and puts it through the `hashString` function to create an MD5 hash.
* It compares this newly created hash to our target hash (`3dec...`).
* **Result:** They don't match (the lock doesn't open).
* Since it failed, it goes to the `else` block and calls the `Next_Word("Aaaa00")` function. It is basically saying, *"Spin the dial one click!"*

### 🔄 Step 3: Spinning the Dial (`Aaaa00` $\rightarrow$ `Aaaa01`)

* The `Next_Word` function grabs the rightmost character (the last `0`) and adds 1 to it.
* The word becomes **`Aaaa01`**.
* Because the number just went from 0 to 1, there is no "overflow." The program takes this new word and jumps back to Step 2 to test it.

### 🌊 Step 4: The Domino Effect / Overflow (`Aaaa09` $\rightarrow$ `Aaaa10`)

* After many failed attempts, the word eventually becomes **`Aaaa09`**.
* The `Next_Word` function adds 1 to the rightmost `9`. The number resets to **`0`**, which triggers an alarm: **"Overflow!"**
* Hearing this overflow alarm, the program moves one space to the left (to the other `0`) and adds 1 to it.
* The word transforms into **`Aaaa10`**. The program takes this updated word and goes back to the endless loop to test it.

---

From here, the story splits into two possible endings!

### 🟢 Ending A: Happy Ending (The Password is Found!)

* After a few hours of spinning the dials, the word happens to become **`Pass55`**.
* It hashes this word, and boom! It perfectly matches our target hash (`3dec...`). *Click!* The lock opens.
* The program joyfully updates its notes: `Found = True` (we found it!) and `Finished = True` (the job is done!).
* Because `Finished` is now true, the endless `while` loop finally stops.
* The program returns to the main menu and proudly prints on your screen: **"Password Found: Pass55"**.

### 🔴 Ending B: Sad Ending (Reaching `Zzzz99` with no luck)

What if the real password was something like `apple!@#`, which doesn't fit our `Aaaa00` pattern at all?

* The program tirelessly tests every single combination until it hits the absolute last one: **`Zzzz99`**.
* `Zzzz99` is also wrong. It calls `Next_Word("Zzzz99")`.
* Adding 1 to the last `9` causes an overflow. This triggers a massive chain reaction (like falling dominoes): the `9`s become `0`s, the `z`s become `a`s, and finally, the capital `Z` turns back into an `A`.
* The program tries to move left again to carry over the overflow, but it realizes there are no more dials left to spin (the index goes below 0, or `-1`).
* The `Next_Word` function waves a white flag. It sets `finished = True`, meaning: *"There are absolutely no combinations left to try."*
* The `while` loop sees this flag and stops. However, because it never found a match, the `Found` status remains **`False`**.
* The program exits the loop, goes to the main menu, and sadly prints: **"Password Not Found"**.

---

Hopefully, this story makes the logic crystal clear!

Would you like me to help you write a tiny, separate Python script to test *just* the `Next_Word` function so you can watch the "odometer" roll over in real-time on your screen?