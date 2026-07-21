"""Discover Q3 — проблемы взаимодействия, данные для вкладки Discover.

Источник правды по контенту — wiki/interaction_problems_research.md (verbatim, verified).
Здесь — структура для рендера на вкладке + расслоение (решения Guzel 21.07):
  п2: колонки помечены этапом Double Diamond (Проблема=Discover, Цель=Define,
      Как учтено=Develop, Рекрутер=meta) — документ смешивал этапы, делаем это явным.
  п3: у каждой «цели» проставлен ТИП design-intent (POV / goal / principle / requirement) —
      колонка «цель» была смесью; теги — ПЕРВЫЙ проход Claude, Guzel проверяет.

⚠️ ЧЕКАП (Guzel, 22.07): колонки «team» местами неточны (писались по догадке) → «рекрутер»
производно тоже. Проблема-цитаты и «goal» — выверены; теги goal_type и team/рекрутер — на сверку.

goal_type: "POV" | "goal" | "principle" | "requirement" (см. память project-discover-define-cleanup).
"""
from __future__ import annotations

# Ось A — дашборд как продукт (adoption для продуктовых ролей).
AXIS_A_BLOCKS: list[dict] = [
    {
        "source": "BARC",
        "url": "https://barc.com/infographic-bi-analytics-adoption-strategies/",
        "problem": "5 факторов, что «almost instantaneously kill BI/analytics adoption». "
                   "Adoption «25% on average», «stuck in the 20% range».",
        "note": "",
        "rows": [
            {"label": "«the data needed is not available or accessible»",
             "goal": "у каждой роли на её виде есть нужные данные, без барьеров доступа",
             "goal_type": "requirement",
             "team": "✅ данные ролей на вкладках, без gating · ⚠️ mock",
             "rec_obs": "базовая грамотность: данные для ролей доступны",
             "rec_self": "рекрутеру всё доступно сразу"},
            {"label": "«the data isn't trustworthy»",
             "goal": "честно показывать происхождение; не выдавать симуляцию за реальность",
             "goal_type": "principle",
             "team": "✅ провенанс real/demo (DASH-117), метки «симуляция»",
             "rec_obs": "🌟 зрелость — не выдаёт симуляцию за факт",
             "rec_self": "доверяет тому, что видит"},
            {"label": "«the tools aren't flexible or easy to use»",
             "goal": "easy: ноль барьеров · «flexible» (наша трактовка): per-role вид",
             "goal_type": "requirement + principle",
             "team": "✅ без логина, один клик · вкладка на роль. ⚠️ BARC «flexible» не определяет",
             "rec_obs": "продумана лёгкость + per-role",
             "rec_self": "заходит одним кликом"},
            {"label": "«query performance is slow»",
             "goal": "субсекундный отклик; минимизировать причины",
             "goal_type": "requirement",
             "team": "✅ fra, тёплый старт <1с, client-render, малый датасет",
             "rec_obs": "инженерная осознанность PD — редкость",
             "rec_self": "грузится быстро"},
            {"label": "«there aren't enough people to coach or support business users»",
             "goal": "продукт самообъясняющийся — не требует coach'а",
             "goal_type": "principle",
             "team": "✅ North Star «понимает без объяснений» · 🔧 онбординг DASH-53 не построен",
             "rec_obs": "замысел «без гида» + честный пробел",
             "rec_self": "🔧 без гида может слегка потеряться"},
        ],
    },
    {
        "source": "RevealBI",
        "url": "https://www.revealbi.io/blog/dashboard-adoption-problem",
        "problem": "«They require context switching. They aren't tied to immediate actions».",
        "note": "Строки = роли (у каждой своё «немедленное действие»); последняя — uniform.",
        "rows": [
            {"label": "PM", "goal": "привязать к ритуалу стендапа/планинга (пн/чт)",
             "goal_type": "principle", "team": "✅ Kanban/Overview под ритм",
             "rec_obs": "вид PM привязан к ритуалу", "rec_self": "N/A"},
            {"label": "Product Analyst", "goal": "к моменту разбора эксперимента",
             "goal_type": "principle", "team": "✅ Analytics · PA",
             "rec_obs": "привязка к разбору эксперимента", "rec_self": "N/A"},
            {"label": "QA", "goal": "к go/no-go перед релизом",
             "goal_type": "principle", "team": "✅ Quality (Go/No-Go)",
             "rec_obs": "привязка к go/no-go", "rec_self": "N/A"},
            {"label": "Product Designer", "goal": "к разбору дизайн-долга/итераций",
             "goal_type": "principle", "team": "🔧 частично (DASH-50 не построен)",
             "rec_obs": "частичная привязка — пробел", "rec_self": "N/A"},
            {"label": "Uniform (context switching)", "goal": "свести фазы в одно место, меньше переключений",
             "goal_type": "principle", "team": "✅ весь SDLC в одном дашборде · ⚠️ демонстрация",
             "rec_obs": "всё в одном месте", "rec_self": "не надо прыгать между тулами"},
        ],
    },
    {
        "source": "dubdubdata",
        "url": "https://www.dubdubdata.com/blog/why-dashboards-fail",
        "problem": "«Dashboards don't drive decisions, people do» — проваливаются, когда построены "
                   "«for the wrong thing», не под решение пользователя.",
        "note": "Строки = роли (у каждой своё решение); последняя — uniform.",
        "rows": [
            {"label": "PM", "goal": "«куда вмешаться» → блокеры, здоровье",
             "goal_type": "goal", "team": "✅ Overview + Roadmap",
             "rec_obs": "вид ведёт к решению", "rec_self": "N/A"},
            {"label": "Product Analyst", "goal": "«kill / scale эксперимента»",
             "goal_type": "goal", "team": "✅ Analytics · PA",
             "rec_obs": "вид под решение kill/scale", "rec_self": "N/A"},
            {"label": "QA", "goal": "«go / no-go на релиз»",
             "goal_type": "goal", "team": "✅ Quality (Go/No-Go)",
             "rec_obs": "вид под go/no-go", "rec_self": "N/A"},
            {"label": "Product Designer", "goal": "«что чинить» → дизайн-долг, a11y",
             "goal_type": "goal", "team": "🔧 Design (a11y); DASH-50 не построен",
             "rec_obs": "частично — пробел", "rec_self": "N/A"},
            {"label": "Uniform", "goal": "не давать сырые данные без «ради какого решения»",
             "goal_type": "principle", "team": "частично",
             "rec_obs": "данные под решение, не свалка", "rec_self": "видит смысл, а не сырые цифры"},
        ],
    },
]

# Теги типов design-intent — цвет для бейджа на вкладке.
GOAL_TYPE_COLOR: dict[str, str] = {
    "POV": "plum",
    "goal": "teal",
    "principle": "iris",
    "requirement": "amber",
    "requirement + principle": "amber",
}
