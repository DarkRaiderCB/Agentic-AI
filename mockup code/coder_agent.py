from together import Together
import os
import logging

class CoderModule:
    def __init__(self, model_name="Qwen/Qwen2.5-Coder-32B-Instruct", output_dir="generated_code"):
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        self.client = Together()
        self.model_name = model_name
        self.output_dir = output_dir

        # Create output directory if it doesn't exist
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            self.logger.info(f"Created output directory: {self.output_dir}")

    def generate_code(self, requirements, max_tokens=None, temperature=0, top_p=0.9, top_k=50):
        """
        Generate code based on the provided requirements.
        """
        self.logger.info("Generating code for requirements...")
        
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
                 6. Remember that the first line of each module must be a comment mentioning the file name for the module. it must be given inside the same triple back ticks that contain the codes also.
                 7. Apart from code, ONLY setup and execution information must be present with explicit heading "RUNNING INSTRUCTIONS" and this instructions portion of your response must NOT contain back ticks or inverted commas anywhere, neither in headings, nor in steps mentioned nor anywhere else.
                 8. Never use triple back ticks (```) for the content under "RUNNING INSRUCTIONS".
                 9. Not following any of the above instructions will levy penalty."""},
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

        generated_code = ""
        try:
            for token in response:
                if hasattr(token, 'choices') and hasattr(token.choices[0], 'delta') and hasattr(token.choices[0].delta, 'content'):
                    generated_code += token.choices[0].delta.content
            print(generated_code)
            self.logger.info("Code generation completed successfully")
            return generated_code
        except Exception as e:
            self.logger.error(f"Error during code generation: {str(e)}")
            raise

    def extract_code_blocks(self, text):
        """
        Extract code blocks from the generated text.
        Returns a list of tuples (filename, code_content)
        """
        code_blocks = []
        self.logger.info("Starting code block extraction...")
        
        # Split by MODULE CHANGE if present
        modules = text.split("MODULE CHANGE") if "MODULE CHANGE" in text else [text]
        
        for module_index, module in enumerate(modules):
            module = module.strip()
            self.logger.info(f"Processing module {module_index + 1}/{len(modules)}")
            
            try:
                # Find all occurrences of code blocks
                while "```" in module:
                    start = module.find("```")
                    end = module.find("```", start + 3)
                    
                    if start == -1 or end == -1:
                        break
                        
                    # Extract the code block content
                    code_content = module[start+3:end].strip()
                    
                    # Remove the language identifier if present
                    if '\n' in code_content:
                        first_newline = code_content.index('\n')
                        if 'python' in code_content[:first_newline].lower():
                            code_content = code_content[first_newline:].strip()
                    
                    # Extract filename from first line comment
                    lines = code_content.split('\n')
                    if lines:
                        if lines[0].startswith('#'):
                            filename = lines[0][1:].strip()
                            code_content = '\n'.join(lines[1:]).strip()
                        else:
                            # If no filename comment, generate a default name
                            filename = f"module_{module_index + 1}"
                            
                        if not filename.endswith('.py'):
                            filename += '.py'
                            
                        self.logger.info(f"Extracted code block for file: {filename}")
                        code_blocks.append((filename, code_content))
                    
                    # Update module to continue searching for more code blocks
                    module = module[end + 3:]
                    
            except Exception as e:
                self.logger.error(f"Error processing module {module_index + 1}: {str(e)}")
                continue
        
        if not code_blocks:
            self.logger.warning("No code blocks found in the generated text")
        
        return code_blocks

    def save_code(self, code_content):
        """
        Save the code to files.
        """
        saved_files = []
        
        try:
            if isinstance(code_content, str):
                # Single file case
                filename = "generated_code.py"
                file_path = os.path.join(self.output_dir, filename)
                with open(file_path, "w") as file:
                    file.write(code_content)
                self.logger.info(f"Saved single file: {file_path}")
                saved_files.append(file_path)
            else:
                # Multiple files case (list of tuples)
                for filename, content in code_content:
                    file_path = os.path.join(self.output_dir, filename)
                    with open(file_path, "w") as file:
                        file.write(content)
                    self.logger.info(f"Saved file: {file_path}")
                    saved_files.append(file_path)
        
        except Exception as e:
            self.logger.error(f"Error saving files: {str(e)}")
            raise
        
        return saved_files

    def process_requirements(self, requirements):
        """
        Process the requirements, generate code, and save it.
        Returns a list of saved file paths.
        """
        try:
            # Generate code
            self.logger.info("Starting code generation process...")
            generated_code = self.generate_code(requirements)
            
            # Extract code blocks
            self.logger.info("Extracting code blocks...")
            code_blocks = self.extract_code_blocks(generated_code)
            
            # Save the code
            self.logger.info("Saving code to files...")
            if code_blocks:
                saved_files = self.save_code(code_blocks)
            else:
                saved_files = self.save_code(generated_code)
            
            self.logger.info("Code processing completed successfully")
            return saved_files
            
        except Exception as e:
            self.logger.error(f"Error in process_requirements: {str(e)}")
            raise

def test_coder_module():
    """
    Test function to verify the CoderModule functionality
    """
    try:
        coder = CoderModule(output_dir="test_output")
        requirements = """
        Create a Python-based Library Book Management System with the following modules and architectural layout. Ensure adherence to the specified requirements for seamless functionality and clarity throughout the development process.

### Project Structure

1. **Database Module (`database.py`):**
   - **Functionality:** Handle all SQLite database operations.
   - **Features:**
     - Establish a connection to the SQLite database.
     - Set up and create the required tables if they do not exist.
     - Implement functions for:
        - Create: Add new book records.
        - Read: Retrieve all records or perform searches based on title, author, or ISBN.
        - Update: Modify existing book details.
        - Delete: Remove books from the database using identifiers.
   - **Location:** `/libbookmgmt/db`

2. **Streamlit UI Module (`app.py`):**
   - **Functionality:** Provide a user-friendly interface for interacting with the database through Streamlit.
   - **Features:**
     - Sidebar navigation for different CRUD functionalities.
     - Form inputs for adding and updating book details.
     - Tables or lists for viewing and interacting with current book records.
   - **Location:** `/libbookmgmt/ui`

3. **Authentication Module (`auth.py`):**
   - **Functionality:** Simple user authentication to control access.
   - **Features:**
     - Basic authentication check using passwords.
     - Restrict access to certain functions based on user login status.
   - **Location:** `/libbookmgmt/security`

4. **Main Execution File (`main.py`):**
   - **Functionality:** Initialize the application and connect UI with database operations.
   - **Features:**
     - Start the Streamlit server.
     - Link each UI component with the corresponding database function.
   - **Location:** `/libbookmgmt`

### Instructions

- **SQLite Database Setup:** In `database.py`, initialize a connection to an SQLite database file named `library.db`. Use SQLite queries to set up the table `books` with fields `id` (Primary Key, Auto-Increment), `title`, `author`, and `isbn`.

- **Streamlit Application Design:** In `app.py`, create a modular layout using Streamlit's sidebar functionality for easy navigation between CRUD operations. Each section should include forms or data representations pertinent to the task (e.g., table for records).

- **Integrating Modules:** Utilize `main.py` to orchestrate the execution flow, ensuring that the database functions are effectively tied into the UI elements.

- **Optional Authentication:** If implementing authentication, define necessary login forms and session checks in `auth.py`, integrating security checks within the UI flow as needed.

- **Dependencies:** Ensure dependencies such as `streamlit` and `sqlite3` are included in a requirements file for easy setup.

By following this detailed structure, the application will be robust, adaptable to additional features, and ensures a smooth user experience.
        """
        
        saved_files = coder.process_requirements(requirements)
        print(f"Successfully saved files: {saved_files}")
        
    except Exception as e:
        print(f"Test failed: {str(e)}")

if __name__ == "__main__":
    test_coder_module()