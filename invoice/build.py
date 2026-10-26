#!/usr/bin/env python3
"""Build the invoice (HTML + print-ready A4 PDF) from invoice_data.json.

    pip install pymupdf
    python3 invoice/build.py

Outputs:
    invoice/invoice.html                        - view / print from a browser
    invoice/Invoice_INV-2026-001_Moonton.pdf    - send to the client
"""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

import pymupdf

HERE = Path(__file__).resolve().parent
DATA = json.loads((HERE / "invoice_data.json").read_text(encoding="utf-8"))
HTML_OUT = HERE / "invoice.html"
PDF_OUT = HERE / "Invoice_INV-2026-001_Moonton.pdf"


# ---------------------------------------------------------------------------
# 1. HTML version (templated, easy to edit / print from a browser)
# ---------------------------------------------------------------------------
def e(value: str) -> str:
    return html.escape(str(value), quote=False)


def build_html() -> None:
    d = DATA
    items = []
    for it in d["items"]:
        items.append(
            f"""    <tr>
      <td class="c-num center">{e(it['no'])}</td>
      <td class="c-desc">
        <div class="item-name">{e(it['name'])}</div>
        <div class="item-desc">{e(it['desc'])}</div>
        <div class="item-ref">{e(it['ref'])}</div>
      </td>
      <td class="c-date">{e(it['date'])}</td>
      <td class="c-qty center">{e(it['qty'])}</td>
      <td class="c-price right nowrap">{e(it['unit_price'])}</td>
      <td class="c-amount right nowrap"><b>{e(it['amount'])}</b></td>
    </tr>"""
        )
    payments = "\n".join(
        f'  <tr><td class="k">{e(k)}</td><td class="v">{e(v)}</td></tr>'
        for k, v in d["payment_rows"]
    )
    notes = "\n".join(f"  <li>{e(n)}</li>" for n in d["notes"])

    values = {
        "INVOICE_NO": e(d["invoice_no"]),
        "INVOICE_DATE": e(d["invoice_date"]),
        "CONTRACT_NO": e(d["contract_no"]),
        "ORDER_NO": e(d["order_no"]),
        "PAYMENT_TERMS": e(d["payment_terms"]),
        "DUE_DATE": e(d["due_date"]),
        "CURRENCY": e(d["currency"]),
        "SUBTITLE": e(d["subtitle"]),
        "AGREEMENT_LINE1": e(d["agreement_line1"]),
        "AGREEMENT_LINE2": e(d["agreement_line2"]),
        "PROVIDER_NAME": e(d["provider"]["name"]),
        "PROVIDER_ROLE": e(d["provider"]["role"]),
        "PROVIDER_ADDRESS": e(d["provider"]["address"]),
        "PROVIDER_EMAIL": e(d["provider"]["email"]),
        "PROVIDER_TAX_NOTE": e(d["provider"]["tax_note"]),
        "COMPANY_NAME": e(d["company"]["name"]),
        "COMPANY_ADDRESS1": e(d["company"]["address1"]),
        "COMPANY_ADDRESS2": e(d["company"]["address2"]),
        "COMPANY_EMAIL": e(d["company"]["email"]),
        "COMPANY_VAT": e(d["company"]["vat"]),
        "COMPANY_CONTACT_NOTE": e(d["company"]["contact_note"]),
        "ITEMS_ROWS": "\n".join(items),
        "SUBTOTAL": e(d["subtotal"]),
        "VAT_TAXES": e(d["vat_taxes"]),
        "BANK_CHARGES": e(d["bank_charges"]),
        "TOTAL": e(d["total"]),
        "AMOUNT_IN_WORDS": e(d["amount_in_words"]),
        "TOTAL_NOTE": e(d["total_note"]),
        "PAYMENT_ROWS": payments,
        "PAYMENT_NOTE": e(d["payment_note"]),
        "NOTES": notes,
        "FOOTER": e(d["footer"]),
    }

    template = (HERE / "invoice_template.html").read_text(encoding="utf-8")
    missing = set(re.findall(r"\{\{(\w+)\}\}", template)) - set(values)
    if missing:
        raise KeyError(f"Unfilled template tokens: {sorted(missing)}")
    HTML_OUT.write_text(
        re.sub(r"\{\{(\w+)\}\}", lambda m: values[m.group(1)], template),
        encoding="utf-8",
    )
    print(f"Wrote {HTML_OUT}")


# ---------------------------------------------------------------------------
# 2. PDF version (fixed A4 layout, no external fonts needed)
# ---------------------------------------------------------------------------
PW, PH = pymupdf.paper_size("a4")
L, R = 36.0, PW - 36.0
W = R - L

F, FB = "helv", "hebo"  # Helvetica / Helvetica-Bold (standard PDF fonts)


def rgb(hex_color: str) -> tuple[float, float, float]:
    h = hex_color.lstrip("#")
    return tuple(int(h[i : i + 2], 16) / 255 for i in (0, 2, 4))


NAVY = rgb("#123c63")
TEXT = rgb("#24303d")
DESC = rgb("#4e5b69")
MUTED = rgb("#6b7887")
FAINT = rgb("#8a95a2")
BORDER = rgb("#d7dee7")
PANEL = rgb("#f5f8fb")
BOXBG = rgb("#fafbfd")
WHITE = (1.0, 1.0, 1.0)

page: pymupdf.Page | None = None


def rect(x0, y0, x1, y1, fill=None, stroke=None, sw=0.6) -> None:
    page.draw_rect(
        pymupdf.Rect(x0, y0, x1, y1), color=stroke, fill=fill, width=sw
    )


def hline(x0, x1, y, col=BORDER, sw=0.5) -> None:
    page.draw_line((x0, y), (x1, y), color=col, width=sw)


def vline(x, y0, y1, col=BORDER, sw=0.5) -> None:
    page.draw_line((x, y0), (x, y1), color=col, width=sw)


def text(x, y, s, size=8, font=F, col=TEXT) -> None:
    page.insert_text((x, y), str(s), fontname=font, fontsize=size, color=col)


def text_right(xr, y, s, size=8, font=F, col=TEXT) -> None:
    width = pymupdf.get_text_length(str(s), fontname=font, fontsize=size)
    text(xr - width, y, s, size, font, col)


def text_center(xc, y, s, size=8, font=F, col=TEXT) -> None:
    width = pymupdf.get_text_length(str(s), fontname=font, fontsize=size)
    text(xc - width / 2, y, s, size, font, col)


def wrap(s, width, size, font=F) -> list[str]:
    lines, current = [], ""
    for word in str(s).split():
        trial = word if not current else current + " " + word
        if pymupdf.get_text_length(trial, fontname=font, fontsize=size) <= width or not current:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def para(x, top, width, s, size=8, font=F, col=TEXT, lh=None, draw=True) -> float:
    """Draw a wrapped paragraph; return the y of its bottom."""
    lh = lh or size * 1.30
    lines = wrap(s, width, size, font)
    if draw:
        for i, ln in enumerate(lines):
            text(x, top + size * 0.94 + i * lh, ln, size, font, col)
    return top + len(lines) * lh


def sec(x, y, s) -> float:
    text(x, y, str(s).upper(), 7.6, FB, NAVY)
    return y + 5


def build_pdf() -> None:
    global page
    d = DATA
    doc = pymupdf.open()
    page = doc.new_page(width=PW, height=PH)

    # ---------------- header ----------------
    y = 26.0
    text(L, y + 27, "INVOICE", 26, FB, NAVY)
    text(L, y + 41, d["subtitle"], 8, F, MUTED)
    para(L, y + 52, 256, d["agreement_line1"] + " " + d["agreement_line2"], 8, F, MUTED, 10)

    meta_rows = [
        ("Invoice No.", d["invoice_no"]),
        ("Invoice date", d["invoice_date"]),
        ("Contract No.", d["contract_no"]),
        ("Order No.", d["order_no"]),
        ("Payment terms", d["payment_terms"]),
        ("Due date", d["due_date"]),
        ("Currency", d["currency"]),
    ]
    mx0, rh = 300.0, 15.0
    panel_h = rh * len(meta_rows)
    rect(mx0, y, R, y + panel_h, fill=PANEL, stroke=BORDER)
    for i, (k, v) in enumerate(meta_rows):
        ry = y + i * rh
        if i < len(meta_rows) - 1:
            hline(mx0, R, ry + rh, BORDER, 0.4)
        text(mx0 + 7, ry + 10, k, 8, F, MUTED)
        text_right(R - 7, ry + 10, v, 8, FB, NAVY)

    rule_y = y + panel_h + 7
    hline(L, R, rule_y, NAVY, 2.4)
    y = rule_y + 12

    # ---------------- parties ----------------
    col_w = (W - 10) / 2
    left_x, right_x = L, L + col_w + 10
    p, c = d["provider"], d["company"]
    party_specs = [
        (
            left_x, "ISSUED BY", p["name"],
            [
                (p["role"], 8.4, TEXT, F),
                (p["address"], 8.4, TEXT, F),
                (f"E-mail: {p['email']}", 8.4, TEXT, FB),
                (p["tax_note"], 7.2, MUTED, F),
            ],
        ),
        (
            right_x, "SENDER OF MONEY", c["name"],
            [
                (c["address1"], 8.4, TEXT, F),
                (c["address2"], 8.4, TEXT, F),
                (f"E-mail: {c['email']}", 8.4, TEXT, FB),
                (f"VAT Reg TIN No.: {c['vat']}", 8.4, TEXT, FB),
                (c["contact_note"], 7.2, MUTED, F),
            ],
        ),
    ]

    def draw_party(x, top, tag, name, lines, draw=True) -> float:
        if draw:
            text(x + 8, top + 13, tag, 6.8, FB, MUTED)
            text(x + 8, top + 29, name, 10, FB, NAVY)
        cy = top + 34
        for s, size, col, font in lines:
            cy = para(x + 8, cy, col_w - 16, s, size, font, col, size * 1.28, draw) + 1.5
        return cy + 2

    sec(L, y, "From / Provider")
    sec(right_x, y, "Bill To / Company (Payer)")
    box_top = y + 5
    box_h = max(
        draw_party(x, box_top, tag, name, lines, draw=False)
        for x, tag, name, lines in party_specs
    ) - box_top
    for x, tag, name, lines in party_specs:
        rect(x, box_top, x + col_w, box_top + box_h, fill=BOXBG, stroke=BORDER)
        draw_party(x, box_top, tag, name, lines)
    y = box_top + box_h + 9

    # ---------------- deliverables ----------------
    sec(L, y, "Deliverables / Services")
    y += 6
    widths = [20, 275, 62, 24, 68, W - 449]  # sum = W
    xs = [L]
    for w in widths:
        xs.append(xs[-1] + w)
    header_h = 18.0
    rect(L, y, R, y + header_h, fill=NAVY)
    headers = ["#", "Deliverable & description", "Delivery date", "Qty", "Unit price", "Amount (USD)"]
    aligns = ["center", "left", "left", "center", "right", "right"]
    for i, (label, align) in enumerate(zip(headers, aligns)):
        bx = y + 12
        if align == "center":
            text_center((xs[i] + xs[i + 1]) / 2, bx, label, 7.4, FB, WHITE)
        elif align == "right":
            text_right(xs[i + 1] - 5, bx, label, 7.4, FB, WHITE)
        else:
            text(xs[i] + 5, bx, label, 7.4, FB, WHITE)
    y += header_h

    desc_w = widths[1] - 10
    for it in d["items"]:
        n_name = len(wrap(it["name"], desc_w, 8.8, FB))
        n_desc = len(wrap(it["desc"], desc_w, 7.8, F))
        n_ref = len(wrap(it["ref"], desc_w, 7.2, F))
        row_h = 5 + n_name * 10.5 + 1.5 + n_desc * 9.4 + 1.5 + n_ref * 8.6 + 5
        rect(L, y, R, y + row_h, stroke=BORDER, sw=0.5)
        for cx in xs[1:-1]:
            vline(cx, y, y + row_h, BORDER, 0.5)

        cy = y + 4
        cy = para(xs[1] + 5, cy, desc_w, it["name"], 8.8, FB, NAVY, 10.5) + 1.5
        cy = para(xs[1] + 5, cy, desc_w, it["desc"], 7.8, F, DESC, 9.4) + 1.5
        para(xs[1] + 5, cy, desc_w, it["ref"], 7.2, F, FAINT, 8.6)

        text_center((xs[0] + xs[1]) / 2, y + 13, it["no"], 8.2)
        text(xs[2] + 5, y + 13, it["date"], 8.2)
        text_center((xs[3] + xs[4]) / 2, y + 13, it["qty"], 8.2)
        text_right(xs[5] - 5, y + 13, it["unit_price"], 8.2)
        text_right(R - 5, y + 13, it["amount"], 8.2, FB)
        y += row_h
    y += 6

    # ---------------- totals ----------------
    left_box_w = 292.0
    tx = L + 300.0
    words_prefix = "Amount in words: "
    prefix_w = pymupdf.get_text_length(words_prefix, fontname=FB, fontsize=8)
    words_rest = wrap(d["amount_in_words"] + ".", left_box_w - 16 - prefix_w, 8, F)
    note_lines = wrap(d["total_note"], left_box_w - 16, 7.6, F)
    words_h = 8 + (len(words_rest) + len(note_lines)) * 9.5 + 6
    totals_rows = [
        ("Subtotal", f"USD {d['subtotal']}"),
        ("VAT / taxes / duties (inclusive)", f"USD {d['vat_taxes']}"),
        ("Bank charges (inclusive)", f"USD {d['bank_charges']}"),
        ("TOTAL DUE", f"USD {d['total']}"),
    ]
    totals_h = 3 * 15 + 22
    block_h = max(words_h, totals_h)

    rect(L, y, L + left_box_w, y + block_h, fill=PANEL, stroke=BORDER)
    text(L + 8, y + 15, words_prefix, 8, FB, TEXT)
    for i, ln in enumerate(words_rest):
        if i == 0:
            text(L + 8 + prefix_w, y + 15, ln, 8, F, TEXT)
        else:
            text(L + 8, y + 15 + 10 * i, ln, 8, F, TEXT)
    for j, ln in enumerate(note_lines):
        text(L + 8, y + 18 + 9.5 * len(words_rest) + 9.5 * j, ln, 7.6, F, MUTED)

    ty = y
    for i, (k, v) in enumerate(totals_rows):
        h = 22 if i == len(totals_rows) - 1 else 15
        if i == len(totals_rows) - 1:
            rect(tx, ty, R, ty + h, fill=NAVY)
        else:
            hline(tx, R, ty + h, BORDER, 0.5)
        text(tx + 7, ty + (14 if i == len(totals_rows) - 1 else 10),
             k, 9.8 if i == len(totals_rows) - 1 else 8.4,
             FB if i == len(totals_rows) - 1 else F,
             WHITE if i == len(totals_rows) - 1 else TEXT)
        text_right(R - 7, ty + (14 if i == len(totals_rows) - 1 else 10),
                   v, 9.8 if i == len(totals_rows) - 1 else 8.4,
                   FB if i == len(totals_rows) - 1 else F,
                   WHITE if i == len(totals_rows) - 1 else TEXT)
        ty += h
    y += block_h + 8

    # ---------------- payment instructions ----------------
    sec(L, y, "Payment instructions / Beneficiary")
    y += 6
    pay_h = len(d["payment_rows"]) * 12.5 + 10
    rect(L, y, R, y + pay_h, fill=BOXBG, stroke=BORDER)
    rect(L, y, L + 3, y + pay_h, fill=NAVY)
    for i, (k, v) in enumerate(d["payment_rows"]):
        by = y + 10 + i * 12.5
        text(L + 12, by, k, 8.2, F, MUTED)
        text(L + 132, by, v, 8.2, FB, TEXT)
    y += pay_h + 3
    y = para(L, y, W, d["payment_note"], 7.2, F, MUTED, 8.6) + 7

    # ---------------- notes ----------------
    sec(L, y, "Notes and conditions")
    y += 5
    for i, n in enumerate(d["notes"]):
        lines = wrap(n, W - 16, 7.5, F)
        text(L, y + 8, f"{i + 1}.", 7.5, F, DESC)
        for j, ln in enumerate(lines):
            text(L + 14, y + 8 + j * 9.0, ln, 7.5, F, DESC)
        y += len(lines) * 9.0 + 1.5
    y += 7

    # ---------------- signatures ----------------
    sign_cols = [
        (L, "For and on behalf of the Provider",
         f"{p['name']}, Creator · Signature / Date"),
        (right_x, "Acknowledged by the Company (balance statement, sec. 5.2)",
         f"{c['name']} · Signature / Stamp / Date"),
    ]
    for x, title, label in sign_cols:
        text(x, y + 8, title, 8, FB, TEXT)
        hline(x, x + col_w - 8, y + 32, MUTED, 0.6)
        text(x, y + 43, label, 7.4, F, MUTED)
    y += 50

    # ---------------- footer ----------------
    hline(L, R, y, BORDER)
    footer = f"Invoice {d['invoice_no']} · {d['invoice_date']} · {d['footer']}"
    y = para(L, y + 4, W, footer, 7, F, FAINT, 8.6)

    if y > PH - 18:
        print(f"WARNING: content bottom y={y:.1f} exceeds safe limit {PH - 18:.1f}")

    doc.set_metadata(
        {
            "title": f"Invoice {d['invoice_no']} — USD {d['total']}",
            "author": p["name"],
            "subject": "Framework Agreement on Content Outsourcing Production "
                       "dated 18 September 2026 / Addendum dated 14 October 2026 / Order No. 1",
            "keywords": f"invoice, {d['invoice_no']}, {d['contract_no']}, Order No. 1",
        }
    )
    doc.save(PDF_OUT, garbage=4, deflate=True)
    print(f"Wrote {PDF_OUT} (1 page, content bottom y={y:.1f}/{PH:.0f})")


if __name__ == "__main__":
    build_html()
    build_pdf()
