"""Download Core (+ optional Enc) into data/raw/."""

from __future__ import annotations

import argparse
import os


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--enc", action="store_true", help="Also download QuranEnc/HadeethEnc")
    parser.add_argument(
        "--enc-full",
        action="store_true",
        help="Full Enc pin: all QuranEnc suras + all HadeethEnc items",
    )
    args = parser.parse_args(argv)

    from pipeline.download_hadith import main as download_hadith
    from pipeline.download_quran import main as download_quran

    download_quran()
    download_hadith()

    want_enc = (
        args.enc
        or args.enc_full
        or os.environ.get("MUHAQQIQ_DOWNLOAD_ENC", "").strip().lower()
        in {"1", "true", "yes"}
    )
    if want_enc:
        from pipeline.download_hadeethenc import main as download_hadeethenc
        from pipeline.download_quranenc import main as download_quranenc

        enc_argv = ["--full"] if args.enc_full else []
        download_quranenc(enc_argv)
        download_hadeethenc([*enc_argv, "--refresh-ids"] if args.enc_full else enc_argv)
        print("Core + Enc downloads complete → data/raw/download_manifest.json")
    else:
        print("Core downloads complete → data/raw/download_manifest.json")
        print("Pass --enc / --enc-full for QuranEnc/HadeethEnc.")


if __name__ == "__main__":
    main()
