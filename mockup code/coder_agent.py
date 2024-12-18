from together import Together
import os

class CoderModule:
    def __init__(self, model_name="Qwen/Qwen2.5-Coder-32B-Instruct", output_dir="generated_code"):
        self.client = Together()
        self.model_name = model_name
        self.output_dir = output_dir

        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def generate_code(self, requirements, max_tokens=1024, temperature=0, top_p=0.9, top_k=50):
        """
        Generate code based on the provided requirements.
        """
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": """You are a coding assistant that writes modular, clean, and production-ready code based on the requirements supplied by the user.
                 IMPORTANT:
                 1. Give code ONLY in triple back ticks (```) with the programming language mentioned explicitly.
                 2. You are capable of writing clean and production ready for every thing that can be possibly exist.
                 3. Whenever you are giving code for a different module, give them in seperate back ticks so that they can be saved in different files.
                 4. All modules must be well connected, so that the user can just copy paste them into files and can run them successfully without requiring him/her to change anything.
                 5. Whenever there is a module change, close the back ticks of the previous module and mention the word "MODULE CHANGE" explicitly before starting the next module.
                 6. First line of each module must be a comment mentioning the file name for the module.
                 7. Apart from code, ONLY setup and execution information must be present with explicit heading "RUNNING INSTRUCTIONS" and this instructions portion of your response must NOT contain back ticks or inverted commas anywhere, neither in headings, nor in steps mentioned nor anywhere else.
                 8. Not following any of the above instructions will levy penalty."""},
                {"role": "user", "content": requirements}
            ],
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            repetition_penalty=1,
            stop=["<|im_end|>"],
            stream=True
        )

        # Extract and return generated code using a streaming approach
        generated_code = ""
        for token in response:
            if hasattr(token, 'choices'):
                generated_code += token.choices[0].delta.content
        print(generated_code)
        return generated_code

    def save_code(self, code):
        """
        Save the generated code to a file.
        """
        file_path = os.path.join(self.output_dir, filename)
        with open(file_path, "w") as file:
            file.write(code)
        print(f"Code saved to {file_path}")

    def process_requirements(self, requirements):
        """
        Process the requirements, generate code, and save it.
        Handles multiple modules if specified in the requirements.
        """
        try:
            # Generate code
            generated_code = self.generate_code(requirements)

            # Check for multiple modules (simple heuristic)
            if "MODULE CHANGE" in generated_code:
                # Split the code into multiple modules using a delimiter
                modules = generated_code.split("MODULE CHANGE")
                for module in modules:
                    module = module.strip()
                    if module.startswith("```") and module.endswith("```"):
                        # Remove triple backticks and split module name and content
                        module_content = module[3:-3].strip()
                        if "\n" in module_content:
                            header, body = module_content.split("\n", 1)
                            if header.startswith("#"):
                                module_name = header[1:].strip() + ".py"
                                self.save_code(body.strip(), module_name)
            else:
                # Save as a single file if no module delimiter is found
                self.save_code(generated_code)

        except Exception as e:
            print(f"Error: {e}")

# Example usage
if __name__ == "__main__":
    coder = CoderModule()
    requirements = "Create a Python program with two modules: one for handling database operations and another for a REST API server. The database module should connect to SQLite and provide basic CRUD operations. The API module should use Flask to expose CRUD operations over HTTP."
    coder.process_requirements(requirements)
