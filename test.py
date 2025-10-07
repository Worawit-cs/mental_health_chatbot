# from litellm import completion, supports_function_calling, supports_response_schema
import litellm
from backend.config import MODEL
print("MODEL:", MODEL)
print("supports function calling:", litellm.supports_function_calling(model=MODEL))
print("supports response schema:", litellm.supports_response_schema(model=MODEL))
print("supports reasoning:", litellm.supports_reasoning(model=MODEL))
# minimal request
# r = litellm.completion(model=MODEL, messages=[{"role":"user","content":"Say hi in 3 words"}])
# print("OK:", r.choices[0].message["content"])
