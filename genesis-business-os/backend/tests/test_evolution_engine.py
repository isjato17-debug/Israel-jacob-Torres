from app.route_engine import GenesisRouteEngine, FounderReality, DestinationContract

def test_evolution_respects_resource_envelope_and_is_simple():
    e=GenesisRouteEngine(); r=FounderReality(300,200,15,[],['phone'],'NY'); d=DestinationContract(5000,12,100)
    out=e.evolution(r,d,{'monthly_revenue':0,'repeat_customer_share':0,'gross_margin':.5,'capacity_used':.3})
    assert out['recommended_evolution']['estimated_cash_needed'] <= 100
    assert len(out['possible_futures']) <= 4
    assert 'guaranteed' in out['disclaimer'].lower()

def test_evolution_uses_real_signals():
    e=GenesisRouteEngine(); r=FounderReality(5000,2000,30,[],[],'NY'); d=DestinationContract(10000,12,3000)
    out=e.evolution(r,d,{'monthly_revenue':6000,'repeat_customer_share':.7,'gross_margin':.7,'capacity_used':.5})
    assert out['business_dna']['repeat_customer_signal']=='STRONG'
    assert out['business_dna']['margin_signal']=='HEALTHY'
