# Char-sheet промпты — каст Motif (11 героев)

> Фундамент консистентности. По каждому герою — один лист: **фас / 45° / профиль**.
> Модель: Nano Banana 2 (в Krea) или Nano Banana Pro напрямую. Источник образов — `team_world_bible.md` §2 / `motif_world.py CAST`.
> Промпты на английском (модели так надёжнее); в скобках — заметки по-русски.

## Как использовать
1. Определись со **стилем** (см. STYLE ниже) — сгенерь 1 тестовый кадр, зафиксируй, не меняй.
2. Прогони **11 char-sheets** с одним и тем же STYLE-блоком в начале каждого промпта.
3. Отбери лучший лист на каждого героя → это твои **референсы**. В каждом кадре комикса подаёшь нужные листы + «keep facial features exactly as reference».
4. Сгенерь **групповой lineup** (в конце файла) — фиксирует относительный рост/пропорции ансамбля.
5. Пол/возраст/этнос ниже — **дефолты, меняй под своё видение**. Главное: выбрала → зафиксировала в листе → больше не меняешь.

---

## STYLE (вставляй в начало КАЖДОГО промпта)
```
Character reference sheet, three views of the SAME person in one image: front view, 3/4 (45°) view, side profile. Neutral standing pose, plain warm off-white background, soft even lighting. Consistent modern editorial comic illustration style: clean confident linework, semi-flat cel shading, warm friendly palette, expressive but grounded (not chibi, not photoreal). Full body visible, character sheet layout with the three views side by side.
```

---

## 11 персонажей (добавляй после STYLE-блока)

**1. Ким — CEO / фаундер** *(энерджайзер-визионер)*
```
Subject: KIM, startup founder, late 20s, androgynous energetic vibe, bright intense eyes, messy short hair. Wardrobe: a well-worn zip hoodie, sneakers. Signature prop: a coffee mug in hand. Expression: charismatic, slightly restless, always pitching.
```

**2. Дэн — PM** *(якорь ритма)*
```
Subject: DAN, product manager, early 30s, male, tidy neat appearance, calm composed face, short combed hair, simple button-up. Signature props: sticky notes and a small whiteboard. Expression: steady, reassuring, the mediator.
```

**3. Марко — Lead Dev / SA** *(прагматик-скептик)*
```
Subject: MARCO, lead developer, 30s, male, unflappable deadpan expression, glasses, dark casual t-shirt. Signature props: a mechanical keyboard, three monitors behind him. Expression: dry, skeptical, quietly competent.
```

**4. Софи — UX Researcher / BA** *(голос юзера)*
```
Subject: SOPHIE, UX researcher, late 20s, female, warm gentle presence, soft curly hair, cozy cardigan. Signature props: a voice recorder and a stack of interview notes. Expression: attentive listener, kind.
```

**5. Прия — Product Analyst / Growth** *(цифры-первый)*
```
Subject: PRIYA, product/growth analyst, late 20s, female, South Asian, sharp focused look, dark hair in a practical style. Signature props: metric dashboards on a screen, a second coffee mug. Expression: eager, competitive, data-driven.
```

**6. Ая — PD · Product Designer** 🎯 *(роль Guzel; эмпат-ремесленник, один из ансамбля)*
```
Subject: AYA, product designer, late 20s, female, warm empathetic expression, cozy oversized sweater. Signature props: a drawing tablet with stylus, a sketchbook always nearby. Expression: thoughtful, caring, quietly perfectionist.
```

**7. Лея — Frontend Dev** *(быстрая, играющая)*
```
Subject: LEIA, frontend developer, mid 20s, female, colorful dyed hair streaks, over-ear headphones around neck, laptop covered in stickers. Expression: fast, playful, energetic.
```

**8. Том — QA** *(дотошный «адвокат дьявола»)*
```
Subject: TOM, QA engineer, 30s, male, calm meticulous demeanor, neat glasses, plaid shirt. Signature props: a checklist clipboard, a magnifying glass. Expression: friendly but scrutinizing, detail-obsessed.
```

**9. Ли — Community Manager** 🌟 *(экстраверт-эмпат, внешний голос бренда)*
```
Subject: LEE, community manager, mid 20s, male, expressive extroverted face, headphones on, casual graphic tee. Background hint: a wall of community memes. Expression: warm, chatty, always in the chats.
```

**10. Реми — Scrum Master (part-time)** *(фасилитатор-миротворец)*
```
Subject: REMI, scrum master, 30s, androgynous calm friendly presence, gentle smile, relaxed casual clothes. Signature props: a small timer, retrospective cards. Expression: warm, mediating, keeps the peace.
```

**11. Нур — Artist-in-Residence** 🌟 *(ремесленник-пурист, dogfooding)*
```
Subject: NUR, artist-in-residence, 20s, gender-flexible, ink-stained fingers, expressive artistic look, a vintage t-shirt with a comic print. Signature props: a sketchbook and a drawing tablet. Expression: passionate purist, craft-first.
```

---

## Групповой lineup (после того как листы готовы — фиксирует пропорции ансамбля)
```
[STYLE block] Group lineup of all 11 Motif team members standing side by side, full body, same consistent style, each recognizable by their signature wardrobe and props, neutral background, even lighting. Left to right: Kim (hoodie, coffee), Dan (sticky notes), Marco (glasses, deadpan), Sophie (recorder, cardigan), Priya (dashboards, coffee), Aya (tablet, sweater), Leia (colored hair, headphones), Tom (checklist, magnifier), Lee (headphones, graphic tee), Remi (timer, smile), Nur (ink-stained, comic tee).
```

## Советы по консистентности
- **Один STYLE-блок везде** — стиль дрейфует первым.
- **Держи имена в промпте** (KIM, AYA…) — помогает семантическому трекингу Nano Banana.
- **1-2 «якоря» на героя** (у Леи — цветные пряди; у Нура — чернильные пальцы; у Марко — три монитора) — по ним модель узнаёт персонажа в кадре.
- В сценах — **макс 5 фокусных героев** с листами; остальные фоном/со спины (лимит модели).
- Лица «плывут» → в кадре добавляй «keep facial features exactly the same as the reference sheet».
