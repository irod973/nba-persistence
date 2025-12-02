# Calculating persistence

This repo helps answer a question from an annoyingly entertaining math teacher:

> The "persistence" of a number:
> - Choose a two digit number.
> - Multiply the digits together until 1 digit.
> - Ex. 43-> 12 -> 2
> - So 43 would have “persistence of two” for the two jumps. 

> Which NBA player’s number has the largest persistence? (Answer with a pic for extra credit)

## Approach

I didn't want to worry about the data setup so I prompted both Gemini and ChatGPT for a script to get jersey numbers for all active NBA players. The latter failed but the former succeeded.

This ends up using the following unofficial third-party library: https://github.com/swar/nba_api

The rest is simply calculating the persistence of the numbers and sorting.

## Setup

```shell
uv sync --group nba_persistence
python gemini_persistence.py
```

## Tangent - Calculating persistence iteratively vs recursively 

I could think of two ways of calculating the persistence. A recursive approach means we can cache repeat calculations more efficiently.

This conjecture turned out correct (see script)
```
Brute: 0.0012s, Recursive: 0.0003s
```
