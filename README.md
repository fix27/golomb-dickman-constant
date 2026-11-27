# Постоянная Голомба–Дикмана: сертифицированные вычисления

$$\lambda=\int_0^\infty F(u)\,du,\qquad F(u)=e^{-u-E_1(u)}
=0.624329988543550870992936383100837244\ldots$$

Здесь $E_1$ — интегральная показательная функция. В репозитории лежат
вычисления этой константы в интервальной арифметике с явным сертификатом
точности: 30 000 знаков (первая версия), 40 000 знаков, 50 000 знаков и
**75 000 знаков** (текущий результат, релиз `v75000`).

## Автор

**Поздняков Константин Николаевич** — расчёты, код, сертификаты и подготовка
пакета. Сургут, ХМАО — Югра, Россия. Почта:
[fix@inbox.ru](mailto:fix@inbox.ru).

В англоязычных метаданных и в препринте используется форма
**Konstantin N. Pozdnyakov**, Surgut, Khanty-Mansi Autonomous Okrug — Yugra,
Russia. Машиночитаемая цитата — [`CITATION.cff`](CITATION.cff), метаданные
Zenodo — [`.zenodo.json`](.zenodo.json), препринт — [`paper/`](paper/),
готовые письма для OEIS/SeqFan/MathWorld — [`submission/`](submission/).

## Текущий результат: 75 000 знаков (релиз v75000)

Сертификат
[`75000/golomb_dickman_75000_certified.txt`](75000/golomb_dickman_75000_certified.txt)
содержит целые $\Lambda_-<\Lambda_+$ и масштаб $S=249341$ такие, что

$$\left\lfloor 10^{75000}\Lambda_-/2^S\right\rfloor
=\left\lfloor 10^{75000}\Lambda_+/2^S\right\rfloor .$$

Значит, первые **75 000** десятичных знаков (усечение, не округление) выведены
из интервала точной целочисленной арифметикой.

| Величина | Значение |
|---|---|
| Сертифицировано знаков $D$ | 75 000 |
| Масштаб $S$ | 249 341 |
| Ширина интервала | $5.8205594787\times10^{-75043}$ |
| Запасные (guard) знаки сверх 75 000 | 42.2350 |
| Узлы Arb | **476 648 всего**, из них **проверено 2 000** (20 блоков) |
| Блоки чекпоинтов | **4 767** блоков по 100 узлов, план `gd-checkpoint-v13` |
| Полный Arb-аудит всех узлов | **не выполнялся** (см. «База доверия») |

Параметры прогона (`75000/gd_rigorous_ckpt_75000/meta_v13.json`, он же
`make_plan(75000)` продюсера v27):

| Параметр | Значение |
|---|---|
| $h$ (шаг сетки) | $54\,039\,302/2^{40}=4.9148458856507204\times10^{-5}$ |
| $K_L,K_R$ | 231 270, 245 377 |
| $E_{\mathrm{bits}}$, $EG_{\mathrm{bits}}$ | 249 277, 362 151 |
| $B$ | 1 |
| $T_R$ | 4 201 793 744 629 |
| $T_L$ | 34 129 286 600 574 252 |
| $C=T_R+T_L+B$ | 34 133 488 394 318 882 |
| $\log_{10}B_{\mathrm{disc}}$ | $-77368.1704$ |
| $\log_{10}\tau_R$ / $\log_{10}\tau_L$ | $-75046.4967$ / $-75042.5870$ |
| $\log_{10}(\Lambda_+-\Lambda_-)-S\log_{10}2$ | $-75042.2350352685$ |

### Артефакты 75 000 знаков

| Что | Файл |
|---|---|
| Сертификат, продюсер v27, чекпоинты, манифест SHA-256 | [`75000/`](75000/) |
| Подробное описание прогона и оговорки | [`75000/README.md`](75000/README.md) |
| Release notes | [`RELEASE_v75000.md`](RELEASE_v75000.md) |
| Отчёт аудита сертификата | [`audit/06-75000.md`](audit/06-75000.md) |
| Статистика цифр | [`audit/07-75000-statistics.md`](audit/07-75000-statistics.md) |
| Препринт | [`paper/main-75000.tex`](paper/main-75000.tex) |

### Быстрая проверка (уровень A, только стандартная библиотека Python)

```bash
python verification/verify_certificate.py \
    --cert 75000/golomb_dickman_75000_certified.txt \
    --digits-file golomb_dickman_75000_digits.txt \
    --sha256-manifest 75000/SHA256SUMS.txt \
    --compare 50000/golomb_dickman_50000_digits.txt
```

Скрипт проверяет, что интервал не пересекает границу десятичной ячейки, что
цифры равны $\lfloor 10^{75000}\lambda\rfloor$, что файл цифр согласован с
сертификатом и манифестом, что первые 102 знака совпадают с OEIS A084945 и что
первые 50 000 знаков совпадают с сертификатом на 50 000 знаков. При расхождении
завершается ненулевым кодом.

### Контрольные суммы 75 000 (каноническая форма, LF)

```text
b177fc551c8a9f950e037fdc92ed72fb9219eb11d81999410967f8013e6df534  golomb_dickman_75000_certified.txt
0c5f2b212eb5fd25b1def672226f65f46b97d44c5e371c5db10ab1cef9b468aa  golomb_dickman_75000_digits.txt
f5a02374d79b4ca6af889a9c4a63b53fe265bc3c861a1c20dc2683c696e781ea  golomb_dickman_27.py
ee9dfe75ea130c15c8a3ade41d6994bcb734d413c1c49e2cd58b39ab31bbf8f9  gd_rigorous_ckpt_75000/meta_v13.json
```

Полный список — в [`75000/SHA256SUMS.txt`](75000/SHA256SUMS.txt). Хеш сам по
себе ничего не доказывает: он лишь связывает имя файла с байтами и должен
сверяться с доверенным эталоном (`verify_certificate.py` печатает
`MATCH (manifest)` только при наличии манифеста, иначе честно выводит
`computed, UNVERIFIED (no trusted reference)`).

### Что проверено для 75 000

| Проверка | Инструмент | Результат |
|---|---|---|
| точная целочисленная проверка 75 000 знаков | `verification/verify_certificate.py` | PASS |
| совпадение с корневым файлом цифр и манифестом | там же | PASS |
| первые 50 000 / 40 000 знаков прежних результатов | там же, `--compare` | PASS |
| план `make_plan(75000)` против `meta_v13.json` | импорт продюсера | PASS, 8 параметров |
| 4 767 блоков: без дыр и дублей, точные суммы | `verification/audit_chunks.py` | PASS |
| ширина по суммам блоков против ширины сертификата | там же | $3.232\times10^{-75043}$ против $5.8205594787\times10^{-75043}$ |
| независимая квадратура (tanh-sinh, Gauss–Legendre, mpmath) | `verification/independent_quadrature.py` | PASS: 320 совпадающих знаков при запросе 300 |
| пересчёт **всех** узлов в Arb | `verification/verify_all_arb.py` | **NOT_RUN** (см. ниже) |

Статистический и структурный анализ цифр (частоты, серии, энтропия,
автокорреляция, шаблоны, сжатие, цепные дроби) воспроизводится командой
`python audit/75000_statistics.py --digits golomb_dickman_75000_digits.txt`;
результаты носят численный, а не доказательный характер.

## Предыдущие результаты

Полные описания, команды и оговорки — в подкаталогах. Здесь — только сводка,
чтобы не дублировать факты.

### 50 000 знаков

| Параметр | Значение |
|---|---|
| Масштаб $S$ | 166 293 |
| Ширина интервала | $4.390\times10^{-50043}$ (более 42 запасных знаков) |
| Блоки чекпоинтов | **3 076** блоков по 100 узлов (307 580 узлов), план `gd-checkpoint-v12` |
| Продюсер | [`50000/golomb_dickman_26.py`](50000/golomb_dickman_26.py) |
| Описание | [`50000/README.md`](50000/README.md) |
| Манифест | [`50000/SHA256SUMS.txt`](50000/SHA256SUMS.txt) |

```text
76f4155981049003351409769505c3cec39e26dfc30624c46bd199e70ed6477a  golomb_dickman_50000_certified.txt
8f017d45ee5108bb6b976882b079279f44f8a767ce62b44bd7c54e9167ad09a0  golomb_dickman_50000_digits.txt
1e3d23e9ac3ce51990d83decd395d6bde96027f43811b94cebd5a6a4b7c19c43  b084945.txt
78783a09bae599298a07415056b0ca521717c9f7ecaa1fd15cb19b4d5ab6b0e0  gd_rigorous_ckpt_50000/meta_v12.json
e2eb7d4ccca761c5c5e1f2b37075f9baea245dac86cbe962fd9dc92aa574ef71  golomb_dickman_26.py
```

### 40 000 знаков

| Параметр | Значение |
|---|---|
| Ширина интервала | $10^{-40042.2602491239}$ (около 42 запасных знаков) |
| Блоки чекпоинтов | **1 209** блоков, формат `meta.pkl`, `chunk=200` (241 688 узлов) |
| Поправки | $B=1$, $T_R+T_L+B=65\,673\,984\,721\,697$ |
| Продюсер | [`40000/golomb_dickman.py`](40000/golomb_dickman.py) |
| Описание | [`40000/README.md`](40000/README.md) |
| Методика проверки | [`40000/VERIFICATION.md`](40000/VERIFICATION.md) |

```text
8892c0715f1afbb271c9f07cc9658cea0f3ca83c2dda3ec7d23b447dc908de9c  golomb_dickman_40000_certified.txt
fbae757900983bd4fb6421c5f27bf9602af1a1bfc013e4c501bb9da2b5a65327  golomb_dickman_40000_digits.txt
c73af643198da299d2e624e3c2f69d05439efcddbbefa7cec176ac63f993bed3  b084945.txt
99377813ec9c48ed84cf4649067f4ba4ee3fb7ef74f15102bf92f75cdd400324  golomb_dickman.py
047ff0471acb07482be15a5cdfc7a65ef14c3193372022e3b1dc9b144098e0ee  smoke_60.txt
```

## База доверия и уровни проверки

### Доказано

При явно перечисленной ниже базе доверия доказаны:

- корректность интервала $[\Lambda_-,\Lambda_+]\ni\lambda$ для 75 000 знаков;
- ширина интервала $5.8205594787\times10^{-75043}$;
- усечение первых 75 000 десятичных знаков (обе границы дают одно и то же
  усечение, поэтому цифры не «вычислены приближённо», а доказаны);
- корректность **2 000 проверенных узлов** из 476 648 (20 блоков из 4 767):
  все они contained.

### Не доказано (ограничение)

- **Полный независимый пересчёт всех 476 648 узлов в Arb не выполнялся.**
  На машине сборки `python-flint` не загружается из-за Application Control
  (`WinError 4551`, блокируется загрузка `libflint`/`libgmp`). По измеренной
  скорости полный прогон занимает около 9 ч на 4 потоках (≈3 ч на 11) и в
  рамках лимита на процесс не запускался. До его завершения сертификат
  опирается на исходный прогон продюсера v27.
- Полного аудита узлов в Arb нет и для 50 000, и для 40 000 знаков — по той же
  причине.
- Нормальность $\lambda$ в базе 10 остаётся открытой проблемой; всё, что
  относится к статистике цифр, — численные наблюдения, а не доказательство.
- Это расширение результата, а не заявка на мировой рекорд.

### База доверия (явно перечисленная)

1. корректность интервальной арифметики [Arb](https://arblib.org/)
   (`python-flint`);
2. теорема о трапециях для аналитических функций в полосе
   (Trefethen & Weideman, *SIAM Review* 56 (2014), Thm 5.1);
3. классическая теорема Стилтьеса о двусторонних оценках подходящими дробями;
4. леммы из docstring вычислителя (§1–§7);
5. точная целочисленная арифметика Python.

Это не проверка в proof assistant.

### Уровни проверки

| Уровень | Команда | Что даёт | Чего не даёт |
|---|---|---|---|
| A | `python verification/verify_certificate.py --cert 75000/golomb_dickman_75000_certified.txt --digits-file golomb_dickman_75000_digits.txt --sha256-manifest 75000/SHA256SUMS.txt --compare 50000/golomb_dickman_50000_digits.txt` | SHA-256, ширина интервала, цифры, согласованность с префиксом OEIS, совпадение с 50 000 знаками; секунды, без сторонних пакетов | не доказывает, что $\lambda$ лежит в интервале |
| B | `python verification/level_b.py` | параметры, $B_{\mathrm{disc}}$, хвосты, формулы и 12 блоков, пересчитанных заново | не пересчитывает enclosure в Arb |
| B′ | `python verification/audit_chunks.py --ckpt 75000/gd_rigorous_ckpt_75000 --cert 75000/golomb_dickman_75000_certified.txt` | непрерывность 4 767 блоков и воспроизведение концов интервала из точных сумм | не заменяет пересчёт узлов в Arb |
| C | `python verification/independent_quadrature.py --digits 300` | независимое воспроизведение цифр другой библиотекой и другой квадратурой | **не является строгим доказательством**: используется плавающая точка, только численное подтверждение |

Уровни A, B и B′ не импортируют вычислитель и не используют плавающую точку в
решающих проверках; уровень C — численная перепроверка в `mpmath`.

Оговорка по B′ для 75 000: `verification/audit_chunks.py` и
`verification/verify_all_arb.py` пока ищут только `meta_v12.json`, а в
`75000/` лежит `meta_v13.json`. Для прогона использовалось временное зеркало
вне репозитория с преобразованным `meta_v12.json`; сами чекпоинты и план не
менялись (см. [`75000/README.md`](75000/README.md)).

### Экспериментальные наработки

Каталоги [`coq/`](coq/) и [`lean/`](lean/) содержат экспериментальную
формализацию отдельных лемм (Coq/mathcomp, Lean/Mathlib). Они **не входят в
базу доверия текущего сертификата** и не заменяют его.

## Воспроизведение

### Требования

- Python 3.11+;
- [`mpmath`](https://mpmath.org/) — только для `crosscheck` и независимой
  квадратуры (уровень C);
- [`python-flint`](https://github.com/flintlib/python-flint) (Arb) —
  **обязателен только для полного Arb-аудита всех узлов** (уровень проверки с
  полным пересчётом). Для базовой проверки целостности сертификата и цифр
  (уровень A) достаточно стандартной библиотеки Python;
- желательно многоядерный CPU: расчёт распараллеливается по процессам.

```bash
python -m pip install python-flint mpmath   # только для уровней B (Arb) и C
```

### CLI текущего результата (v27)

Результат на 75 000 знаков получен CLI
[`golomb_dickman_27.py`](golomb_dickman_27.py); план прогона —
`gd-checkpoint-v13`, команды и параметры — в
[`75000/README.md`](75000/README.md).

```bash
python golomb_dickman_27.py test
python golomb_dickman_27.py smoke
python golomb_dickman_27.py certify --digits 75000
python golomb_dickman_27.py crosscheck --digits 200
python golomb_dickman_27.py boundary-test
```

- `test` — самопроверка окружения и точные рациональные проверки леммы 7;
- `smoke` — сквозной прогон на 60 знаках;
- `certify --digits 75000` — полный сертификат; пишет
  `golomb_dickman_<D>_certified.txt` в текущий каталог и сохраняет чекпоинты
  в `gd_rigorous_ckpt_<D>/` (значение по умолчанию для `--digits` — 40 000);
- `crosscheck` — независимые сверки через `mpmath`/`mpmath.iv`, цепные дроби,
  форсированные ветви, альтернативный шаг и лестницу точности;
- `boundary-test` — граничные тесты леммы 7.

Полный прогон занимает **часы CPU**; его можно прерывать, прогресс сохраняется
в чекпоинтах. Режим `--resume` — только аудиторский: он доверяет готовым
чекпоинтам, не пересчитывает их и **не выдаёт сертификат**. По умолчанию
работает безопасный режим `--no-resume`: каждый блок пересчитывается в Arb.

> **Не запускайте `certify` внутри `75000/`, `50000/` или `40000/` —
> потеряются опубликованные чекпоинты.** Каталог по умолчанию —
> `gd_rigorous_ckpt_<D>/` в текущем каталоге, то есть тот же, где лежат
> опубликованные блоки: 4 767 в `75000/` (план `meta_v13.json`, `chunk=100`),
> 3 076 в `50000/` (`meta_v12.json`, `chunk=100`) и 1 209 в `40000/`
> (формат `meta.pkl`, `chunk=200`). Продюсер пишет свой план и чужой не
> проверяет, поэтому часть файлов `c_*.pkl` будет перезаписана блоками
> другого размера. Исходный набор восстанавливается только полным пересчётом.
> Для нового счёта используйте пустой каталог или явный `--ckpt`, а
> опубликованные каталоги считайте read-only артефактами.

Для 40 000 знаков исторический пайплайн запускается отдельно
(`cd 40000 && python golomb_dickman.py`); повторный прогон перезаписывает
`smoke_60.txt` и сертификат в текущем каталоге, поэтому делайте его в копии
каталога и пересчитывайте манифест.

## Важно для пользователей Windows

- Перед клонированием выполните `git config --global core.autocrlf input`
  (или `false`). Политика LF для текстовых файлов закреплена в
  [`.gitattributes`](.gitattributes), но при `core.autocrlf=true` рабочая
  копия всё равно может получить CRLF.
- Если файлы уже получили CRLF, `sha256sum -c` и `verify_certificate.py`
  начнут падать на контрольных суммах, а b-file перестанет соответствовать
  требованиям OEIS (ASCII, LF, без BOM). В этом случае переключите `autocrlf`
  и переклонируйте репозиторий; для ручной сверки используйте
  `Get-FileHash * -Algorithm SHA256` на LF-копии.
- Запись сертификата и `smoke_60.txt` на Windows идёт без `newline="\n"`,
  поэтому повторный прогон вычислителя даёт CRLF и ломает манифест — считайте
  его только в копии каталога.

## Дубликаты файлов в корне

`golomb_dickman_75000_certified.txt`, `golomb_dickman_75000_digits.txt` и
`golomb_dickman_27.py` в корне репозитория — **байтовые копии** файлов из
[`75000/`](75000/), оставленные для удобства (быстрый доступ без перехода в
подкаталог). Каноническим путём считается `75000/`; манифест
[`75000/SHA256SUMS.txt`](75000/SHA256SUMS.txt) содержит обе записи по имени
файла.

## B-file для OEIS A084945

Опубликованный в OEIS b-file содержит только **102 знака** (`n = 0..101`).
Файл [`submission/b084945.txt`](submission/b084945.txt) на 75 000 знаков
является **черновиком и пока не отправлен**.

| Файл | Термы | Размер | SHA-256 | Статус |
|---|---:|---:|---|---|
| [`50000/b084945.txt`](50000/b084945.txt) | `n = 0..49999` | 388 891 B | `1e3d23e9…c19c43` | готовый файл предыдущего результата |
| [`40000/b084945.txt`](40000/b084945.txt) | `n = 0..39999` | 308 891 B | `c73af643…993bed3` | готовый файл предыдущего результата |
| [`submission/b084945.txt`](submission/b084945.txt) | `n = 0..74999` | 588 891 B | `05584c9d3f0afccbfb9a1d8c8f28177a33a30be3ec880dc6ffe481a136b19241` | **черновик, не отправлен** |

Формат: только данные, без комментариев; ASCII, LF, без BOM и табов;
завершающая пустая строка. Письмо для редакторов —
[`submission/oeis-bfile-75000.eml`](submission/oeis-bfile-75000.eml),
пошаговая инструкция — [`40000/OEIS_SUBMISSION.md`](40000/OEIS_SUBMISSION.md).
Первые 102 терма совпадают с опубликованным префиксом A084945, первые 50 000 —
с файлом из `50000/`.

## Публикация и статус внешних ссылок

1. **GitHub** — исходный репозиторий
   <https://github.com/fix27/golomb-dickman-constant>, релиз `v75000`,
   release notes — [`RELEASE_v75000.md`](RELEASE_v75000.md).
2. **Zenodo** — **планируемая публикация / черновик записи**: заявленный
   version DOI [10.5281/zenodo.24567561](https://doi.org/10.5281/zenodo.24567561)
   с датой 2026-11-26. Метаданные — в [`.zenodo.json`](.zenodo.json), текст
   релиза — в [`RELEASE_v75000.md`](RELEASE_v75000.md). Актуальный статус
   записи следует проверять по самой ссылке; до активации DOI не следует
   цитировать как опубликованный.
3. **arXiv** — препринт [`paper/main-75000.tex`](paper/main-75000.tex)
   (75 000 знаков); [`paper/main.tex`](paper/main.tex) описывает предыдущий
   результат на 50 000 знаков. Раздел math.NA, cross-list cs.MS; поля формы —
   в [`paper/ARXIV_SUBMISSION.md`](paper/ARXIV_SUBMISSION.md). Рукопись в среде
   сборки не компилировалась (нет LaTeX).
4. **OEIS** — черновик b-file на 75 000 термов подготовлен, но **не отправлен**
   (см. раздел выше).
5. **MathWorld** — статус неоднозначный, категоричные утверждения неуместны.
   Все применимые утверждения страницы «Golomb-Dickman Constant Digits»
   проверены на 75 000 знаках: 8 пунктов **PASS**, две исторические атрибуции
   (Митчелл 1968; глубина расчёта Вебштейна 2013) — **NOT_VERIFIABLE**,
   нормальность — **OPEN**, заявленный исчерпывающий поиск простых до
   15 000 знаков — **PARTIAL** (выборочно проверены 140 длин). Кроме того,
   снимок страницы от 23.11.2026 указывает **40 000** знаков и не упоминает
   50 000 и 75 000. Отчёт —
   [`verification/reports/mathworld_50000.md`](verification/reports/mathworld_50000.md),
   скрипт — [`verification/mathworld_checks.py`](verification/mathworld_checks.py),
   фиксация упоминания —
   [`submission/MATHWORLD_MENTION.md`](submission/MATHWORLD_MENTION.md).

## Структура репозитория

| Путь | Назначение |
|---|---|
| [`75000/`](75000/) | **Текущий результат**: 75 000 знаков, сертификат, продюсер v27, 4 767 чекпоинтов, манифест SHA-256 |
| [`50000/`](50000/) | Предыдущий результат: 50 000 знаков, сертификат, b-file, 3 076 чекпоинтов |
| [`40000/`](40000/) | Предыдущий результат: 40 000 знаков, b-file, 1 209 чекпоинтов, проверки |
| [`audit/`](audit/) | Отчёты: `06-75000.md` (аудит сертификата), `07-75000-statistics.md` (статистика цифр) |
| [`verification/`](verification/) | Набор для внешнего проверяющего: уровни A, B, B′, C |
| [`paper/`](paper/) | Препринты (`main-75000.tex`, `main.tex`) и метаданные отправки |
| [`submission/`](submission/) | Письма OEIS/SeqFan/MathWorld, черновик b-file на 75 000 термов |
| [`30000/`](30000/), [`30000-v2/`](30000-v2/) | Первый сертифицированный результат: 30 000 знаков (две итерации пайплайна) |
| [`old_version/`](old_version/) | Архив ранних версий программы (v22–v25) |
| [`coq/`](coq/), [`lean/`](lean/) | Экспериментальная формализация отдельных лемм; вне базы доверия |
| [`golomb_dickman_27.py`](golomb_dickman_27.py) | Текущий самодостаточный CLI (v27), копия из `75000/` |
| [`CITATION.cff`](CITATION.cff), [`.zenodo.json`](.zenodo.json) | Машиночитаемая цитата и метаданные релиза |

## Документация

| Документ | Содержание |
|---|---|
| [`75000/README.md`](75000/README.md) | Текущий результат: параметры, проверки, оговорки |
| [`50000/README.md`](50000/README.md) | Результат на 50 000 знаков: проверки, шаг сетки, оговорки |
| [`40000/README.md`](40000/README.md) | Результат на 40 000 знаков: выводы, структура цифр, дефекты R1–R11 |
| [`40000/VERIFICATION.md`](40000/VERIFICATION.md) | Методика проверки, найденные дефекты, база доверия |
| [`audit/06-75000.md`](audit/06-75000.md) | Полный отчёт аудита 75 000 знаков |
| [`audit/07-75000-statistics.md`](audit/07-75000-statistics.md) | Статистический анализ цифр |
| [`RELEASE_v75000.md`](RELEASE_v75000.md) | Release notes v75000: параметры, железо, время, проверки |
| [`paper/README.md`](paper/README.md), [`paper/ARXIV_SUBMISSION.md`](paper/ARXIV_SUBMISSION.md) | Сборка препринта, ограничения, поля формы arXiv |
| [`submission/EMAILS.md`](submission/EMAILS.md) | Куда и в каком порядке отправлять |
| [`30000/README.md`](30000/README.md) | Детали первого результата на 30 000 знаков |

## Цитирование

```bibtex
@misc{pozdnyakov2026golombdickman,
  title        = {Golomb--Dickman constant: 75{,}000 certified decimal digits},
  author       = {Pozdnyakov, Konstantin},
  year         = {2026},
  doi          = {10.5281/zenodo.24567561},
  howpublished = {\url{https://github.com/fix27/golomb-dickman-constant/tree/main/75000}},
  note         = {Rigorous interval-arithmetic certificate using Arb;
                  full Arb re-audit of all 476{,}648 nodes not run}
}
```

## Лицензия

[MIT](LICENSE) © 2026 Поздняков Константин.

---

<details>
<summary><b>English summary</b></summary>

This repository contains rigorous interval-arithmetic certificates for decimal
digits of the Golomb–Dickman constant
$\lambda = \int_0^\infty e^{-u-E_1(u)}\,du = 0.6243299885\ldots$.
The current result is **75,000 certified decimal digits** (`75000/`, tag
`v75000`). Previous packages are kept unchanged: 50,000 digits in `50000/`,
40,000 digits in `40000/`, and 30,000 digits in `30000/` and `30000-v2/`.
The computation of the 75,000-digit certificate was done with
`golomb_dickman_27.py`; the earlier certificates were produced by
`50000/golomb_dickman_26.py` (50,000) and `40000/golomb_dickman.py` (40,000).
This is an extension of the result, not a record claim.

The certificate in `75000/golomb_dickman_75000_certified.txt` gives integer
bounds $[\Lambda_-,\Lambda_+]\ni\lambda$ with scale $S=249341$ and
$\lfloor 10^{75000}\Lambda_-/2^S\rfloor
=\lfloor 10^{75000}\Lambda_+/2^S\rfloor$,
so the digits are proven by truncation. The interval width is
$5.8205594787\times10^{-75043}$, leaving 42.2350 guard digits beyond the
75,000th place. The first 50,000 and 40,000 digits agree with the earlier
certificates.

The computation uses the trapezoidal rule after the Takahashi–Mori substitution,
explicit tail and discretization bounds (Trefethen–Weideman), Stieltjes continued
fractions, and Arb balls via `python-flint`. Trust base: Arb correctness, the
cited theorems, and exact Python integer arithmetic.

**What is proven:** correctness of the interval, its width
$5.8205594787\times10^{-75043}$, the truncation to the first 75,000 digits, and
the correctness of the 2,000 verified nodes.
**What is not proven (limitation):** the full independent re-audit of all
476,648 nodes in Arb was **not** run — Application Control blocks `python-flint`
on the build machine. Until that audit is completed, the certificate relies on
the original producer run. `python-flint` is required only for that full Arb
audit; level A (certificate, digits, manifest, OEIS prefix) needs only the
Python standard library.

`75000/SHA256SUMS.txt` lists the canonical hashes. Run

```bash
python verification/verify_certificate.py \
    --cert 75000/golomb_dickman_75000_certified.txt \
    --digits-file golomb_dickman_75000_digits.txt \
    --sha256-manifest 75000/SHA256SUMS.txt \
    --compare 50000/golomb_dickman_50000_digits.txt
```

for a dependency-free check of the certificate, digits and OEIS prefix.
Checkpoints: 4,767 blocks of 100 nodes for 75,000 digits (plan
`gd-checkpoint-v13`), 3,076 blocks for 50,000 digits (plan
`gd-checkpoint-v12`), 1,209 blocks in `meta.pkl` format (`chunk=200`) for
40,000 digits. Level C is an independent mpmath quadrature (tanh-sinh and
Gauss–Legendre) agreeing on 320 digits when 300 were requested; it is a
numerical check, not a proof. The experimental `coq/` and `lean/` directories
are not part of the trust base of the current certificate.

OEIS: the published b-file for A084945 contains only 102 digits
(`n = 0..101`). The 75,000-term draft `submission/b084945.txt` has **not** been
submitted; ready b-files with 50,000 and 40,000 terms are kept in `50000/` and
`40000/`. Zenodo: the version DOI `10.5281/zenodo.24567561` with date 2026-11-26
is a planned/draft record — check the link for the actual status before citing
it as published.

`verification/reports/mathworld_50000.md` checks every statement on
MathWorld's "Golomb-Dickman Constant Digits" page against the certified digits:
8 PASS, two historical attributions NOT_VERIFIABLE, normality OPEN, and the
reported prime search to 15,000 digits PARTIAL (140 sampled lengths). The page
snapshot of 2026-11-23 cites 40,000 digits and mentions neither 50,000 nor
75,000. Normality of $\lambda$ remains an open problem.

</details>