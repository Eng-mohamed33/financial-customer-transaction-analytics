# SQL analysis

الاستعلامات متوافقة مع **DuckDB** (وقريبة جدًا من PostgreSQL). كل القيم المالية بـ `amount_usd` (USD-equivalent بأسعار صرف توضيحية ثابتة) لأن المصدر يخلط USD/GBP/EUR.

## التشغيل

```bash
python scripts/run_sql.py
```

السكربت يحمّل `customers`, `accounts`, `transactions` من `data/processed/cleaned_*.csv` داخل DuckDB في الذاكرة، ثم ينفّذ كل ملفات `sql/*.sql` ويحفظ النتائج في `data/processed/sql_results/`.

## الملفات

- `customer_analysis.sql`: أعلى العملاء قيمة والعملاء بلا نشاط.
- `transaction_analysis.sql`: الحجم والقيمة شهريًا وبالنوع، وإجماليات العملات الأصلية.
- `financial_kpis.sql`: المؤشرات المالية (الرسوم منفصلة، والتحويلات الداخلية مستبعدة من القيمة).
