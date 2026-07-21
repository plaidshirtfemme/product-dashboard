# Проблемы взаимодействия — Discover Q3 (research)

> Артефакт этапа Discover (DASH-60). Q3: где стыки, что теряется/тормозит.
> Оси: **A** — дашборд как продукт для продуктовых ролей (adoption); **B** — стыки ролей (handoff).
> Собрано 21.07.2026.

> ⚠️ **ЧЕКАП НУЖЕН (Guzel, 22.07):** колонки **«Как учтено сейчас (команда)»** местами заполнены
> неточно (Claude писал по догадке/памяти), и производная колонка **«рекрутер»** из-за этого тоже
> может быть неверна. Нужна сверка обеих. **Проблема-цитаты (verbatim) и «цель» — выверены**; ошибки
> в основном в оценке «как учтено» и в рекрутер-колонке.

## Дисциплина источников (правило CLAUDE.md 21.07)
- Проблема — **прямой цитатой + контекст**, не пересказ. Источники **не смешиваем**; каждый блок = свой
  источник, verbatim, verified. Все ссылки — **проверены как живые** (зафетчены). Что «испарялось» при
  проверке — отброшено.
- Колонки: **Проблема** (verbatim) · **Цель** · **Как учтено (команда)** · **Рекрутер** (🔍 наблюдатель
  качества решения / 👤 что ощущает сам как зритель; для Оси B «сам» ≈ N/A — рекрутер не в стыке).

---

## Ось A — дашборд как продукт (adoption для продуктовых ролей)

### Блок BARC — 5 факторов, убивающих adoption
[BARC — Strategies for Driving Adoption and Usage](https://barc.com/infographic-bi-analytics-adoption-strategies/). Adoption «25% on average», «stuck in the 20% range».

| Проблема (BARC, verbatim) | Цель | Как учтено (команда) | Рекрутер |
|---|---|---|---|
| «the data needed is not available or accessible» | у каждой роли на её виде есть нужные данные, без барьеров | ✅ данные ролей на вкладках, без gating · ⚠️ mock | 🔍 базовая грамотность: данные для ролей доступны<br>👤 рекрутеру всё доступно сразу |
| «the data isn't trustworthy» | честно показывать происхождение; не выдавать симуляцию за реальность | ✅ провенанс real/demo (DASH-117), метки «симуляция» | 🔍 🌟 зрелость — не выдаёт симуляцию за факт<br>👤 доверяет тому, что видит |
| «the tools aren't flexible or easy to use» | easy: ноль барьеров · «flexible» (наша трактовка): per-role вид | ✅ без логина, один клик · вкладка на роль. ⚠️ BARC «flexible» не определяет | 🔍 продумана лёгкость + per-role<br>👤 заходит одним кликом |
| «query performance is slow» | субсекундный отклик; минимизировать причины | ✅ fra, тёплый старт <1с, client-render, малый датасет | 🔍 инженерная осознанность PD — редкость<br>👤 грузится быстро |
| «there aren't enough people to coach or support business users» | продукт самообъясняющийся — не требует coach'а | ✅ North Star «понимает без объяснений» · 🔧 онбординг DASH-53 не построен | 🔍 замысел «без гида» + честный пробел<br>👤 🔧 без гида может слегка потеряться |

### Блок RevealBI — привязка к действию / context switching
[RevealBI — Why Dashboard Adoption Fails](https://www.revealbi.io/blog/dashboard-adoption-problem).
**Проблема** · «They require context switching. They aren't tied to immediate actions».

| Роль | Цель | Как учтено (команда) | Рекрутер |
|---|---|---|---|
| PM | к ритуалу стендапа/планинга (пн/чт) | ✅ Kanban/Overview под ритм | 🔍 вид PM привязан к ритуалу<br>👤 N/A |
| Product Analyst | к моменту разбора эксперимента | ✅ Analytics · PA | 🔍 привязка к разбору эксперимента<br>👤 N/A |
| QA | к go/no-go перед релизом | ✅ Quality (Go/No-Go) | 🔍 привязка к go/no-go<br>👤 N/A |
| Product Designer | к разбору дизайн-долга/итераций | 🔧 частично (DASH-50 не построен) | 🔍 частичная привязка — пробел<br>👤 N/A |
| Uniform (context switching) | свести фазы в одно место, меньше переключений | ✅ весь SDLC в одном дашборде · ⚠️ демонстрация | 🔍 всё в одном месте<br>👤 рекрутеру не надо прыгать между тулами |

### Блок dubdubdata — «don't drive decisions»
[DubDub — Why Dashboards Fail](https://www.dubdubdata.com/blog/why-dashboards-fail).
**Проблема** · «Dashboards don't drive decisions, people do» — проваливаются, когда построены «for the wrong thing», не под решение пользователя.

| Роль | Цель: какое решение поддержать | Как учтено (команда) | Рекрутер |
|---|---|---|---|
| PM | «куда вмешаться» → блокеры, здоровье | ✅ Overview + Roadmap | 🔍 вид ведёт к решению<br>👤 N/A |
| Product Analyst | «kill / scale эксперимента» | ✅ Analytics · PA | 🔍 вид под решение kill/scale<br>👤 N/A |
| QA | «go / no-go на релиз» | ✅ Quality (Go/No-Go) | 🔍 вид под go/no-go<br>👤 N/A |
| Product Designer | «что чинить» → дизайн-долг, a11y | 🔧 Design (a11y); DASH-50 не построен | 🔍 частично — пробел<br>👤 N/A |
| Uniform | не давать сырые данные без «ради какого решения» | частично | 🔍 данные под решение, не свалка<br>👤 рекрутер видит смысл, а не сырые цифры |

---

## Ось B — стыки между ролями (handoff)
*(«ощущает сам» ≈ N/A: рекрутер не участник стыка, только наблюдатель качества.)*

### Блок Actuation Consulting (2014) — где рвётся
[Actuation Consulting — Product Team Handoffs](https://actuationconsulting.com/product-team-handoffs-likely-problematic/). ⚠️ 2014 г.; даёт **где** рвётся, не **что** передаётся, без определения «handoff».
**Проблема** · % проблемных handoff'ов по парам: PM↔Dev **20.26%** · PM↔project mgr 13.40% · Dev↔QA 13.08% · PM↔ops 11.21% · PM↔BA 10.90% · Dev↔ops 9.03% · project mgr↔Dev 8.41% · project mgr↔ops 5.30% · project mgr↔QA 4.67% · QA↔ops 3.74%. Агрегат: «56% of the handoff issues involve product managers and roughly a third project managers».

| Что говорит источник | Цель | Как учтено (команда) | Рекрутер |
|---|---|---|---|
| концентрация на PM (56%) | максимум видимости PM-центричным стыкам | ✅ Overview · PM + кросс-вкладочный | 🔍 дал PM кросс-обзор под реальный риск<br>👤 N/A |
| топ-пары: PM↔Dev, Dev↔QA, PM↔BA | приоритет видимости | ✅ общая доска + связи issue↔bug + Analysis | 🔍 приоритизировал видимость топ-стыков<br>👤 N/A |

*«Что передаётся» — из нашего артефакта «Карта обмена артефактами» (ARTIFACTS, Q2), не из Actuation.*

### Блок Figma (2025) — желание улучшить (без механики)
[Figma — What developers want from designers](https://www.figma.com/reports/designer-developer-collaboration/). ⚠️ фиксирует желание, конкретных болей не называет.
**Проблема** · «91% of developers and 92% of designers say the handoff process needs improvement»; «92% of developers would like designers to know more about the development process»; «55% of front-end developers would like to be brought into the design process earlier».

| Что хотят стороны | Цель | Как учтено (команда) | Рекрутер |
|---|---|---|---|
| дизайнеры знают разработку; фронт вовлекают раньше | ранняя совместная работа; дизайнер понимает обе стороны | ✅ **автор — и дизайнер, и разработчик**; токены = общий язык | 🔍 🌟 designer-который-кодит закрывает design↔dev разрыв<br>👤 N/A |

### Блок Miro — структурный механизм
[Miro — Product Design to Dev Handoff](https://miro.com/product-development/product-design-to-dev-handoff/).
**Проблема** · «most teams use separate tools for separate phases of the work, which means **handoffs are where decisions go to die**»; «71% of leaders say switching between tools causes friction and interrupts workflows»; «reasoning behind key decisions has often evaporated».

| Механизм (Miro) | Цель | Как учтено (команда) | Рекрутер |
|---|---|---|---|
| разные тулы под фазы → «decisions go to die» | свести фазы в связанное пространство; хранить «почему» | ✅ весь SDLC в дашборде · `decision_note`/ADR хранят reasoning | 🔍 хранит reasoning, фазы в одном месте<br>👤 сам видит «почему» решений в попапах (bonus) |
| «71% … switching between tools causes friction» | меньше переключений | ✅ единая поверхность · ⚠️ демонстрация | 🔍 единая поверхность<br>👤 рекрутеру не надо прыгать между тулами |

### Блок Uplevel — деградация знания
[Uplevel — Why Warm Engineering Handoffs Won't Fix Your Delivery Problems](https://uplevelteam.com/blog/engineering-handoffs) (Nonaka & Takeuchi / SECI).
**Проблема** · «This first handoff already introduces interpretation layers»; «The moment you convert it to a ticket or spec, you strip away nuance like a game of Telephone»; «tacit knowledge — the user's actual experience, context, and unstated assumptions — can't be captured in writing».

| Механизм (Uplevel) | Цель | Как учтено (команда) | Рекрутер |
|---|---|---|---|
| перевод в тикет/спеку «strips away nuance»; tacit теряется | хранить контекст и «почему»; меньше передач | ✅ `decision_note`/ADR хранят reasoning · 🔧 tacit системно не фиксируем | 🔍 хранит контекст решений + честный предел<br>👤 N/A |

### Блок Figr — flows vs states
[Figr — Developer Handoff: Tools, Templates, Playbook](https://figr.design/blog/developer-handoff-playbook-tools-templates-and-best-practices-for-cross-functional-teams).
**Проблема** · «Designers think in flows and visuals. Engineers think in states and logic» — инженеру нужны состояния/edge-cases, которых в макете нет: «what happens when the user enters invalid data? What's the loading state? Which component from our library do I use? What about mobile?».

| Механизм (Figr) | Цель | Как учтено (команда) | Рекрутер |
|---|---|---|---|
| дизайнер даёт поток/визуал, инженеру нужны состояния/edge-cases | фиксировать состояния/edge-cases; общий компонент-словарь | ✅ автор мыслит и как инженер; Ant/токены = словарь · 🔧 edge-cases не документируем | 🔍 мыслит состояниями (пишет фронт) + честный пробел edge-cases<br>👤 N/A |

### QA-стык — честный пробел (блок НЕ берём)
**Проблема поздней передачи в QA реальна, но чистого верифицируемого источника именно про
функциональный QA не нашли.** Всё, что попадалось, — одно из трёх:
- **Старое:** NIST 2002 — «code first, test later costs the U.S. economy $59.5 billion annually» (реальное гос-исследование, 2002 г.).
- **Контестед (зомби-стат):** «баг в проде дороже в 100× / IBM Systems Sciences Institute» — первоисточник не проследить, не используем.
- **Adjacent-домен:** [GitLab / sdxcentral](https://www.sdxcentral.com/news/gitlab-survey-shows-dev-sec-tensions-amid-shift-left-push/) — «security vulnerabilities are still most likely to be found by security teams after the code is in a test environment» (GitLab 2022, 5000 респ.) — но это **security shift-left**, не функциональный QA. По той же причине убран блок Gartner (marketing-домен).

Решение (21.07): QA-блок не форсируем; фиксируем пробел честно.

---

## Источники (проверены как живые)
- BARC — https://barc.com/infographic-bi-analytics-adoption-strategies/
- RevealBI — https://www.revealbi.io/blog/dashboard-adoption-problem
- DubDub — https://www.dubdubdata.com/blog/why-dashboards-fail
- Actuation Consulting — https://actuationconsulting.com/product-team-handoffs-likely-problematic/
- Figma — https://www.figma.com/reports/designer-developer-collaboration/
- Miro — https://miro.com/product-development/product-design-to-dev-handoff/
- Uplevel — https://uplevelteam.com/blog/engineering-handoffs
- Figr — https://figr.design/blog/developer-handoff-playbook-tools-templates-and-best-practices-for-cross-functional-teams
- GitLab/sdxcentral (QA-note, adjacent) — https://www.sdxcentral.com/news/gitlab-survey-shows-dev-sec-tensions-amid-shift-left-push/
