---
theme: ../dist/slidev
title: Слайды из markdown
info: |
  Демонстрационная дека темы Slidev этого репозитория: обложка, списки, две колонки,
  разделитель, код, таблица, цифра, цитата и ссылки
layout: cover
class: has-art
---

<figure class="ddlc-figure">
  <img src="/ui-light.png" alt="Веб-кит этого репозитория на светлой стороне" />
  <figcaption>Веб-кит этого репозитория</figcaption>
</figure>

# Слайды из markdown

Дека, которая живёт в git

---
layout: default
---

# Зачем это нужно

- Дека — это **текст**, а не бинарник: диффится, ревьюится, живёт рядом с кодом
- Правка одной строки не двигает остальные слайды
- Один исходник даёт **PDF для сдачи** и живую деку для показа
- Цвета и шрифты приходят из одного источника, а не из головы автора

---
layout: two-cols-header
---

# Две колонки

::left::

## Идея

Слева объясняют контекст и называют вопрос, на который отвечает доклад

::right::

## Результат

Справа помещаются выводы, следующий шаг или короткое сравнение подходов

---
layout: section
---

# Как это выглядит

---
layout: two-cols-header
---

# Текст и изображение

::left::

## Бумага

Изображение в теме висит на бумаге, как фотография на доске: тонкая рамка, подпись под чертой

::right::

<figure class="ddlc-figure">
  <img src="/report-dark.png" alt="Стиль отчёта на тёмной стороне" />
  <figcaption>Стиль отчёта этого репозитория</figcaption>
</figure>

---
layout: default
---

# Код на слайде

```bash
slidev slides.md            # живая дека
slidev export slides.md     # PDF, 16:9, со шрифтами внутри
```

Блок кода — окно kitty этого репозитория: тёмное на обеих схемах, с полосой сверху

---
layout: default
---

# Сравнение

| | Тема дек | Обычная презентация |
| --- | --- | --- |
| Исходник | markdown в git | бинарник |
| Диффы | построчные | нет |
| Правки агентом | дешёвые | дорогие |

---
layout: fact
---

# 2 с

сборка деки из markdown

---
layout: statement
---

Дека — это текст в git, и это меняет всё: её можно править, ревьюить и собирать заново

---
layout: quote
---

> Хороший слайд говорит одно. Всё остальное говорит докладчик

<div class="attribution">Правило, проверенное на защитах</div>

---
layout: links
---

## Где меня найти

<div class="ddlc-contact">

**Сайт**

[rokokol.github.io/ddlc-themes](https://github.com/rokokol/ddlc-themes)

</div>

<div class="ddlc-contact">

**Исходники**

[github.com/rokokol/ddlc-palette](https://github.com/rokokol/ddlc-palette)

</div>
