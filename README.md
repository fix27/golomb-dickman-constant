# Постоянная Голомба–Дикмана: сертифицированные знаки

Постоянная Голомба–Дикмана $\lambda$ возникает в теории случайных
перестановок и в теории чисел. Если $a_n$ — средняя длина наибольшего цикла
перестановки множества из $n$ элементов, то $\lambda=\lim_{n\to\infty}a_n/n$;
одновременно это асимптотическая доля числа знаков наибольшего простого
делителя целого. Значение:

$$\lambda=0.624329988543550870992936383100837244\ldots$$

([OEIS A084945](https://oeis.org/A084945)). Неизвестно, рационально ли это число.

Автор расчётов, кода и сертификатов: **Поздняков Константин Николаевич**
(Konstantin N. Pozdnyakov), Сургут, ХМАО — Югра, Россия,
[fix@inbox.ru](mailto:fix@inbox.ru).

## Интегральные представления

$$
\lambda=\int_0^1 e^{\operatorname{li}(t)}\,dt
=\int_0^\infty e^{-t-E_1(t)}\,dt
=\int_0^\infty\frac{\rho(t)}{t+2}\,dt
=\int_0^\infty\frac{\rho(t)}{(t+1)^2}\,dt .
$$

Здесь $\operatorname{li}$ — интегральный логарифм,
$E_1(t)=\int_t^\infty e^{-s}/s\,ds$ — экспоненциальный интеграл, $\rho$ —
функция Дикмана. Расчёт использует второе представление после подстановки
Такахаси–Мори; подробности метода — в [`75000/README.md`](75000/README.md).

## Текущий результат: 75 000 знаков

Релиз [`v75000`](RELEASE_v75000.md) (Zenodo DOI
[10.5281/zenodo.24567561](https://doi.org/10.5281/zenodo.24567561)).
Первые **75 000** десятичных знаков доказаны усечением, а не вычислены
приближённо.

| Артефакт | Файл |
|---|---|
| Сертификат | [`75000/golomb_dickman_75000_certified.txt`](75000/golomb_dickman_75000_certified.txt) |
| Цифры, одной строкой | [`golomb_dickman_75000_digits.txt`](golomb_dickman_75000_digits.txt) |
| b-file для OEIS (75 000 термов, **не отправлен**) | [`submission/b084945.txt`](submission/b084945.txt) |
| Программа и чекпоинты | [`75000/`](75000/), [`golomb_dickman_27.py`](golomb_dickman_27.py) |

## Интервальная сертификация

Сертификат содержит целые $\Lambda_-<\Lambda_+$ и масштаб $S$, для которых

$$\left\lfloor\frac{10^{75000}\Lambda_-}{2^S}\right\rfloor
=\left\lfloor\frac{10^{75000}\Lambda_+}{2^S}\right\rfloor
=\lfloor 10^{75000}\lambda\rfloor .$$

Значит, весь интервал $[\Lambda_-/2^S,\Lambda_+/2^S]$ попадает в одну
десятичную ячейку, и цифры следуют точно.

| Параметр сертификата | Значение |
|---|---|
| $D$ (сертифицированных знаков) | 75 000 |
| $S$ | 249 341 |
| $h$ (шаг сетки) | $54\,039\,302/2^{40}$ |
| $B$ | 1 |
| $C=T_R+T_L+B$ | 34 133 488 394 318 882 |
| Ширина интервала | $5.8205594787\times10^{-75043}$ |

Полная таблица ($G$, $K_L,K_R$, показатели радиусов, $T_R,T_L$), хеши и
оговорки — в [`75000/README.md`](75000/README.md); протокол запуска — в
[`audit/06-75000.md`](audit/06-75000.md).

## Быстрая проверка

Потребуется **Python 3.11+**; для этой команды сторонние пакеты не нужны.

```bash
git clone https://github.com/fix27/golomb-dickman-constant.git
cd golomb-dickman-constant
python verification/verify_certificate.py \
    --cert 75000/golomb_dickman_75000_certified.txt \
    --digits-file golomb_dickman_75000_digits.txt \
    --sha256-manifest 75000/SHA256SUMS.txt \
    --bfile submission/b084945.txt \
    --sha256 b084945.txt=05584c9d3f0afccbfb9a1d8c8f28177a33a30be3ec880dc6ffe481a136b19241
```

Ожидается `OK: 75000 digits certified (interval arithmetic)`, `b-file: 75000
terms`, `OEIS prefix: checked`, три `MATCH` и код возврата 0. Скрипт проверяет
целочисленный интервал, цифры, согласованность b-файла и 102-значный префикс
OEIS. Команда аудита структуры 4 767 чанков, полный CLI и режимы расчёта даны
один раз в [`75000/README.md`](75000/README.md) — здесь они не повторяются.
Полный пересчёт узлов в Arb требует
[`python-flint`](https://github.com/flintlib/python-flint) и часов работы;
[`mpmath`](https://mpmath.org/) нужен только для численной перепроверки.

## Статус независимой проверки

- Целочисленная проверка сертификата, цифр и b-файла — **PASS**.
- Аудит структуры и сумм 4 767 чанков — **PASS**.
- Независимая квадратура `mpmath` (tanh-sinh и Gauss–Legendre) — 320
  совпадающих знаков при запросе 300; это численная, не доказательная проверка.
- **Полный Arb-аудит всех 476 648 узлов — NOT_RUN**: пересчитаны только первые
  20 чанков (2 000 узлов), все contained. Итоговый статус — **INCOMPLETE**, а
  не `PASS`.

Это расширение ранее опубликованного результата, а не заявка на рекорд и не
приоритетная заявка. Нормальность $\lambda$ остаётся открытой проблемой.

## Предыдущие результаты

- [`50000/`](50000/README.md) — 50 000 знаков, $S=166293$; сертификат и
  чекпоинты сохранены, отдельный файл цифр и b-file удалены.
- [`40000/`](40000/README.md) и [`40000-v2/`](40000-v2/README.md) — 40 000
  знаков; в `40000-v2/` есть полный Arb-replay, не запущенный на всём
  сертификате.
- [`old_version/30000/`](old_version/30000/README.md) — первая версия на
  30 000 знаков.

## Статья, формализации и публикация

- Препринт: [`paper/main-75000.tex`](paper/main-75000.tex),
  [`paper/README.md`](paper/README.md), поля подачи —
  [`paper/ARXIV_SUBMISSION.md`](paper/ARXIV_SUBMISSION.md).
- Формализации отдельных лемм: [`coq/`](coq/README.md) и [`lean/`](lean/);
  они экспериментальны и не заменяют сертификат.
- Материалы релиза: [`RELEASE_v75000.md`](RELEASE_v75000.md),
  [`.zenodo.json`](.zenodo.json), [`CITATION.cff`](CITATION.cff).
- Письма и статус отправок: [`submission/EMAILS.md`](submission/EMAILS.md),
  фиксация упоминания MathWorld —
  [`submission/MATHWORLD_MENTION.md`](submission/MATHWORLD_MENTION.md). Отправки
  в OEIS, SeqFan и MathWorld **не выполнялись** без подтверждения.
- Описание уровней проверки и их ограничений —
  [`verification/README.md`](verification/README.md).

## База доверия и ограничения

Доказательство условно относительно: корректности интервальной арифметики
[Arb](https://arblib.org/) (`python-flint`), теоремы о трапециях для
аналитических функций в полосе (Trefethen & Weideman, *SIAM Review* 56 (2014),
Thm 5.1), классической теоремы Стилтьеса о подходящих дробях, лемм из
docstring вычислителя (§1–§7) и точной целочисленной арифметики Python.
Это не проверка в proof assistant. Хеши связывают имя файла с байтами, но
сами по себе ничего не доказывают. При `core.autocrlf=true` рабочая копия на
Windows может получить CRLF — для OEIS и проверок берите LF-файлы из
репозитория.

Лицензия: [MIT](LICENSE) © 2026 Поздняков Константин.

<details>
<summary><b>English summary</b></summary>

This repository contains an interval-arithmetic certificate for the first
**75,000 decimal digits** of the Golomb–Dickman constant (release `v75000`,
DOI 10.5281/zenodo.24567561). The certificate proves that the whole interval
lies in one decimal cell; its width is $5.8206\times10^{-75043}$ (42.235 guard
digits, $S=249341$). Certificate checks and the 4,767-chunk audit pass, but the
full Arb re-audit of all 476,648 nodes was **not run** (2,000 nodes checked),
so the overall status is `INCOMPLETE`, not `PASS`. Earlier 50,000- and
40,000-digit results are preserved in `50000/` and `40000/`. This is an
extension of a published computation, not a world-record or priority claim.

</details>
