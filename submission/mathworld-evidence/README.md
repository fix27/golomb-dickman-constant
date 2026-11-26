# MathWorld evidence bundle

Captured 2026-11-26 from:

- `Constant.html` / `Constant.pdf` / `Constant-screenshot.png` —
  <https://mathworld.wolfram.com/Golomb-DickmanConstant.html>
- `ConstantDigits.html` / `ConstantDigits.pdf` / `ConstantDigits-screenshot.png` —
  <https://mathworld.wolfram.com/Golomb-DickmanConstantDigits.html>

`*-headers.txt` are the raw HTTP response headers saved by `curl.exe -D` at
the moment of capture (HTTP date: Thu, 26 Nov 2026 15:50:46 GMT). They are the
independent timestamp of the live fetch.

`Constant.pdf`, `Constant-screenshot.png`, `ConstantDigits.pdf` and
`ConstantDigits-screenshot.png` were produced by headless Chrome from the
**locally saved HTML bytes** (`Constant.html`, `ConstantDigits.html`), not by a
second network request. This avoids a changing page while keeping the captured
bytes exact. Relative images may not render in these PDFs; the text and the
Pozdnyakov sentences are preserved.

`mathworld-golomb-dickman-2026-11-26.pdf` is different: it was printed directly
from the **live URL** by headless Edge at 2026-11-26 21:19 local time (the PNG
request in the same job did not produce a file). `pdftotext` confirms that it
contains "Pozdnyakov (2026) reports a computation of ... decimal digits" and
the full reference to `87bdfe…`. It is an independent live-page rendering of the
main *Golomb-Dickman Constant* page, complementing the earlier HTTP capture at
15:50 GMT.

`SHA256SUMS.txt` binds every file name to its bytes. Verify with
`sha256sum -c SHA256SUMS.txt` (or `Get-FileHash` on Windows).

Third-party timestamp in the Internet Archive:

- *Golomb-Dickman Constant Digits* — snapshot successfully requested on
  2026-11-26:
  <https://web.archive.org/web/20261126160603/https://mathworld.wolfram.com/Golomb-DickmanConstantDigits.html>
- *Golomb-Dickman Constant* — the `/save/` request timed out twice; use the
  generic capture link
  <https://web.archive.org/web/2026/https://mathworld.wolfram.com/Golomb-DickmanConstant.html>
  and re-check later.

The local HTTP headers, HTML and hashes above already fix the Digits page
independently of the Wayback Machine.
