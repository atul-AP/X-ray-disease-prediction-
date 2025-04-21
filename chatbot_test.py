from gpt4all import GPT4All
import os

model_name = "ggml-gpt4all-j-v1.3-groovy.bin"
model_dir = os.path.join(os.getcwd(), "models")

try:
    gpt_model = GPT4All(model_name=model_name, model_path=model_dir, allow_download=False)

    while True:
        prompt = input("You: ")
        if prompt.lower() == "exit":
            break

        with gpt_model.chat_session():
            response = gpt_model.generate(prompt=prompt, max_tokens=200)
        print("AI:", response.strip())

except Exception as e:
    print("❌ Error loading or generating:", str(e))
