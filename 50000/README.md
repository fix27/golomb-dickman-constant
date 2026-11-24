# Постоянная Голомба–Дикмана: 50 000 сертифицированных знаков

$$\lambda=\int_0^\infty e^{-u-E_1(u)}\,du
=0.624329988543550870992936383100837244\ldots$$

Сертификат [`golomb_dickman_50000_certified.txt`](golomb_dickman_50000_certified.txt)
содержит целые $\Lambda_-<\Lambda_+$ и масштаб $S=166293$ такие, что

$$\left\lfloor 10^{50000}\Lambda_-/2^S\right\rfloor
=\left\lfloor 10^{50000}\Lambda_+/2^S\right\rfloor .$$

Значит, первые **50 000** десятичных знаков (усечение, не округление)
доказаны интервальной арифметикой, а не получены плавающей точкой.
Ширина интервала — $4.390\times10^{-50043}$, то есть сверх 50 000 знаков
остаётся больше 42 гарантированных знаков.

## Файлы

| Файл | Что это |
|---|---|
| `golomb_dickman_50000_certified.txt` | сертификат: $S$, $\Lambda_-$, $\Lambda_+$, 50 000 знаков |
| `golomb_dickman_50000_digits.txt` | только цифры, одной строкой |
| `b084945.txt` | b-file для OEIS A084945, термы `n = 0..49999` |
| `gd_rigorous_ckpt_50000/` | 3076 блоков по 100 узлов (кэш вычисления) |
| `golomb_dickman_26.py` | версия CLI, которой выполнялся расчёт |
| `SHA256SUMS.txt` | контрольные суммы файлов этого каталога |

## Проверки от 16.11.2026

Полный отчёт — [`../verification/reports/50000_verification.txt`](../verification/reports/50000_verification.txt).

| Проверка | Инструмент | Результат |
|---|---|---|
| целочисленная арифметика сертификата, десятичная ячейка, ширина | `verification/verify_certificate.py` | PASS |
| файл цифр совпадает с сертификатом | там же | PASS |
| b-file: 50 000 термов, `n = 0..49999`, каждая цифра | там же | PASS |
| первые 102 знака = OEIS A084945 | там же | PASS |
| первые 40 000 знаков = сертификат 40 000 | там же (`--compare`) | PASS, 40 000 из 40 000 |
| 3076 блоков: непрерывность, 307 580 узлов, без пропусков | `verification/audit_chunks.py` | PASS |
| суммы блоков воспроизводят $\Lambda_-,\Lambda_+$ | там же | $B=1$, $C=2427712667995762$ |
| ширина по блокам против ширины сертификата | там же | $4.230$ против $4.390\times10^{-50043}$ |

Дополнительно проверены все утверждения страницы MathWorld
«Golomb-Dickman Constant Digits»: отчёт
[`../verification/reports/mathworld_50000.md`](../verification/reports/mathworld_50000.md),
скрипт [`../verification/mathworld_checks.py`](../verification/mathworld_checks.py).
Итог: 8 PASS, 2 исторические атрибуции NOT_VERIFIABLE, нормальность OPEN,
заявленный поиск простых до 15 000 знаков PARTIAL (140 выборочных длин).

Шаг сетки зафиксирован в плане `gd_rigorous_ckpt_50000/meta_v12.json`:
$h=7.352934335358441\times10^{-5}$, что даёт ровно
$m=80846368$, то есть $h=m/2^{40}$. Аудит берёт $m$ из плана, а не из
$\Lambda_-$, поэтому $B=1$ — настоящая проверка согласованности, а не
следствие подгонки. План также задаёт $K_L=149075$, $K_R=158504$, что
точно соответствует покрытому диапазону узлов
$-149075\ldots158504$ (307 580 узлов; полуоткрытый интервал
$-149075\ldots158505$).
Контрольный прогон того же аудита на 40 000 знаках, где план хранится в
старом `meta.pkl`, восстанавливает $m=100859575$ и $C=65673984721697$ —
ровно значения из плана, что подтверждает методику и для старого формата.

## Контрольные суммы (каноническая форма, LF)

```text
76f4155981049003351409769505c3cec39e26dfc30624c46bd199e70ed6477a  golomb_dickman_50000_certified.txt
8f017d45ee5108bb6b976882b079279f44f8a767ce62b44bd7c54e9167ad09a0  golomb_dickman_50000_digits.txt
1e3d23e9ac3ce51990d83decd395d6bde96027f43811b94cebd5a6a4b7c19c43  b084945.txt
78783a09bae599298a07415056b0ca521717c9f7ecaa1fd15cb19b4d5ab6b0e0  gd_rigorous_ckpt_50000/meta_v12.json
e2eb7d4ccca761c5c5e1f2b37075f9baea245dac86cbe962fd9dc92aa574ef71  golomb_dickman_26.py
```

Все текстовые файлы — LF без BOM; политика закреплена в
[`../.gitattributes`](../.gitattributes), поэтому Windows-checkout с
`core.autocrlf=true` не изменит эти байты. Полный список — в
[`SHA256SUMS.txt`](SHA256SUMS.txt).

Хеш сам по себе ничего не доказывает: он только связывает имя файла с
байтами. Сверять его нужно с доверенным эталоном:

```bash
python ../verification/verify_certificate.py \
    --cert golomb_dickman_50000_certified.txt \
    --sha256-manifest SHA256SUMS.txt
```

Скрипт выводит для каждого входа либо `MATCH (manifest)` (или
`MATCH (--sha256)`), либо `computed, UNVERIFIED (no trusted reference)`.
Слова `OK` для непроверенного хеша он не печатает.

## Оговорки

- Сертификат и файл цифр, созданные 16.11.2026, поставлялись с CRLF.
  Сейчас они в канонической LF-форме; SHA-256 их CRLF-вариантов —
  `71ae993df6166a5334fee2775e75282c95d76c790dee0361a36120a8670cc9ce`
  (сертификат) и
  `bd4af9d2c4ccd345e792eb21c52c44a0506aa395ce9c1169b612337ca0a75a1c`
  (цифры). Содержимое — знаки и интервал — не менялось.
- `gd_rigorous_ckpt_50000/meta_v12.json` хранит
  `source_sha256=03c4ace9c3d7761b81f7681ea2710b854576643d0adf6c6213461b16d11c2f59`:
  это хеш вычислителя в том виде, в каком он был при прогоне (CRLF).
  Канонический LF-хеш того же кода —
  `e2eb7d4ccca761c5c5e1f2b37075f9baea245dac86cbe962fd9dc92aa574ef71`.
  Запись в плане не переписывалась: она описывает происхождение данных,
  а не текущее состояние файла.
- План прогона лежит в `gd_rigorous_ckpt_50000/meta_v12.json` (формат
  `gd-checkpoint-v12`), а не в старом `meta.pkl`; `meta.pkl` в этом
  каталоге нет. Аудит читает `D`, `S`, `h`, `K_L`, `K_R` из
  `meta_v12.json` и сверяет их с сертификатом и с фактическим набором
  блоков.
- Полный аудит всех узлов в Arb **не выполнялся**: `python-flint` не
  загружается на машине сборки (Application Control). Сертификат, как и для
  40 000 знаков, опирается на исходный прогон вычислителя.
- Независимое воспроизведение (уровень C) на 50 000 знаков не выполнялось.
  Прогон на 1 000 знаков (tanh-sinh и Gauss-Legendre, mpmath, без Arb)
  выполнен 23.11.2026 против файла `golomb_dickman_50000_digits.txt`: обе
  квадратуры совпали между собой и с файлом на 1 020 знаках; отчёт —
  [`../verification/reports/independent_1000_vs_50000.txt`](../verification/reports/independent_1000_vs_50000.txt).
  Это численная проверка, а не доказательство.
- Страница MathWorld «Golomb-Dickman Constant Digits» (снимок от
  23.11.2026) указывает **40 000** знаков, ссылается на статью на 40 000
  знаков и на коммит `87bdfe3`; 50 000 знаков там не упомянуты. Точная
  формулировка, снимок страницы и хеши —
  [`../verification/evidence/mathworld_mention_2026-11-23/`](../verification/evidence/mathworld_mention_2026-11-23/).
- Это расширение результата, а не заявка на мировой рекорд; о нормальности
  $\lambda$ ничего не утверждается.

## Как проверить

```bash
python ../verification/verify_certificate.py \
    --cert golomb_dickman_50000_certified.txt \
    --sha256-manifest SHA256SUMS.txt \
    --compare ../40000/golomb_dickman_40000_digits.txt

python ../verification/audit_chunks.py \
    --ckpt gd_rigorous_ckpt_50000 \
    --cert golomb_dickman_50000_certified.txt

# Независимый аудит всех 307 580 узлов в Arb (python-flint), часы:
python ../verification/verify_all_arb.py \
    --ckpt gd_rigorous_ckpt_50000 \
    --cert golomb_dickman_50000_certified.txt \
    --jobs 11

# Всё сразу; код возврата 0 только при полном PASS:
python ../verification/run_all.py --full-arb --arb-jobs 11
```

Первые два скрипта используют только стандартную библиотеку Python и точную
целочисленную арифметику; при любом расхождении они завершаются с ненулевым
кодом. `verify_all_arb.py` без `--limit-chunks` возвращает 2 (`NOT_RUN`),
если Arb недоступен, и 0 только когда пересчитаны все узлы и все интервалы
пересеклись.
