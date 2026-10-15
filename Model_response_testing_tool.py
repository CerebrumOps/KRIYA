from openai import OpenAI


prompt = "Hi there!!"


client = OpenAI(
    base_url="http://100.98.154.51:8000/v1",
    api_key="sih2026"
)

response = client.chat.completions.create(
    model="default",
    messages=[{"role": "user", "content": prompt}],
    extra_body={
        "enable_thinking": False,
        "chat_template_kwargs": {"enable_thinking": False},
    },
)

print("Model : ", end = "")
print(response.choices[0].message.content)
print()