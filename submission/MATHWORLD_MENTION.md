# Фиксация факта упоминания на MathWorld

## Источники

Упомянуты **две страницы MathWorld**, обе обновлены 15 ноября 2026 г.:

1. **Основная:** <https://mathworld.wolfram.com/Golomb-DickmanConstant.html>
2. **С цифрами (указана пользователем):**
   <https://mathworld.wolfram.com/Golomb-DickmanConstantDigits.html>

- **Дата правки:** **2026-11-15** — согласно
  [New in MathWorld — November 2026](https://mathworld.wolfram.com/whatsnew/2026/11.html):
  под заголовком *Sunday November 15, 2026* перечислены
  `Golomb-Dickman Constant (modified)` и
  `Golomb-Dickman Constant Digits (modified)`.
- **Дата доступа/проверки:** 2026-11-26.
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
3. **Wayback Machine** — снимок страницы по адресу
   <https://web.archive.org/web/2026/https://mathworld.wolfram.com/Golomb-DickmanConstantDigits.html>.
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
Контрольные суммы — в `mathworld-evidence/SHA256SUMS.txt`; происхождение файлов
объяснено в `mathworld-evidence/README.md`.
