# Инвойс для Moonton Philippines Technology Inc

Готовый инвойс по документам:

- `7688586818559983659-1-1.pdf` — Framework Agreement on Content Outsourcing Production от 18.09.2026 + Exhibit A (Order No. 1) + Authorization Letter от 10.09.2026;
- `[VIKTOR]_Addendum_to_Content_Outsourcing_Production_Agreement_(1).pdf` — Addendum от 14.10.2026 (доп. работа Chibi Version, пересмотренная сумма);
- реквизиты плательщика, присланные вами в сообщении.

## Файлы

| Файл | Что это |
| --- | --- |
| `Invoice_INV-2026-001_Moonton.pdf` | **Основной документ** — готовый к отправке инвойс, 1 страница A4, английский язык |
| `invoice.html` | Та же информация в HTML: можно открыть в браузере, распечатать в PDF или отредактировать |
| `invoice_data.json` | Единый источник данных (все суммы, даты, реквизиты, позиции, примечания) |
| `invoice_template.html` | HTML-шаблон с плейсхолдерами `{{...}}` |
| `build.py` | Собирает HTML и PDF из `invoice_data.json` |

Пересборка после правок:

```bash
pip install pymupdf
python3 invoice/build.py
```

## Что в инвойсе

- **Сумма:** USD 2 800.00 = USD 1 500.00 (Order No. 1, Layla TikTok Effect Filter) + USD 1 300.00 (Chibi Version по Addendum). Это Revised Total Fee из раздела 3 Addendum.
- **Плательщик:** Moonton Philippines Technology Inc, 23F The Curve Building, 32nd Street, Bonifacio Global City, Taguig City, Philippines; adminph@moonton.com; VAT Reg TIN 602-837-083-000.
- **Поставщик (From):** Viktor Vlasov, Izhevsk, lednique@gmail.com.
- **Получатель платежа:** Maksim Kuzlin, REVOLUT BANK UAB, IBAN FR76 2823 3000 0155 9947 9578 845, SWIFT REVOFRP2, USD — по разделу 5.1 Agreement и Authorization Letter от 10.09.2026. Поэтому «From» и «Beneficiary» — разные люди; это не ошибка.
- **Условия оплаты:** 30 календарных дней с момента получения инвойса **и** подписанного обеими сторонами balance statement (раздел 5.2). Дата 25.11.2026 указана из расчёта, что документ получен 26.10.2026.
- **Налоги:** цены уже включают все банковские комиссии, налоги, пошлины и withholding taxes (раздел 5.3), отдельная строка VAT не начисляется — суммы 0.00.
- Внизу есть блоки подписей: подпись провайдера + подпись/печать компании (это же служит balance statement по 5.2).

## ⚠️ Что нужно проверить / заменить перед отправкой

1. **Номер и дата инвойса** — `INV-2026-001` и `26 October 2026` — черновые. Замените на свои (`invoice_no`, `invoice_date`, `due_date` в `invoice_data.json`).
2. **Contract No. `FA-2026-0918-VV`** — придуман, потому что в Agreement числового номера договора нет (есть только DocuSign Envelope ID; они приведены в примечании 2). Если у Moonton есть внутренний номер контракта/PO — вставьте его.
3. **Сумма 2 800 USD.** Если первые 1 500 USD уже были проинвойсированы/оплачены, нужно выставить счёт только на 1 300 USD: уберите первую позицию, измените `subtotal`, `total`, `amount_in_words` и примечание 4.
4. **Адрес компании:** вы прислали `23F The Curve Building`, а в Agreement и Addendum указано `3F`. В инвойсе стоит ваш вариант `23F` — сверьте с Moonton.
5. **E-mail компании:** использован присланный вами `adminph@moonton.com`; контакт из договора (Jessica Woo, jessicawoo@moonton.com) добавлен строкой «Agreement contact» — при желании поменяйте местами.
6. **Даты поставки** скопированы из документов как есть: 26.09.2026 и 07.10.2026. Обратите внимание, что Addendum датирован 14.10.2026, а due date доп. работы в нём — 07.10.2026. Если это опечатка в Addendum, поправьте `items[1].date`.
7. **VAT/withholding:** по разделу 5.3 все налоги уже включены в цену. Если финансовая служба Moonton потребует отдельные VAT-реквизиты провайдера или удержит налог у источника, уточните у них до отправки — у провайдера (физлицо, РФ) такого номера в документах нет.
8. Инвойс на английском: договор и плательщик англоязычные. Русская версия может быть сделана отдельно, но для оплаты обычно используют этот вариант.
