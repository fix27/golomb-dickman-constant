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

## Новый результат: 75 000 знаков (релиз v75000)

Сертификат
[`75000/golomb_dickman_75000_certified.txt`](75000/golomb_dickman_75000_certified.txt)
задаёт интервал $[\Lambda_-,\Lambda_+]\ni\lambda$ с масштабом $S=249341$,
в котором $\lfloor 10^{75000}\Lambda_-/2^S\rfloor
=\lfloor 10^{75000}\Lambda_+/2^S\rfloor$. Первые **75 000** знаков доказаны
усечением; ширина интервала — $5.8206\times10^{-75043}$ (42.235 запасных
знака). Полный Arb-аудит всех 476 648 узлов **не выполнялся** — проверены
2 000 узлов; это расширение результата, а не заявка на рекорд.

| Что | Файл |
|---|---|
| Сертификат, код, чекпоинты, контрольные суммы | [`75000/`](75000/) |
| Release notes | [`RELEASE_v75000.md`](RELEASE_v75000.md) |
| Препринт | [`paper/main-75000.tex`](paper/main-75000.tex) |
| Аудит | [`audit/06-75000.md`](audit/06-75000.md) |
| Фиксация упоминания MathWorld | [`submission/MATHWORLD_MENTION.md`](submission/MATHWORLD_MENTION.md) |

Быстрая проверка:

```bash
python verification/verify_certificate.py \
    --cert 75000/golomb_dickman_75000_certified.txt \
    --digits-file golomb_dickman_75000_digits.txt \
    --sha256-manifest 75000/SHA256SUMS.txt \
    --compare 50000/golomb_dickman_50000_digits.txt
```

## Предыдущий результат: 50 000 знаков

Сертификат
[`50000/golomb_dickman_50000_certified.txt`](50000/golomb_dickman_50000_certified.txt)
задаёт интервал $[\Lambda_-,\Lambda_+]\ni\lambda$ с масштабом $S=166293$ и

$$\left\lfloor 10^{50000}\Lambda_-/2^S\right\rfloor
=\left\lfloor 10^{50000}\Lambda_+/2^S\right\rfloor,$$

поэтому первые **50 000** знаков доказаны усечением. Ширина интервала —
$4.390\times10^{-50043}$, то есть в запасе остаётся ещё 42 знака.

| Артефакт | Файл |
|---|---|
| Сертификат: границы интервала и 50 000 знаков | [`50000/golomb_dickman_50000_certified.txt`](50000/golomb_dickman_50000_certified.txt) |
| Только цифры, одной строкой | [`50000/golomb_dickman_50000_digits.txt`](50000/golomb_dickman_50000_digits.txt) |
| b-file для OEIS A084945, термы `n = 0..49999` | [`50000/b084945.txt`](50000/b084945.txt) |
| Чекпоинты: 3076 блоков по 100 узлов | [`50000/gd_rigorous_ckpt_50000/`](50000/gd_rigorous_ckpt_50000/) |

```text
76f4155981049003351409769505c3cec39e26dfc30624c46bd199e70ed6477a  golomb_dickman_50000_certified.txt
8f017d45ee5108bb6b976882b079279f44f8a767ce62b44bd7c54e9167ad09a0  golomb_dickman_50000_digits.txt
1e3d23e9ac3ce51990d83decd395d6bde96027f43811b94cebd5a6a4b7c19c43  b084945.txt
```

Первые 40 000 знаков нового сертификата совпадают с сертификатом на
40 000 знаков (проверяется `verification/verify_certificate.py --compare`),
а суммы 3076 блоков воспроизводят оба конца интервала с поправками
$B=1$ и $C=2427712667995762$. Шаг $h=80846368/2^{40}$ берётся из плана
`50000/gd_rigorous_ckpt_50000/meta_v12.json`, поэтому $B=1$ — независимая
проверка, а не следствие подгонки. Подробности и оговорки —
[`50000/README.md`](50000/README.md) и
[`verification/reports/50000_verification.txt`](verification/reports/50000_verification.txt).

## Проверка утверждений MathWorld

Отдельный отчёт проверяет **все** утверждения страницы
[«Golomb-Dickman Constant Digits»](https://mathworld.wolfram.com/Golomb-DickmanConstantDigits.html)
на 50 000 знаках: начало разложения, последовательность Эрлса, A229195,
сканирование строк, отсутствие `0123456789`/`9876543210`, таблицу частот,
A174975/A174974 и заявленный поиск простых до 15 000 знаков.

| Что | Файл |
|---|---|
| Отчёт с разбором каждого пункта | [`verification/reports/mathworld_50000.md`](verification/reports/mathworld_50000.md) |
| Воспроизводимый скрипт | [`verification/mathworld_checks.py`](verification/mathworld_checks.py) |
| Машинный отчёт JSON | [`verification/reports/mathworld_50000.json`](verification/reports/mathworld_50000.json) |
| Справочные b-файлы OEIS | [`verification/reports/oeis/`](verification/reports/oeis/) |

Итог: 8 пунктов **PASS**, 2 исторические атрибуции **NOT_VERIFIABLE**
(Митчелл 1968 и глубина расчёта Вебштейна 2013), нормальность — **OPEN**,
заявленный исчерпывающий поиск простых до 15 000 знаков — **PARTIAL**
(выборочно проверены 140 длин). Дополнительно найдены самые длинные серии,
палиндром, повторы, тандемы, периодические участки, покрытие $k$-грамм и
проведены $\chi^2$-тесты. Это проверка цифровой строки и утверждений
страницы, а не доказательство нормальности и не заявка на рекорд.

```bash
# ~7 секунд: утверждения страницы и цифровые проверки.
python verification/mathworld_checks.py

# Полный отчёт: плюс исчерпывающий перебор длин 1..2508,
# сильная проверка 1659/2508 и выборочный скан до 15 000
# (около 12 минут, 698 с).
python verification/mathworld_checks.py --primes --deep-primes \
    --json verification/reports/mathworld_50000.json
```

## Предыдущий результат: 40 000 знаков

Сертификат
[`40000/golomb_dickman_40000_certified.txt`](40000/golomb_dickman_40000_certified.txt)
содержит целочисленный интервал $[\Lambda_-,\Lambda_+]\ni\lambda$ такой, что

$$\left\lfloor 10^{40000}\Lambda_-\right\rfloor
=\left\lfloor 10^{40000}\Lambda_+\right\rfloor .$$

Поэтому первые **40 000** десятичных знаков (усечение, без округления)
доказаны, а не просто вычислены с плавающей точкой. Ширина интервала —
около $10^{-40042.26}$, то есть в запасе остаётся ещё примерно 42 знака.

| Артефакт | Файл |
|---|---|
| Сертификат: границы интервала и 40 000 знаков | [`40000/golomb_dickman_40000_certified.txt`](40000/golomb_dickman_40000_certified.txt) |
| Только цифры, одной строкой | [`40000/golomb_dickman_40000_digits.txt`](40000/golomb_dickman_40000_digits.txt) |
| b-file для OEIS A084945, термы `n = 0..39999` | [`40000/b084945.txt`](40000/b084945.txt) |
| Автономная проверка без сторонних пакетов | [`40000/verify_40000.py`](40000/verify_40000.py) |

Контрольные суммы:

```text
8892c0715f1afbb271c9f07cc9658cea0f3ca83c2dda3ec7d23b447dc908de9c  golomb_dickman_40000_certified.txt
fbae757900983bd4fb6421c5f27bf9602af1a1bfc013e4c501bb9da2b5a65327  golomb_dickman_40000_digits.txt
c73af643198da299d2e624e3c2f69d05439efcddbbefa7cec176ac63f993bed3  b084945.txt
```

Полный список — в [`40000/SHA256SUMS.txt`](40000/SHA256SUMS.txt).

## Быстрая проверка

Нужен только Python 3.11+; сторонние пакеты не требуются.

```bash
git clone https://github.com/fix27/golomb-dickman-constant.git
cd golomb-dickman-constant
python verification/verify_certificate.py \
    --cert 50000/golomb_dickman_50000_certified.txt \
    --compare 40000/golomb_dickman_40000_digits.txt
```

Ожидаемый вывод:

```text
OK: 50000 digits certified
  scale: lam_lo/2^166293 .. lam_hi/2^166293
  width: 4.390 x 10^-50043  (42 guard digits)
  b-file: 50000 terms
  OEIS prefix: checked
  compared with 40000\golomb_dickman_40000_digits.txt: 40000 leading digits agree
  SHA-256: OK
```

Для 40 000 знаков — `--cert 40000/golomb_dickman_40000_certified.txt`
(без `--compare`).

Скрипт проверяет, что сертифицированный интервал не пересекает границу
десятичной ячейки, что цифры равны $\lfloor 10^{D}\lambda\rfloor$, что
файл цифр и b-file согласованы с сертификатом и что первые 102 цифры
совпадают с OEIS A084945. Более глубокий аудит чекпоинтов для 40 000
знаков описан в [`40000/VERIFICATION.md`](40000/VERIFICATION.md), а для
50 000 знаков суммы 3076 блоков проверяет `verification/audit_chunks.py`.

## Три уровня проверки

Каталог [`verification/`](verification/) — отдельный набор для внешнего
проверяющего. Уровни A и B не импортируют вычислитель и не используют
плавающую точку в решающих проверках; аудит B′ читает только чекпоинты
(pickle) и тоже не импортирует вычислитель; уровень C — численная
перепроверка в `mpmath`, а не доказательство.

| Уровень | Команда | Что даёт | Чего не даёт |
|---|---|---|---|
| A | `python verification/verify_certificate.py --cert 50000/...` | SHA-256, ширина интервала, цифры, b-file, префикс OEIS; секунды | не доказывает, что $\lambda$ лежит в интервале |
| B | `python verification/level_b.py` | параметры, $B_{\rm disc}$, хвосты, формулы и 12 чанков, пересчитанных заново | не пересчитывает enclosure в Arb |
| B′ | `python verification/audit_chunks.py --ckpt 50000/...` | непрерывность 3076 блоков и воспроизведение концов интервала из сумм | не заменяет пересчёт узлов в Arb |
| C | `python verification/independent_quadrature.py --digits 1000` | независимое воспроизведение цифр: другая библиотека и другая квадратура | не строго: mpmath работает в плавающей точке |

Уровень B на машине сборки сообщает, что аудит в Arb не запускался
(`python-flint` не загружается из-за Application Control), и это указано в
отчёте, а не замалчивается.

Готовый архив для отправки по 40 000 знакам —
`golomb_dickman_40000_verification.zip`. Пакет для 50 000 знаков — это
каталог [`50000/`](50000/) (сертификат, цифры, b-file, чекпоинты) плюс
отчёт [`verification/reports/50000_verification.txt`](verification/reports/50000_verification.txt).

## Структура репозитория

| Путь | Назначение |
|---|---|
| [`50000/`](50000/) | **Текущий результат**: 50 000 знаков, сертификат, b-file, чекпоинты, проверки |
| [`40000/`](40000/) | Предыдущий результат: 40 000 знаков, b-file, проверки, документация |
| [`verification/`](verification/) | Трёхуровневая проверка для внешнего читателя: сертификат, аудит, независимый расчёт |
| [`paper/`](paper/) | Препринт для arXiv (`main.tex`) и метаданные отправки |
| [`submission/`](submission/) | Готовые письма: OEIS, SeqFan, MathWorld; единственный b-file на 75 000 термов |
| [`CITATION.cff`](CITATION.cff) | Машиночитаемая цитата (CFF 1.2.0) |
| [`.zenodo.json`](.zenodo.json) | Метаданные релиза Zenodo (DOI) |
| [`30000/`](30000/) | Первый сертифицированный результат: 30 000 знаков |
| [`30000-v2/`](30000-v2/) | Вторая итерация пайплайна для 30 000 знаков (v23); сертификаты на 2 000 и 30 000 |
| [`old_version/`](old_version/) | Архив ранних версий программы (v22–v25) и `archive/` |
| [`coq/`](coq/), [`lean/`](lean/) | Экспериментальная формализация отдельных лемм (Coq/mathcomp, Lean/Mathlib) |
| [`golomb_dickman_27.py`](golomb_dickman_27.py) | Текущий самодостаточный CLI (v27) |

В корне лежат сертификат и цифры результата на 75 000 знаков:
`golomb_dickman_75000_certified.txt`, `golomb_dickman_75000_digits.txt`.
Сертификат байт в байт совпадает с `75000/golomb_dickman_75000_certified.txt`.
Единственный b-file результата — [`submission/b084945.txt`](submission/b084945.txt),
75 000 термов. Канонические файлы предыдущих результатов остаются в `50000/`
и `40000/`; именно для них приведены SHA-256. При `core.autocrlf=true` рабочая
копия на Windows может получить CRLF, поэтому для OEIS и проверок берите
LF-файлы из репозитория.

## Как воспроизвести

### Требования

- Python 3.11+;
- [`python-flint`](https://github.com/flintlib/python-flint) (Arb) — обязателен;
- [`mpmath`](https://mpmath.org/) — только для `crosscheck`;
- желательно многоядерный CPU: расчёт распараллеливается по процессам.

```bash
python -m pip install python-flint mpmath
```

### CLI для результата 50 000 знаков (v26)

```bash
python 50000/golomb_dickman_26.py test
python 50000/golomb_dickman_26.py smoke
python 50000/golomb_dickman_26.py certify --digits 50000
python 50000/golomb_dickman_26.py crosscheck --digits 200
python 50000/golomb_dickman_26.py boundary-test
```

Результат на 75 000 знаков получен CLI v27 (`golomb_dickman_27.py`); команды
воспроизведения и план `gd-checkpoint-v13` — в [`75000/README.md`](75000/README.md).

- `test` — самопроверка окружения и точные рациональные проверки леммы 7;
- `smoke` — сквозной прогон на 60 знаках;
- `certify --digits 50000` — полный сертификат; значение по умолчанию для
  `--digits` по-прежнему 40 000. Пишет `golomb_dickman_<D>_certified.txt`
  в текущий каталог и сохраняет чекпоинты в `gd_rigorous_ckpt_<D>/`;
- `crosscheck` — независимые сверки через `mpmath`/`mpmath.iv`, цепные дроби,
  форсированные ветви, альтернативный шаг и лестницу точности;
- `boundary-test` — граничные тесты леммы 7.

> **Не запускайте `certify` внутри `40000/` или `50000/` — потеряются
> опубликованные чекпоинты.** Каталог по умолчанию —
> `gd_rigorous_ckpt_<D>/` в текущем каталоге, то есть тот же, где лежат
> опубликованные куски: 1 209 в `40000/` (формат `meta.pkl`, `chunk=200`)
> и 3 076 в `50000/` (формат `meta_v12.json`, `chunk=100`). v26 пишет свой
> `meta_v12.json` и чужой план не проверяет, поэтому часть файлов `c_*.pkl`
> будет перезаписана кусками другого размера. Исходный набор
> восстанавливается только полным пересчётом. Для нового счёта используйте
> пустой каталог или явный `--ckpt`, а опубликованные каталоги считайте
> read-only артефактами.

Полный прогон занимает **часы CPU** (50 000 знаков — заметно дольше
40 000); его можно прерывать,
прогресс сохраняется в чекпоинтах. Режим `--resume` — только аудиторский:
он доверяет готовым чекпоинтам, не пересчитывает их и **не выдаёт
сертификат**. По умолчанию работает безопасный режим `--no-resume`:
каждый кусок пересчитывается в Arb.

Текущий CLI использует формат чекпоинтов v12 (`meta_v12.json`). Так получен
результат на 50 000 знаков; его чекпоинты лежат в
`50000/gd_rigorous_ckpt_50000/`. Чекпоинты `40000/gd_rigorous_ckpt_40000/`
имеют старый формат `meta.pkl` и относятся к
[`40000/golomb_dickman.py`](40000/golomb_dickman.py) — пайплайну, которым
получен сертификат на 40 000 знаков. Его можно запустить так:

```bash
cd 40000
python golomb_dickman.py
```

`main()` сначала выполняет пробный прогон на 60 знаках, затем основной расчёт
на 40 000 знаков, используя существующие чекпоинты.

> **Повторный прогон `golomb_dickman.py` перезаписывает файлы комплекта.**
> `main()` пишет `smoke_60.txt` и сертификат в текущий каталог. На Windows
> вычислитель открывает их без `newline="\n"`, поэтому перезапись даёт CRLF,
> и `SHA256SUMS.txt` (посчитан по LF) перестаёт сходиться: `sha256sum -c` и
> `verify_40000.py` начинают падать на контрольных суммах. Если нужен именно
> повторный расчёт, делайте его в копии каталога и пересчитывайте манифест
> заново.

### База доверия

Доказательство условно только по отношению к явно перечисленной базе доверия:

1. корректность интервальной арифметики [Arb](https://arblib.org/)
   (`python-flint`);
2. теорема о трапециях для аналитических функций в полосе
   (Trefethen & Weideman, *SIAM Review* 56 (2014), Thm 5.1);
3. классическая теорема Стилтьеса о двусторонних оценках подходящими дробями;
4. леммы из docstring вычислителя (§1–§7);
5. точная целочисленная арифметика Python.

Это не проверка в proof assistant. Каталоги `coq/` и `lean/` содержат лишь
экспериментальную формализацию отдельных лемм и не заменяют сертификат.

## B-file для OEIS

Текущий файл — [`50000/b084945.txt`](50000/b084945.txt):

- 50 000 термов, `n = 0..49999`;
- только данные, без комментариев;
- ASCII, LF, без BOM и табов;
- завершающая пустая строка;
- 50 001 строка, 388 891 байт;
- SHA-256: `1e3d23e9ac3ce51990d83decd395d6bde96027f43811b94cebd5a6a4b7c19c43`.

Предыдущий файл — [`40000/b084945.txt`](40000/b084945.txt): 40 000 термов,
`n = 0..39999`, 40 001 строка, 308 891 байт, SHA-256
`c73af643198da299d2e624e3c2f69d05439efcddbbefa7cec176ac63f993bed3`.

Подготовлен также черновик расширения до 75 000 термов —
[`submission/b084945.txt`](submission/b084945.txt) (75 000 термов,
`n = 0..74999`, 588 891 байт, SHA-256
`05584c9d3f0afccbfb9a1d8c8f28177a33a30be3ec880dc6ffe481a136b19241`), письмо —
[`submission/oeis-bfile-75000.eml`](submission/oeis-bfile-75000.eml). Он **не
отправлен**; в OEIS по-прежнему b-file `n = 0..101`. Первые 102 терма совпадают
с ним, первые 50 000 — с файлом из `50000/`.

На момент подготовки первого файла b-file в OEIS A084945 содержал только
`n = 0..101` (он синтезирован из записи), поэтому новый файл его заменяет.
Текст ссылки для текущего файла:

```text
Konstantin Pozdnyakov, <a href="b084945.txt">Table of n, a(n) for n=0..49999</a>
```

Пошаговая инструкция и письмо для редакторов — в
[`40000/OEIS_SUBMISSION.md`](40000/OEIS_SUBMISSION.md). Публикация в
Zenodo/arXiv и анонс в SeqFan — в
[`40000/PUBLICATION_CHECKLIST.md`](40000/PUBLICATION_CHECKLIST.md).

## Документация

| Документ | Содержание |
|---|---|
| [`50000/README.md`](50000/README.md) | Подробное описание текущего результата на 50 000 знаков |
| [`50000/SHA256SUMS.txt`](50000/SHA256SUMS.txt) | Контрольные суммы текущего пакета |
| [`RELEASE_v50000.md`](RELEASE_v50000.md) | Release notes v50000: параметры, железо, время, проверки, DOI |
| [`40000/README.md`](40000/README.md) | Подробное описание результата на 40 000 знаков |
| [`40000/VERIFICATION.md`](40000/VERIFICATION.md) | Что и как проверяется, найденные дефекты, база доверия |
| [`40000/OEIS_SUBMISSION.md`](40000/OEIS_SUBMISSION.md) | Отправка b-file в OEIS |
| [`40000/PUBLICATION_CHECKLIST.md`](40000/PUBLICATION_CHECKLIST.md) | Zenodo, arXiv, SeqFan |
| [`paper/README.md`](paper/README.md) | Препринт: сборка, содержание, ограничения |
| [`paper/ARXIV_SUBMISSION.md`](paper/ARXIV_SUBMISSION.md) | Заголовок, abstract, категории и MSC для arXiv |
| [`submission/EMAILS.md`](submission/EMAILS.md) | Куда отправлять и в каком порядке |
| [`30000/README.md`](30000/README.md) | Детали результата на 30 000 знаков |

## Публикация

Результат подготовлен к публикации в четырёх местах:

1. **GitHub** — исходный репозиторий
   <https://github.com/fix27/golomb-dickman-constant>, релиз `v75000`;
2. **Zenodo** — запись <https://zenodo.org/records/24567561>, version DOI
   [10.5281/zenodo.24567561](https://doi.org/10.5281/zenodo.24567561)
   (опубликован 2026-11-26); метаданные — в [`.zenodo.json`](.zenodo.json),
   текст релиза — в [`RELEASE_v75000.md`](RELEASE_v75000.md);
3. **arXiv** — препринт [`paper/main-75000.tex`](paper/main-75000.tex)
   (75 000 знаков); [`paper/main.tex`](paper/main.tex) описывает предыдущий
   результат на 50 000 знаков. Раздел math.NA, cross-list cs.MS; поля формы —
   в [`paper/ARXIV_SUBMISSION.md`](paper/ARXIV_SUBMISSION.md);
4. **OEIS** — черновик b-file для A084945 на 75 000 термов
   (`n = 0..74999`) подготовлен, но **не отправлен**; в OEIS пока b-file
   `n = 0..101`. Файл —
   [`submission/b084945.txt`](submission/b084945.txt), письмо —
   [`submission/oeis-bfile-75000.eml`](submission/oeis-bfile-75000.eml).
   Ранее готовились файлы на 40 000 и 50 000 термов.

Упоминание на MathWorld уже опубликовано (журнал обновлений: 2026-11-14;
процитированный коммит: 2026-11-15 +04:00), новая отправка не требуется. Факт зафиксирован в
[`submission/MATHWORLD_MENTION.md`](submission/MATHWORLD_MENTION.md) с точными
URL, формулировками, HTML, заголовками HTTP, скриншотами и PDF; черновик письма
[`submission/mathworld-thanks.eml`](submission/mathworld-thanks.eml) **не
отправлен**.


## Цитирование

```bibtex
@misc{pozdnyakov2026golombdickman,
  title        = {Golomb--Dickman constant: 75{,}000 certified decimal digits},
  author       = {Pozdnyakov, Konstantin},
  year         = {2026},
  doi          = {10.5281/zenodo.24567561},
  howpublished = {\url{https://github.com/fix27/golomb-dickman-constant/tree/main/75000}},
  note         = {Rigorous interval-arithmetic certificate using Arb;
                  full Arb re-audit not run}
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
`v75000`); the previous 50,000- and 40,000-digit packages are kept in `50000/`
and `40000/`, and a 30,000-digit result in `30000/` and `30000-v2/`.
The full Arb re-audit of all 476,648 nodes was not run; this is an extension,
not a record claim.

The certificate in `75000/golomb_dickman_75000_certified.txt` gives integer
bounds $[\Lambda_-,\Lambda_+]\ni\lambda$ with scale $S=249341$ and
$\lfloor 10^{75000}\Lambda_-/2^S\rfloor
=\lfloor 10^{75000}\Lambda_+/2^S\rfloor$,
so the digits are proven by truncation. The interval width is
$5.8206\times10^{-75043}$, leaving 42.235 guard digits. Its first 50,000 and
40,000 digits agree with the earlier certificates.

The computation uses the trapezoidal rule after the Takahashi–Mori substitution,
explicit tail and discretization bounds (Trefethen–Weideman), Stieltjes continued
fractions, and Arb balls via `python-flint`. Trust base: Arb correctness and the
cited theorems. The current self-contained CLI is `golomb_dickman_27.py`;
`golomb_dickman_26.py` produced the 50,000-digit certificate.

`75000/SHA256SUMS.txt` lists the canonical hashes. Run
`python verification/verify_certificate.py --cert 75000/golomb_dickman_75000_certified.txt
--digits-file golomb_dickman_75000_digits.txt --sha256-manifest 75000/SHA256SUMS.txt`
for a dependency-free check of the certificate, digits and OEIS prefix, and
`python verification/audit_chunks.py --ckpt 75000/gd_rigorous_ckpt_75000
--cert 75000/golomb_dickman_75000_certified.txt` to audit the 4,767 checkpoint
chunks. The full Arb re-audit of all 476,648 nodes was **not** run (2,000 nodes
were checked); level C is an independent mpmath quadrature agreeing on 320
digits. The OEIS b-file for A084945 in `50000/b084945.txt` has 50,000 terms;
a 75,000-term draft is in `submission/b084945.txt` (not submitted).

`verification/reports/mathworld_50000.md` checks every statement on
MathWorld's "Golomb-Dickman Constant Digits" page against the 50,000
digits: 8 PASS, two historical attributions NOT_VERIFIABLE, normality
OPEN, and the reported prime search to 15,000 digits PARTIAL (140 sampled
lengths). The script is `verification/mathworld_checks.py`.

</details>
