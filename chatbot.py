from gpt4all import GPT4All

model_path = r"D:\CU\AIML_project\Mistral-7B-Instruct-v0.3-Q4_K_M.gguf"

model = GPT4All(model_path)  # Load the model from local path

def medical_chatbot():
    print("🤖 AI Medical Chatbot - Type 'exit' to stop")
    while True:
        user_input = input("🧝‍♀️ You: ")
        if user_input.lower() == "exit":
            print("Chatbot: Goodbye! Stay healthy! 😊")
            break
        response = model.generate(user_input, max_tokens=200)
        print(f"Chatbot: {response}")

medical_chatbot()
 