import subprocess

def execute_program(program_code, filename="temp_program.py"):
    # Step 1: Write the program code to a file
    try:
        with open(filename, "w") as file:
            file.write(program_code)
        print(f"Program written to {filename}")
    except Exception as e:
        print(f"Error writing to file: {e}")
        return None, e

    # Step 2: Execute the file and capture the output
    try:
        result = subprocess.run(
            ["python", filename],
            capture_output=True,
            text=True,
            check=True
        )
        # Return the output if successful
        return result.stdout, None
    except subprocess.CalledProcessError as e:
        # Handle execution errors
        return None, e.stderr
    finally:
        # Optional: Clean up (remove the file after execution)
        try:
            import os
            os.remove(filename)
        except Exception as e:
            print(f"Error removing file: {e}")

# Example usage
program_code = """
print("Hello, World!")
x = 5 + 10
print(f'The result is {x}')
"""

output, error = execute_program(program_code)
if output:
    print("Program Output:")
    print(output)
if error:
    print("Program Error:")
    print(error)
