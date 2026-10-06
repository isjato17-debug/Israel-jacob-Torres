from app.route_engine import GenesisRouteEngine, FounderReality, DestinationContract
def test_reserve_never_spent():
    e=GenesisRouteEngine(); r=FounderReality(300,250,20,[],[]); d=DestinationContract(5000,12,300)
    assert e.spendable(r,d)==50
def test_reserve_above_cash_yields_zero():
    e=GenesisRouteEngine(); r=FounderReality(100,200,20,[],[]); d=DestinationContract(5000,12,100)
    assert e.spendable(r,d)==0
def test_location_reroute_invalidates_requirements():
    e=GenesisRouteEngine(); d=DestinationContract(5000,12,100)
    a=FounderReality(300,200,20,[],[],"NY"); b=FounderReality(300,200,20,[],[],"FL")
    x=e.reroute(a,b,d)
    assert "requirements" in x["invalidate_and_recompute"]
    assert x["authorization_recheck_required"] is True
def test_cash_change_does_not_invalidate_requirements():
    e=GenesisRouteEngine(); d=DestinationContract(5000,12,100)
    a=FounderReality(300,200,20,[],[],"NY"); b=FounderReality(250,200,20,[],[],"NY")
    x=e.reroute(a,b,d)
    assert "requirements" not in x["invalidate_and_recompute"]
