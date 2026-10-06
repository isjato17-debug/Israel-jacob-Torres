import json, os, urllib.request

class AIProvider:
    def __init__(self):
        self.provider=os.getenv('GENESIS_AI_PROVIDER','disabled').lower()
        self.api_key=os.getenv('GENESIS_AI_API_KEY','')
        self.base_url=os.getenv('GENESIS_AI_BASE_URL','')
        self.model=os.getenv('GENESIS_AI_MODEL','')
    def enabled(self):
        return bool(self.provider!='disabled' and self.api_key and self.base_url and self.model)
    def structured_analysis(self, system_prompt, payload):
        if not self.enabled(): return None
        # OpenAI-compatible server-side adapter. No key is ever sent to the browser.
        body=json.dumps({'model':self.model,'messages':[{'role':'system','content':system_prompt},{'role':'user','content':json.dumps(payload)}],'response_format':{'type':'json_object'},'temperature':0.2}).encode()
        req=urllib.request.Request(self.base_url.rstrip('/')+'/chat/completions',data=body,headers={'Authorization':'Bearer '+self.api_key,'Content-Type':'application/json'})
        with urllib.request.urlopen(req,timeout=30) as r:
            data=json.loads(r.read())
        return json.loads(data['choices'][0]['message']['content'])

ai_provider=AIProvider()
