from app.services.consultant import generate_candidates,financial_model,executive_board
def test_candidates(): assert len(generate_candidates('consulting',{'capital':5000}))==3
def test_finance(): assert financial_model({'monthly_revenue':10000,'gross_margin':.5,'monthly_fixed_cost':3000})['operating_profit']==2000
def test_board(): assert 'Cyber' in executive_board('scale?',{'monthly_revenue':10000,'gross_margin':.5,'monthly_fixed_cost':3000},[])['agents']
