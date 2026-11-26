# Фиксация факта упоминания на MathWorld

## Источники

Упомянуты **две страницы MathWorld**, обе добавлены в журнал обновлений
MathWorld 14 ноября 2026 г. (по дате сайта; подробности ниже):

1. **Основная:** <https://mathworld.wolfram.com/Golomb-DickmanConstant.html>
2. **С цифрами (указана пользователем):**
   <https://mathworld.wolfram.com/Golomb-DickmanConstantDigits.html>

- **Дата правки по журналу MathWorld:** **2026-11-14** (по дате сайта) —
  согласно [New in MathWorld — November 2026](https://mathworld.wolfram.com/whatsnew/2026/11.html),
  обе страницы (`Golomb-Dickman Constant (modified)` и
  `Golomb-Dickman Constant Digits (modified)`) стоят в разделе
  *Saturday November 14, 2026*. Это подтверждено разбором HTML: ближайший
  заголовок даты перед ссылкой — `Saturday November 14, 2026`.
- **Дата процитированного коммита:** `87bdfe…` датирован
  `2026-11-15T03:01:07+04:00` (= `2026-11-14T23:01:07Z`), то есть тот же
  день по UTC и уже 15-е по местному времени. Не путать с датой правки
  страницы: 15 ноября — это дата коммита, а не обновления MathWorld.
- **Дата доступа/проверки:** 2026-11-26.
- **Более ранняя фиксация:** `verification/evidence/mathworld_mention_2026-11-23/`
  (доступ 2026-11-23, футер страницы `Last Updated: Mon Nov 23 2026` —
  общесайтовая метка, а не дата правки).
- **Каноническая цитата страницы:** Weisstein, Eric W. "Golomb-Dickman Constant
  Digits." From *MathWorld* — A Wolfram Resource.
  <https://mathworld.wolfram.com/Golomb-DickmanConstantDigits.html>.

> Примечание: новая отправка в MathWorld **не требуется** — упоминание уже
> опубликовано. Задача этой записи — зафиксировать факт, а не инициировать
> правку страницы.

## Дословные формулировки

### Страница «Golomb-Dickman Constant Digits»

Таблица «reported computations of the constant's decimal digits»:

| decimal digits | computation |
|---|---|
| 53 | Mitchell (1968) |
| 15,000 | E. Weisstein (Jul. 25, 2013) |
| **40,000** | **Pozdnyakov (2026)** |

Сразу после таблицы:

> **Pozdnyakov (2026) provides digit data and computation code.**

Ссылка в разделе References (дословно):

> Pozdnyakov, K. N. "Forty Thousand Certified Decimal Digits of the
> Golomb-Dickman Constant." 2026.
> <https://github.com/fix27/golomb-dickman-constant/blob/87bdfe378c3197b9710ed919f72ac9df28f9dcb3/paper/main.tex>.
> Digit data and code:
> <https://github.com/fix27/golomb-dickman-constant/tree/87bdfe378c3197b9710ed919f72ac9df28f9dcb3/40000>.

### Страница «Golomb-Dickman Constant»

> Pozdnyakov (2026) reports a computation of **40000 decimal digits**.

Библиографическая ссылка там же совпадает с приведённой выше.

## Что именно упомянуто

| Элемент | Присутствует | Комментарий |
|---|---|---|
| Автор | Да | `Pozdnyakov (2026)`, `Pozdnyakov, K. N.` |
| Число знаков | Да | **40 000** decimal digits |
| Название работы | Да | "Forty Thousand Certified Decimal Digits of the Golomb-Dickman Constant" |
| GitHub | Да | `github.com/fix27/golomb-dickman-constant`, зафиксирован на коммите `87bdfe378c3197b9710ed919f72ac9df28f9dcb3` |
| Код и данные | Да | ссылка `Digit data and code` на каталог `/40000` того же коммита |
| Препринт | Да | `paper/main.tex` на том же коммите |
| Алгоритм | Нет | метод, параметры, сертификат и верификатор на странице не описаны |
| Сертификат/интервальная арифметика | Нет | слово `certified` есть только в названии работы |
| 30 000 / 50 000 / 75 000 | Нет | страницы упоминают только 40 000 |
| «Рекорд» | Нет | никаких заявлений о рекорде |

## Способы фиксации факта

1. **Локальный снимок + PDF** с контрольными суммами — `mathworld-evidence/`.
2. **Заголовки HTTP ответа** (`Date`, `Last-Modified`, `ETag`) —
   `mathworld-evidence/*-headers.txt`, получены через `curl.exe -D`.
3. **Wayback Machine** — снимок страницы с цифрами запрошен 2026-11-26 и
   доступен по адресу
   <https://web.archive.org/web/20261126160603/https://mathworld.wolfram.com/Golomb-DickmanConstantDigits.html>;
   запрос для основной страницы дважды истёк по таймауту (повторить позже).
4. **Пермалинк на коммит GitHub** — уже используется в самой ссылке MathWorld
   (`87bdfe…`); он неизменен даже при движении ветки `main`.
5. **Машиночитаемая цитата** — `CITATION.cff` и `README.md` с датой доступа.
6. **Архив релиза с DOI** — TODO после публикации release/Zenodo; каноническая
   ссылка для будущих цитирований.

## Письмо в редакцию

Черновик [`mathworld-thanks.eml`](mathworld-thanks.eml) подготовлен, но
**не отправляется**: пользователь сообщил, что новая отправка пока не нужна.

## Доказательства

Снимки, PDF, HTML и заголовки HTTP находятся в
[`mathworld-evidence/`](mathworld-evidence/): `Constant.html/.pdf/-screenshot.png`
и `ConstantDigits.html/.pdf/-screenshot.png`, заголовки — в `*-headers.txt`.
Дополнительно `mathworld-golomb-dickman-2026-11-26.pdf` — прямая печать
живой страницы через Edge в 21:19 (не из сохранённого HTML); `pdftotext`
подтверждает наличие формулировки про 40 000 знаков и ссылки на коммит
`87bdfe…`. Контрольные суммы — в `mathworld-evidence/SHA256SUMS.txt`;
происхождение файлов объяснено в `mathworld-evidence/README.md`.
