# MathWorld evidence bundle

Captured 2026-11-26 from:

- `Constant.html` / `Constant.pdf` / `Constant-screenshot.png` —
  <https://mathworld.wolfram.com/Golomb-DickmanConstant.html>
- `ConstantDigits.html` / `ConstantDigits.pdf` / `ConstantDigits-screenshot.png` —
  <https://mathworld.wolfram.com/Golomb-DickmanConstantDigits.html>

`*-headers.txt` are the raw HTTP response headers saved by `curl.exe -D` at
the moment of capture (HTTP date: Thu, 26 Nov 2026 15:50:46 GMT). They are the
independent timestamp of the live fetch.

The PDF and PNG files were produced by headless Chrome from the **locally saved
HTML bytes** (`Constant.html`, `ConstantDigits.html`), not by a second network
request. This avoids a changing page while keeping the captured bytes exact.
Relative images may not render in the PDF; the text and the Pozdnyakov sentence
are preserved.

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
