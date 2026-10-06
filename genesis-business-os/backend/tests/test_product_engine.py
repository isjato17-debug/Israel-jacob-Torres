from app.services.product_engine import founder_score,battle_mode,failure_lab,execution_plan
def test_founder_score_bounds(): assert 0 <= founder_score({'capital':10000,'hours_per_week':40,'experience_years':3,'risk_tolerance':6})['readiness'] <= 100
def test_battle_has_three(): assert len(battle_mode({'monthly_revenue':10000,'gross_margin':.5,'monthly_fixed_cost':3000}))==3
def test_failure_has_combined(): assert any(x['scenario']=='Combined downside' for x in failure_lab({'monthly_revenue':10000,'gross_margin':.5,'monthly_fixed_cost':3000}))
def test_execution_horizons(): assert {'today','week','month','90days'} <= {x['horizon'] for x in execution_plan('launch',10000)}
