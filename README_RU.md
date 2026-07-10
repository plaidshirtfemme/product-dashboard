# Product Dashboard

> **В разработке** — активная разработка, v0.1

Продуктовый портфолио-дашборд, построенный на [Reflex](https://reflex.dev) (Python → React, без JS-файлов).  
Демонстрирует продуктовое мышление на всех этапах SDLC — от дискавери до мониторинга.

[README in English](README.md)

---

## Что это такое

Интерактивный дашборд, который показывает реальный программный проект через призму каждой продуктовой роли:  
PM, BA, SA, Дизайнер, PA, Dev, QA, Growth и другие.

Дашборд поддерживает **3 режима проекта**, переключаемых в реальном времени:
- **Motif Demo** — вымышленная продуктовая команда с генерируемыми Jira-подобными данными
- **Knowledge Pipeline** — реальный соло-AI-проект (YouTube → заметки Obsidian через Claude API)
- **Product Dashboard** — сам дашборд, показанный как продуктовый проект с реальной историей спринтов

**North Star:** *«Рекрутер понимает продуктовый контекст без объяснений».*

---

## Что готово сейчас

**Техническая база**
- 17 SDLC-вкладок: About, Practices & Rules, Kanban, Backlog, Roadmap, Overview/PM, Research, Analytics, Architecture, Requirements, Design, Design System, Dev & Pipeline, Quality, Release, Monitoring, Growth
- Все вкладки построены и доступны (нет пустых страниц)
- 3 режима проекта с переключением через дропдаун в реальном времени
- Дизайн-токены в формате W3C (`design_tokens.json`), совместимы с Figma Tokens Studio
- Hand-authored Jira-данные: 88 задач с полной историей спринтов, эпиками, decision notes
- Реактивные фильтры в Backlog (squad, тип, спринт, эпик, OKR)
- Аккордеон-навигация: Design System вложена под Design
- `USER_STORIES.md` — 17 ролей × 100+ пользовательских историй

**Реальные данные проекта (режим Knowledge Pipeline)**
- Метрики пайплайна: созданные заметки, время обработки, использование токенов
- Снэпшот Obsidian-vault: структура папок, количество заметок
- Architecture Decision Records из реального README
- Чеклист качества из реального security-ревью

---

## Что в разработке

- [ ] Figma-файлы: wireframes и hi-fi макеты (дизайн-процесс виден в коде, но ещё не в Figma)
- [ ] GitHub release с публичным URL (сейчас только локально)
- [ ] Онбординг для рекрутера: tooltips, coach marks
- [ ] Вкладка Design Process: journey map, HMW, user flow
- [ ] Комикс/сценарий: история 2-недельного спринта с дневниками ролей
- [ ] Framer-портфолио со ссылкой на этот дашборд

---

## Как запустить локально

**Требования:** Python 3.11+, Node.js 18+

```bash
git clone https://github.com/plaidshirtfemme/product-dashboard.git
cd dashboard-product
pip install -r requirements.txt
reflex run
```

Открыть [http://localhost:3000](http://localhost:3000)

> **Примечание:** Первый запуск занимает 1–2 минуты — Reflex компилирует фронтенд.  
> Последующие запуски быстрее.

---

## Стек технологий

| Слой | Технология |
|------|-----------|
| Фреймворк | [Reflex](https://reflex.dev) 0.9.x — Python → React |
| UI-компоненты | Radix UI через Reflex |
| Дизайн-токены | Формат W3C Design Tokens |
| Данные | Hand-authored Jira mock + реальные данные проекта |
| Python | 3.11+ |

---

## Структура проекта

```
dashboard_product/
├── dash_app/
│   ├── pages/          # один файл на вкладку
│   ├── components/     # переиспользуемые UI-компоненты
│   ├── states/         # Reflex state (NavState, ProjectState, BacklogState…)
│   ├── data/           # mock-данные, адаптер, реальные данные проекта
│   └── tokens/         # дизайн-токены → Python
├── scripts/            # скрипт обновления снэпшота vault
├── wiki/               # дневники ролей, PM-заметки
├── USER_STORIES.md     # 17 ролей × 100+ пользовательских историй
└── rxconfig.py
```

---

*Создано Guzel Karimova · Product Designer & PM · 2026*
