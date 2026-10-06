# Financial Precision Gate
Reference Route arithmetic currently uses floating-point numbers for planning estimates. Before money-moving/accounting-grade use:
- use Decimal/fixed-point for currency;
- define rounding per currency and provider;
- reject NaN/Infinity and impossible percentages;
- distinguish revenue, gross profit, contribution margin, operating profit, cash and owner income;
- version assumptions and formulas;
- handle taxes/fees only when sourced and applicable;
- stress-test zero revenue, zero margin, negative actual results, refunds, chargebacks, debt, inventory and seasonal cash flow;
- never present projections as guaranteed outcomes.
