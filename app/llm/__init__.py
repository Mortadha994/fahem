"""Everything that reaches Groq.

Every call goes through llm_queue - see its docstring for why a request waits
its turn rather than failing on a 429. Around it: the streaming call, the
prompt construction, the gatekeeper that decides whether a message is for the
tutor at all, the usage accounting, and the switches the admin console turns
in ai_control.
"""
