[![make.fun · the-picture-that-tastes-of-one-20261122-2047](https://make.fun/badge/the-picture-that-tastes-of-one-20261122-2047.svg)](https://make.fun/bounty/the-picture-that-tastes-of-one-20261122-2047?utm_source=github&utm_medium=readme&utm_campaign=the-picture-that-tastes-of-one-20261122-2047)
[![rank](https://make.fun/badge/the-picture-that-tastes-of-one-20261122-2047/Doritra/the-picture-that-tastes-of-one-20261122-2047/rank.svg)](https://make.fun/bounty/the-picture-that-tastes-of-one-20261122-2047/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=the-picture-that-tastes-of-one-20261122-2047)
[![reward](https://make.fun/badge/the-picture-that-tastes-of-one-20261122-2047/Doritra/the-picture-that-tastes-of-one-20261122-2047/reward.svg)](https://make.fun/bounty/the-picture-that-tastes-of-one-20261122-2047?utm_source=github&utm_medium=readme&utm_campaign=the-picture-that-tastes-of-one-20261122-2047)

# The picture that tastes of one ingredient

One picture of food, judged on how delicious it looks: a single ripe
strawberry, macro and glossy, filling the frame against a dark moody
background — scarlet flesh with a soft radial light, small golden
achenes in curved rows, a fresh green calyx, water droplets and a hard
specular gloss. One ingredient, one look, you can taste it.

`entry.png` is the 1024x1024 picture, drawn procedurally by
`build_image.py` (numpy + Pillow, no external assets, no network).
`main.py` copies it to `/output/entry.png` byte for byte.

## Run

    mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py

## Re-render

    python3 build_image.py
